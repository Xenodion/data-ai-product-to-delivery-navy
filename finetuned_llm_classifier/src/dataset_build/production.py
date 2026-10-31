"""Produce one split in growing batches: write, check, review, replace failures from the reserve, stop on alarms.

A ticket that fails a check or the judge is never retried or deleted: it stays in the logs and is exported to the
quarantine. The split is topped up with cards of its own reserve until its target is met (or its floor, see run.toml).
"""

import logging
import math
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from src.dataset_build.cards import Card
from src.dataset_build.generation_prompt import PromptConfig
from src.dataset_build.openrouter import Budget, Completion, RoleConfig, RunConfig
from src.dataset_build.review import ReviewRecord, read_reviews, review_tickets
from src.dataset_build.runner import TicketRecord, read_log, write_tickets

logger = logging.getLogger(__name__)

CompleteFn = Callable[[RoleConfig, str, str], Completion]
MIN_BATCH = 5
RATE_AFTER_ATTEMPTS = 20  # before this, assume every ticket passes
MIN_ACCEPTANCE = 0.3


class ProductionStoppedError(RuntimeError):
    """A stop rule tripped: diagnose before continuing (see the spec)."""


class SplitStatus(BaseModel):
    split: str
    target: int
    accepted: int
    attempted: int
    complete: bool
    reason: str
    cost_usd: float


def split_reserves(
    pool: list[Card], splits: dict[str, list[Card]], config: RunConfig
) -> dict[str, list[Card]]:
    """Cards of the pool used by no split, dealt to the splits by position so that no card serves two splits."""
    used = {card.card_id for cards in splits.values() for card in cards}
    leftovers = [card for card in pool if card.card_id not in used]
    buckets = config.production.reserve_buckets
    return {
        name: [c for i, c in enumerate(leftovers) if i % 10 in slots]
        for name, slots in buckets.items()
    }


def log_paths(run_dir: Path, split: str) -> tuple[Path, Path]:
    return (
        run_dir / f"prod_{split}_tickets.jsonl",
        run_dir / f"prod_{split}_reviews.jsonl",
    )


def accepted_ids(tickets: list[TicketRecord], reviews: list[ReviewRecord]) -> set[str]:
    verdict = {review.card_id: review.final for review in reviews}
    return {
        t.card_id
        for t in tickets
        if t.status == "ok" and verdict.get(t.card_id) == "accepted"
    }


def next_candidates(
    own: list[Card],
    reserve: list[Card],
    attempted: set[str],
    accepted: list[Card],
    min_per_trap: int,
    count: int,
) -> list[Card]:
    """Own cards first; once exhausted, reserve cards (for traps: only those that carry an under-filled trap)."""
    picked = [card for card in own if card.card_id not in attempted][:count]
    if len(picked) >= count:
        return picked
    taken = Counter(trap for card in accepted for trap in card.traps)
    short = {
        f"trap:{trap}"
        for card in own
        for trap in card.traps
        if taken[trap] < min_per_trap
    }
    chosen = {card.card_id for card in picked}
    for card in reserve:
        if len(picked) >= count:
            break
        if card.card_id in attempted or card.card_id in chosen:
            continue
        if min_per_trap == 0 or card.tags & short:
            picked.append(card)
    return picked


