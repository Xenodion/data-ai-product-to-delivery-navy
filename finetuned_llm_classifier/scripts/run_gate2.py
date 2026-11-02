"""Gate 2: 100 real train cards through the whole chain (write, deterministic checks, voters, judge).

python scripts/run_gate2.py --dry-run     # estimate the cost, call nothing
python scripts/run_gate2.py --limit 10    # small paid canary
python scripts/run_gate2.py               # the 100 cards (resumable)

Writes data/gate2/gate2_stats.md (rates, costs) and data/gate2/gate2_review.md (30 rows for a human read:
10 flagged, 20 that passed everything, to measure what the chain misses).
"""

import argparse
import logging
import os
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from dotenv import load_dotenv

from src.dataset_build.cards import Card, load_config
from src.dataset_build.generation_prompt import load_prompt_config, render_prompt
from src.dataset_build.openrouter import (
    Budget,
    Completion,
    RoleConfig,
    complete,
    estimate_call_cost,
    load_run_config,
)
from src.dataset_build.review import (
    ReviewRecord,
    load_definitions,
    read_reviews,
    review_tickets,
    voter_prompts,
)
from src.dataset_build.runner import TicketRecord, read_log, write_tickets
from src.dataset_build.splits import SplitSizes, draw_pool, split_pool

GATE_SIZE = 100
POOL_SEED = 20261031
READ_FLAGGED, READ_PASSED, READ_SEED = 10, 20, 7
WRITER_ROLE = "writer_train"
RUN_DIR = PROJECT_ROOT / "data" / "runs"
TICKETS_LOG = RUN_DIR / "gate2_tickets.jsonl"
REVIEWS_LOG = RUN_DIR / "gate2_reviews.jsonl"
OUT_DIR = PROJECT_ROOT / "data" / "gate2"

logger = logging.getLogger("run_gate2")


def gate_cards() -> list[Card]:
    config = load_config()
    sizes = SplitSizes(**config.splits)
    return split_pool(draw_pool(config, sizes, POOL_SEED), sizes, POOL_SEED)["train"][
        :GATE_SIZE
    ]


def build_stats(
    cards: list[Card], tickets: list[TicketRecord], reviews: list[ReviewRecord]
) -> str:
    by_card = {card.card_id: card for card in cards}
    reviewed = {review.card_id: review for review in reviews}
    discarded = [t for t in tickets if t.status == "discarded"]
    accepted = [r for r in reviews if r.final == "accepted"]
    rejected = [r for r in reviews if r.final == "rejected"]
    judged = [r for r in reviews if r.judge_verdict]
    cost = sum(t.cost_usd for t in tickets) + sum(r.cost_usd for r in reviews)
    lines = [
        "# Gate 2 statistics",
        f"- cards written: {len(tickets)} | failed deterministic checks: {len(discarded)} | reviewed: {len(reviews)}",
        f"- judge called on {len(judged)} tickets | rejected by judge: {len(rejected)} | accepted: {len(accepted)}",
        f"- final pass rate: {len(accepted) / max(len(tickets), 1):.0%} of written tickets",
        f"- cost: {cost:.4f} USD ({cost / max(len(tickets), 1):.5f} per ticket; spec estimate for the full run: 5.8 USD / 3190 = 0.0018)",
        f"- deterministic reasons: {dict(Counter(x for t in discarded for x in t.reasons))}",
    ]
    for role in ("voter_a", "voter_b"):
        votes = [v for r in reviews for v in r.votes if v.role == role]
        diff = Counter(
            f for v in votes if v.label is not None for f in v.differing_fields
        )
        unusable = sum(v.label is None for v in votes)
        lines.append(
            f"- {role}: {len(votes)} votes, {unusable} unusable, disagreeing fields {dict(diff)}"
        )
    traps: Counter[str] = Counter()
    failed: Counter[str] = Counter()
    for ticket in tickets:
        card = by_card[ticket.card_id]
        review = reviewed.get(ticket.card_id)
        ok = ticket.status == "ok" and review is not None and review.final == "accepted"
        for trap in card.traps or ("(no trap)",):
            traps[trap] += 1
            failed[trap] += not ok
    lines.append("\n| trap | written | not accepted |\n|---|---|---|")
    lines += [
        f"| {trap} | {count} | {failed[trap]} |"
        for trap, count in sorted(traps.items(), key=lambda kv: -kv[1])
    ]
    return "\n".join(lines)


