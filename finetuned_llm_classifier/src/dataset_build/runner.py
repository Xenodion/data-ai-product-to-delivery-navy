"""Write tickets for a list of cards: one call per card, append-only log, resumable, budget-guarded.

A ticket that fails a check is discarded and logged with its reasons; it is never retried (see the spec).
"""

import hashlib
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from src.dataset_build.cards import Card
from src.dataset_build.checks import check_ticket
from src.dataset_build.generation_prompt import (
    PromptConfig,
    format_ticket,
    render_prompt,
)
from src.dataset_build.openrouter import (
    ApiError,
    Budget,
    Completion,
    RoleConfig,
    RunConfig,
    estimate_call_cost,
    parse_ticket_json,
)

logger = logging.getLogger(__name__)

CompleteFn = Callable[[RoleConfig, str, str], Completion]


class TicketRecord(BaseModel):
    """One line of the call log."""

    card_id: str
    role: str
    model: str
    status: Literal["ok", "discarded"]
    reasons: list[str]
    subject: str
    body: str
    ticket: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    prompt_version: str


def prompt_version(prompt_config: PromptConfig) -> str:
    """Short hash of the prompt texts, to tell which prompt wrote which ticket."""
    return hashlib.sha256(prompt_config.model_dump_json().encode()).hexdigest()[:10]


def read_log(log_path: Path) -> list[TicketRecord]:
    if not log_path.exists():
        return []
    return [
        TicketRecord.model_validate_json(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]


def write_tickets(
    cards: list[Card],
    role_name: str,
    config: RunConfig,
    prompt_config: PromptConfig,
    log_path: Path,
    budget: Budget,
    complete: CompleteFn,
) -> list[TicketRecord]:
    """Write a ticket for every card not yet in the log; return the records of this call."""
    role = config.roles[role_name]
    version = prompt_version(prompt_config)
    done = {record.card_id for record in read_log(log_path) if record.role == role_name}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_records: list[TicketRecord] = []
    consecutive_errors = 0
    for card in cards:
        if card.card_id in done:
            continue
        system, user = render_prompt(card, prompt_config)
        budget.ensure(estimate_call_cost(role, system, user))
        try:
            completion = complete(role, system, user)
            consecutive_errors = 0
        except ApiError as error:
            consecutive_errors += 1
            logger.error(
                "API error on %s (%d in a row): %s",
                card.card_id,
                consecutive_errors,
                error,
            )
            if consecutive_errors >= config.max_consecutive_errors:
                raise
            continue
        budget.add(completion.cost_usd)
        record = _to_record(card, role_name, role, completion, version, prompt_config)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(record.model_dump_json() + "\n")
        new_records.append(record)
    logger.info(
        "wrote %d tickets, spent %.4f USD in total", len(new_records), budget.spent_usd
    )
    return new_records


def _to_record(
    card: Card,
    role_name: str,
    role: RoleConfig,
    completion: Completion,
    version: str,
    prompt_config: PromptConfig,
) -> TicketRecord:
    base = {
        "card_id": card.card_id,
        "role": role_name,
        "model": role.model,
        "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens,
        "cost_usd": completion.cost_usd,
        "prompt_version": version,
    }
    try:
        subject, body = parse_ticket_json(completion.content)
    except (json.JSONDecodeError, TypeError):
        return TicketRecord(
            **base,
            status="discarded",
            reasons=["unparseable_json"],
            subject="",
            body=completion.content,
            ticket="",
        )
    reasons = check_ticket(card, subject, body)
    return TicketRecord(
        **base,
        status="discarded" if reasons else "ok",
        reasons=reasons,
        subject=subject,
        body=body,
        ticket=format_ticket(subject, body),
    )