def run_split(
    split: str,
    own: list[Card],
    reserve: list[Card],
    min_per_trap: int,
    config: RunConfig,
    prompt_config: PromptConfig,
    definitions: str,
    budget: Budget,
    complete: CompleteFn,
    run_dir: Path,
    max_batches: int | None = None,
    ignore_stop_rules: bool = False,
) -> SplitStatus:
    """Produce ``split`` batch by batch; raise ProductionStoppedError when a stop rule trips."""
    settings = config.production
    tickets_log, reviews_log = log_paths(run_dir, split)
    target, by_id = len(own), {card.card_id: card for card in [*own, *reserve]}
    batch_no = 0
    while True:
        tickets, reviews = read_log(tickets_log), read_reviews(reviews_log)
        done = accepted_ids(tickets, reviews)
        attempted = {t.card_id for t in tickets}
        accepted_cards = [by_id[i] for i in done]
        cost = sum(t.cost_usd for t in tickets) + sum(r.cost_usd for r in reviews)
        complete_now = len(done) >= target
        exhausted = len(attempted) >= math.ceil(settings.attempts_factor * target)
        if (
            complete_now
            or exhausted
            or (max_batches is not None and batch_no >= max_batches)
        ):
            return _status(
                split,
                target,
                done,
                attempted,
                cost,
                settings.accepted_floor,
                complete_now,
                max_batches,
                batch_no,
            )
        size = settings.batch_sizes[min(batch_no, len(settings.batch_sizes) - 1)]
        rate = (
            len(done) / len(attempted) if len(attempted) >= RATE_AFTER_ATTEMPTS else 1.0
        )
        needed = math.ceil((target - len(done)) / max(rate, MIN_ACCEPTANCE))
        size = max(MIN_BATCH, min(size, needed))
        batch = next_candidates(
            own, reserve, attempted, accepted_cards, min_per_trap, size
        )
        if not batch:
            return _status(
                split,
                target,
                done,
                attempted,
                cost,
                settings.accepted_floor,
                False,
                max_batches,
                batch_no,
            )
        write_tickets(
            batch,
            settings.writer_role[split],
            config,
            prompt_config,
            tickets_log,
            budget,
            complete,
        )
        written = [
            t for t in read_log(tickets_log) if t.card_id in {c.card_id for c in batch}
        ]
        review_tickets(
            [(by_id[t.card_id], t) for t in written if t.status == "ok"],
            settings.voter_b_fraction[split],
            config,
            reviews_log,
            budget,
            complete,
            definitions,
        )
        batch_no += 1
        logger.info(
            "%s batch %d: %d candidates, spent %.4f USD in total",
            split,
            batch_no,
            len(batch),
            budget.spent_usd,
        )
        if not ignore_stop_rules:
            _check_stop_rules(split, batch, tickets_log, reviews_log, by_id, config)


def _status(
    split: str,
    target: int,
    done: set[str],
    attempted: set[str],
    cost: float,
    floor: float,
    complete_now: bool,
    max_batches: int | None,
    batch_no: int,
) -> SplitStatus:
    ok = complete_now or len(done) >= floor * target
    if complete_now:
        reason = "target reached"
    elif ok:
        reason = f"floor reached ({floor:.0%} of the target), attempts exhausted"
    elif max_batches is not None and batch_no >= max_batches:
        reason = "stopped after the requested number of batches"
    else:
        reason = "incomplete: attempts or reserve exhausted below the floor"
    return SplitStatus(
        split=split,
        target=target,
        accepted=len(done),
        attempted=len(attempted),
        complete=ok,
        reason=reason,
        cost_usd=cost,
    )


def _check_stop_rules(
    split: str,
    batch: list[Card],
    tickets_log: Path,
    reviews_log: Path,
    by_id: dict[str, Card],
    config: RunConfig,
) -> None:
    settings = config.production
    tickets, reviews = read_log(tickets_log), read_reviews(reviews_log)
    good = accepted_ids(tickets, reviews)
    in_batch = {card.card_id for card in batch}
    batch_tickets = [t for t in tickets if t.card_id in in_batch]
    if len(batch_tickets) >= settings.min_batch_for_rates:
        rate = 1 - sum(t.card_id in good for t in batch_tickets) / len(batch_tickets)
        if round(rate, 6) > settings.max_nonconformity:
            raise ProductionStoppedError(
                f"{split}: {rate:.0%} of the last batch is non-conforming (limit {settings.max_nonconformity:.0%})"
            )
    attempts: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    for ticket in tickets:
        for trap in by_id[ticket.card_id].traps:
            attempts[trap] += 1
            failures[trap] += ticket.card_id not in good
    for trap, n in attempts.items():
        if (
            n >= settings.trap_min_attempts
            and failures[trap] / n > settings.trap_max_failure
        ):
            raise ProductionStoppedError(
                f"{split}: trap {trap} fails {failures[trap]}/{n} (limit {settings.trap_max_failure:.0%})"
            )
    cost = sum(t.cost_usd for t in tickets) + sum(r.cost_usd for r in reviews)
    ceiling = settings.cost_factor * settings.cost_per_ticket_estimate * len(tickets)
    if cost > ceiling:
        raise ProductionStoppedError(
            f"{split}: spent {cost:.4f} USD for {len(tickets)} tickets, above {ceiling:.4f} (estimate x {settings.cost_factor})"
        )
