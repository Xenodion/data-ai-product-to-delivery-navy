"""Check written tickets: two blind voters re-label each ticket, a judge settles disagreements only.

The voters see the ticket and the label rules, never the card label. Their answer is compared to the card
label field by field (free). A ticket is rejected when the judge says it does not support its label, and it
is never retried (see the spec).
"""

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from src.dataset_build.cards import Card
from src.dataset_build.openrouter import (
    ApiError,
    Budget,
    Completion,
    RoleConfig,
    RunConfig,
    estimate_call_cost,
    parse_json_object,
)
from src.dataset_build.runner import TicketRecord
from src.dataset_build.schema import TicketLabel
from src.prompt import INSTRUCTION

logger = logging.getLogger(__name__)

DEFINITIONS_PATH = Path(__file__).resolve().parents[2] / "docs" / "label_definitions.md"
LABEL_FIELDS = (
    "intent",
    "sub_intent",
    "transaction_id",
    "amount",
    "currency",
    "urgency",
    "sentiment",
)
CompleteFn = Callable[[RoleConfig, str, str], Completion]

VOTER_SYSTEM = (
    "You are a careful annotator of support tickets. Apply these labelling rules exactly.\n\n{definitions}\n\n"
    "Output format: {instruction}"
)
JUDGE_SYSTEM = (
    "You are an expert annotator of support tickets. Apply these labelling rules exactly.\n\n{definitions}\n\n"
    "Read the ticket and label it. Answer with one JSON object with the keys in this order: "
    '{{"reasoning": "<brief reasoning on the fields that are not obvious, under 40 words>", "label": {{...}}}} '
    "where label has the seven keys. Format of the label: {instruction}"
)


class Vote(BaseModel):
    role: str
    label: (
        dict[str, str] | None
    )  # None when the answer was unusable (the voter abstains)
    raw: str
    differing_fields: list[str]
    cost_usd: float


class ReviewRecord(BaseModel):
    """One line of the review log."""

    card_id: str
    votes: list[Vote]
    judge_verdict: Literal["", "accept", "reject"]
    judge_reason: str
    final: Literal["accepted", "rejected"]
    cost_usd: float


def load_definitions(path: Path = DEFINITIONS_PATH) -> str:
    return path.read_text(encoding="utf-8")


def voter_prompts(definitions: str, ticket: str) -> tuple[str, str]:
    return VOTER_SYSTEM.format(
        definitions=definitions, instruction=INSTRUCTION
    ), f"Ticket:\n{ticket}"


def judge_prompts(definitions: str, ticket: str) -> tuple[str, str]:
    return JUDGE_SYSTEM.format(
        definitions=definitions, instruction=INSTRUCTION
    ), f"Ticket:\n{ticket}"


def differing_fields(expected: TicketLabel, got: TicketLabel) -> list[str]:
    return [
        name for name in LABEL_FIELDS if getattr(expected, name) != getattr(got, name)
    ]