def export_reading(
    cards: list[Card], tickets: list[TicketRecord], reviews: list[ReviewRecord]
) -> None:
    """30 rows to read: 10 flagged by the chain, 20 that passed everything."""
    by_card = {card.card_id: card for card in cards}
    reviewed = {review.card_id: review for review in reviews}
    flagged = [
        t
        for t in tickets
        if t.status == "discarded"
        or (t.card_id in reviewed and reviewed[t.card_id].final == "rejected")
    ]
    passed = [
        t
        for t in tickets
        if t.card_id in reviewed and reviewed[t.card_id].final == "accepted"
    ]
    rng = random.Random(READ_SEED)
    picked = [
        ("FLAGGED", t) for t in rng.sample(flagged, min(READ_FLAGGED, len(flagged)))
    ]
    picked += [("PASSED", t) for t in rng.sample(passed, min(READ_PASSED, len(passed)))]
    lines = [
        "# Gate 2 reading",
        "",
        "Mark each ticket: defect or not (does the ticket carry exactly its label?). The PASSED ones measure what the chain misses.",
        "",
    ]
    for kind, ticket in picked:
        card = by_card[ticket.card_id]
        review = reviewed.get(ticket.card_id)
        note = (
            ", ".join(ticket.reasons)
            if ticket.status == "discarded"
            else (
                f"judge: {review.judge_verdict} - {review.judge_reason}"
                if review and review.judge_verdict
                else ""
            )
        )
        votes = (
            "; ".join(
                f"{v.role}: {v.differing_fields or 'agrees'}" for v in review.votes
            )
            if review
            else ""
        )
        lines += [
            f"## [{kind}] {ticket.card_id} {note}",
            f"- label: `{card.label.model_dump_json()}`",
            f"- traps: {', '.join(card.traps) or 'none'} | {card.language} | {card.channel} | {card.length} | voters: {votes}",
            "",
            "```text",
            ticket.ticket or ticket.body,
            "```",
            "",
        ]
    (OUT_DIR / "gate2_review.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=GATE_SIZE)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cards = gate_cards()[: args.limit]
    run_config, prompt_config = load_run_config(), load_prompt_config()
    definitions = load_definitions()

    if args.dry_run:
        writer = run_config.roles[WRITER_ROLE]
        estimate = sum(
            estimate_call_cost(writer, *render_prompt(card, prompt_config))
            for card in cards
        )
        sample = voter_prompts(definitions, "x" * 900)
        for name in ("voter_a", "voter_b"):
            estimate += len(cards) * estimate_call_cost(run_config.roles[name], *sample)
        estimate += (
            0.2
            * len(cards)
            * estimate_call_cost(run_config.roles["judge"], definitions, "x" * 1800)
        )
        logger.info(
            "dry run: %d cards, upper-bound estimate %.4f USD (writer + 2 voters + judge on 20 pct), nothing sent",
            len(cards),
            estimate,
        )
        return

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key.startswith("your-"):
        raise SystemExit("OPENROUTER_API_KEY is missing from the sub-project .env")
    budget = (
        Budget.from_logs(run_config.budget_usd, RUN_DIR)
        if RUN_DIR.exists()
        else Budget(run_config.budget_usd)
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as client:

        def call(role: RoleConfig, system: str, user: str) -> Completion:
            return complete(client, run_config, role, api_key, system, user)

        write_tickets(
            cards, WRITER_ROLE, run_config, prompt_config, TICKETS_LOG, budget, call
        )
        tickets = [t for t in read_log(TICKETS_LOG) if t.role == WRITER_ROLE]
        by_card = {card.card_id: card for card in cards}
        to_review = [
            (by_card[t.card_id], t)
            for t in tickets
            if t.status == "ok" and t.card_id in by_card
        ]
        review_tickets(
            to_review, 1.0, run_config, REVIEWS_LOG, budget, call, definitions
        )  # voter B on all rows at gate 2

    tickets = [
        t for t in read_log(TICKETS_LOG) if t.card_id in {c.card_id for c in cards}
    ]
    reviews = [
        r for r in read_reviews(REVIEWS_LOG) if r.card_id in {c.card_id for c in cards}
    ]
    stats = build_stats(cards, tickets, reviews)
    (OUT_DIR / "gate2_stats.md").write_text(stats, encoding="utf-8")
    export_reading(cards, tickets, reviews)
    logger.info("\n%s", stats)


if __name__ == "__main__":
    main()