def uses_voter_b(card_id: str, fraction: float) -> bool:
    """Deterministic sample: the same card always gets the same decision."""
    return (
        int(hashlib.sha256(card_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        < fraction
    )


def read_reviews(log_path: Path) -> list[ReviewRecord]:
    if not log_path.exists():
        return []
    return [
        ReviewRecord.model_validate_json(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]


def review_tickets(
    items: list[tuple[Card, TicketRecord]],
    voter_b_fraction: float,
    config: RunConfig,
    log_path: Path,
    budget: Budget,
    complete: CompleteFn,
    definitions: str,
) -> list[ReviewRecord]:
    """Review every (card, written ticket) not yet in the log; return the new records."""
    done = {record.card_id for record in read_reviews(log_path)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_records: list[ReviewRecord] = []
    errors_in_a_row = 0
    for card, ticket in items:
        if card.card_id in done:
            continue
        roles = ["voter_a"] + (
            ["voter_b"] if uses_voter_b(card.card_id, voter_b_fraction) else []
        )
        votes: list[Vote] = []
        for role_name in roles:
            vote, errors_in_a_row = _vote(
                role_name,
                card,
                ticket,
                config,
                budget,
                complete,
                definitions,
                errors_in_a_row,
            )
            votes.append(vote)
        record = _decide(card, ticket, votes, config, budget, complete, definitions)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(record.model_dump_json() + "\n")
        new_records.append(record)
    logger.info(
        "reviewed %d tickets, spent %.4f USD in total",
        len(new_records),
        budget.spent_usd,
    )
    return new_records


def _vote(
    role_name: str,
    card: Card,
    ticket: TicketRecord,
    config: RunConfig,
    budget: Budget,
    complete: CompleteFn,
    definitions: str,
    errors_in_a_row: int,
) -> tuple[Vote, int]:
    role = config.roles[role_name]
    system, user = voter_prompts(definitions, ticket.ticket)
    budget.ensure(estimate_call_cost(role, system, user))
    try:
        completion = complete(role, system, user)
    except ApiError as error:
        errors_in_a_row += 1
        logger.error(
            "API error (%s, %d in a row): %s", role_name, errors_in_a_row, error
        )
        if errors_in_a_row >= config.max_consecutive_errors:
            raise
        return Vote(
            role=role_name,
            label=None,
            raw=f"api_error: {error}",
            differing_fields=[],
            cost_usd=0.0,
        ), errors_in_a_row
    budget.add(completion.cost_usd)
    try:
        got = TicketLabel.model_validate(parse_json_object(completion.content))
        label, diff = got.model_dump(), differing_fields(card.label, got)
    except (ValueError, TypeError, ValidationError):
        label, diff = None, []
    return Vote(
        role=role_name,
        label=label,
        raw=completion.content,
        differing_fields=diff,
        cost_usd=completion.cost_usd,
    ), 0


def _decide(
    card: Card,
    ticket: TicketRecord,
    votes: list[Vote],
    config: RunConfig,
    budget: Budget,
    complete: CompleteFn,
    definitions: str,
) -> ReviewRecord:
    valid = [vote for vote in votes if vote.label is not None]
    cost = sum(vote.cost_usd for vote in votes)
    if valid and all(not vote.differing_fields for vote in valid):
        return ReviewRecord(
            card_id=card.card_id,
            votes=votes,
            judge_verdict="",
            judge_reason="",
            final="accepted",
            cost_usd=cost,
        )
    verdict, reason, judge_cost = _judge(
        card, ticket, config, budget, complete, definitions
    )
    return ReviewRecord(
        card_id=card.card_id,
        votes=votes,
        judge_verdict=verdict,
        judge_reason=reason,
        final="accepted" if verdict == "accept" else "rejected",
        cost_usd=cost + judge_cost,
    )


def _judge(
    card: Card,
    ticket: TicketRecord,
    config: RunConfig,
    budget: Budget,
    complete: CompleteFn,
    definitions: str,
) -> tuple[Literal["accept", "reject"], str, float]:
    """A third, stronger reading of the ticket; the code compares it to the card label (no free-form verdict)."""
    role = config.roles["judge"]
    system, user = judge_prompts(definitions, ticket.ticket)
    cost = 0.0
    for attempt_role in (
        role,
        role.model_copy(update={"max_tokens": role.max_tokens * 3}),
    ):
        budget.ensure(estimate_call_cost(attempt_role, system, user))
        try:
            completion = complete(attempt_role, system, user)
            budget.add(completion.cost_usd)
            cost += completion.cost_usd
            answer = parse_json_object(completion.content)
            got = TicketLabel.model_validate(answer["label"])
            reasoning = str(answer.get("reasoning", ""))
        except (ApiError, ValueError, TypeError, KeyError):
            continue
        differing = differing_fields(card.label, got)
        if not differing:
            return "accept", reasoning, cost
        return "reject", f"judge reads {differing} differently: {reasoning}", cost
    return "reject", "judge unusable: rejected by default", cost


def rejudge_rejected(
    items: list[tuple[Card, TicketRecord]],
    config: RunConfig,
    log_path: Path,
    budget: Budget,
    complete: CompleteFn,
    definitions: str,
) -> list[ReviewRecord]:
    """Ask the judge again for the tickets it rejected; a new line supersedes the old one (the log is append-only)."""
    latest = {record.card_id: record for record in read_reviews(log_path)}
    superseded: list[ReviewRecord] = []
    for card, ticket in items:
        old = latest.get(card.card_id)
        if old is None or old.final != "rejected" or old.judge_verdict != "reject":
            continue
        verdict, reason, cost = _judge(
            card, ticket, config, budget, complete, definitions
        )
        record = ReviewRecord(
            card_id=card.card_id,
            votes=old.votes,
            judge_verdict=verdict,
            judge_reason=reason,
            final="accepted" if verdict == "accept" else "rejected",
            cost_usd=cost,
        )
        with log_path.open("a", encoding="utf-8") as log:
            log.write(record.model_dump_json() + "\n")
        superseded.append(record)
    return superseded
