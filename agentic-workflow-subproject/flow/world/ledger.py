"""The transaction ledger: rows cited by the sampled tickets, plus filler rows per merchant."""

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from random import Random

from pydantic import BaseModel, ConfigDict

from flow.world.config import WorldConfig
from flow.world.deck import DeckTicket
from flow.world.merchants import MerchantBook
from flow.world.models import Dispute, Merchant, Payout, Refund, Ticket, Transaction
from flow.world.money import build_disputes, build_payouts, build_refunds, to_minor
from flow.world.rng import stage_rng
from flow.world.sampling import SelectedTicket
from flow.world.text_signals import extract_references

ID_LOW, ID_HIGH = 100_000, 999_999
FIRST_HOUR, LAST_HOUR = 7, 19
SETTLED_LIKE = ("settled", "refunded", "disputed")
SETTLE_DELAY = timedelta(days=1)
MIN_CITED_GAP = timedelta(days=2)
PENDING_STATUSES = ("processing", "under_review")


class LedgerBuild(BaseModel):
    """Ledger rows and the bookkeeping the money objects and the report need."""

    model_config = ConfigDict(frozen=True)

    transactions: tuple[Transaction, ...]
    cited: dict[str, tuple[str, ...]]  # ticket id -> its transaction ids that got a row
    shared_references: tuple[str, ...]  # references already owned by an earlier ticket


def _moment(rng: Random, day: datetime) -> datetime:
    return day.replace(
        hour=rng.randint(FIRST_HOUR, LAST_HOUR),
        minute=rng.randint(0, 59),
        second=rng.randint(0, 59),
    )


def _usual_amount(rng: Random, merchant: Merchant, config: WorldConfig) -> int:
    low, high = config.ledger.amount_range_minor[merchant.volume_tier]
    return max(1, round(math.exp(rng.uniform(math.log(low), math.log(high)))))


def _stated_minor(ticket: DeckTicket) -> int | None:
    try:
        minor = to_minor(Decimal(ticket.label.amount)) if ticket.label.amount else 0
    except InvalidOperation:
        return None
    return minor if minor > 0 else None


def _row(
    transaction_id: str,
    merchant_id: str,
    amount: int,
    currency: str,
    status: str,
    method: str,
    created: datetime,
) -> Transaction:
    settled = created + SETTLE_DELAY if status in SETTLED_LIKE else None
    return Transaction(
        transaction_id=transaction_id,
        merchant_id=merchant_id,
        amount_minor=amount,
        currency=currency,
        status=status,
        payment_method=method,
        created_at=created,
        settled_at=settled,
    )


def _free_id(rng: Random, reserved: set[str]) -> str:
    while True:
        candidate = f"TX-{rng.randint(ID_LOW, ID_HIGH)}"
        if candidate not in reserved:
            reserved.add(candidate)
            return candidate


def build_ledger(
    tickets: Sequence[Ticket],
    deck_all: Mapping[str, DeckTicket],
    selected: Mapping[str, SelectedTicket],
    book: MerchantBook,
    config: WorldConfig,
) -> LedgerBuild:
    """Build every ledger row.

    Each well-formed reference of a sampled ticket gets one row under the ticket's merchant, with
    the annotated amount and currency; a malformed or foreign reference finds no row. The first
    ticket (by id) that cites a reference owns it. Generated identifiers avoid every reference
    found anywhere in the deck, so a filler row never answers a ticket's reference.
    """
    ledger = config.ledger
    merchants = {m.merchant_id: m for m in book.merchants}
    reserved = {
        reference
        for card in deck_all.values()
        for reference in (*extract_references(card.text), card.label.transaction_id)
        if reference
    }
    rng = stage_rng(config.seed, "ledger")
    methods, method_weights = list(ledger.payment_methods), list(ledger.payment_methods.values())
    rows: list[Transaction] = []
    cited: dict[str, tuple[str, ...]] = {}
    shared: list[str] = []
    owned: set[str] = set()
    for ticket in sorted(tickets, key=lambda item: item.ticket_id):
        card = deck_all[ticket.ticket_id]
        merchant = merchants[ticket.merchant_id]
        references = [
            r
            for r in dict.fromkeys((card.label.transaction_id, *extract_references(card.text)))
            if r
        ]
        mine = [r for r in references if r not in owned]
        shared += [r for r in references if r in owned]
        owned.update(mine)
        cited[ticket.ticket_id] = tuple(mine)
        opened_day = ticket.opened_at.replace(hour=0, minute=0, second=0)
        status = ledger.status_by_sub_intent.get(card.label.sub_intent, ledger.default_status)
        for position, reference in enumerate(mine):
            day = opened_day - timedelta(days=rng.randint(*ledger.cited_age_days))
            text_date = selected[ticket.ticket_id].earliest_full_date
            if text_date is not None:
                day = datetime.combine(text_date, time(0), tzinfo=UTC)
            day = min(day, opened_day - MIN_CITED_GAP)
            stated = _stated_minor(card) if position == 0 else None
            amount = stated or _usual_amount(rng, merchant, config)
            if stated and card.label.sub_intent == "amount_mismatch":
                sign = rng.choice((-1, 1))
                amount = max(1, round(stated * (1 + sign * ledger.amount_mismatch_pct)))
                amount = amount if amount != stated else stated + 1
            currency = (
                card.label.currency
                if stated and card.label.currency in config.fx_to_eur
                else merchant.settlement_currency
            )
            created = _moment(rng, day)
            method = rng.choices(methods, method_weights)[0]
            rows.append(
                _row(reference, merchant.merchant_id, amount, currency, status, method, created)
            )
            if position == 0 and card.label.sub_intent == "duplicate_charge":
                rows.append(
                    _row(
                        _free_id(rng, reserved),
                        merchant.merchant_id,
                        amount,
                        currency,
                        status,
                        method,
                        created + timedelta(minutes=ledger.duplicate_gap_minutes),
                    )
                )
    rows += _filler(book.merchants, reserved, config)
    return LedgerBuild(
        transactions=tuple(sorted(rows, key=lambda item: item.transaction_id)),
        cited=cited,
        shared_references=tuple(sorted(set(shared))),
    )


def _filler(
    merchants: Sequence[Merchant], reserved: set[str], config: WorldConfig
) -> list[Transaction]:
    ledger = config.ledger
    rng = stage_rng(config.seed, "ledger-filler")
    methods, method_weights = list(ledger.payment_methods), list(ledger.payment_methods.values())
    statuses, status_weights = (
        list(ledger.filler_status_weights),
        list(ledger.filler_status_weights.values()),
    )
    start = datetime.combine(config.window_start, time(0), tzinfo=UTC)
    span_days = (config.window_end - config.window_start).days
    end = datetime.combine(config.window_end, time(0), tzinfo=UTC)
    rows = []
    for merchant in sorted(merchants, key=lambda item: item.merchant_id):
        for _ in range(config.transactions_per_merchant):
            created = _moment(rng, start + timedelta(days=rng.randint(0, span_days)))
            status = rng.choices(statuses, status_weights)[0]
            if status in PENDING_STATUSES and end - created > timedelta(
                days=ledger.pending_max_days
            ):
                status = "settled"
            rows.append(
                _row(
                    _free_id(rng, reserved),
                    merchant.merchant_id,
                    _usual_amount(rng, merchant, config),
                    merchant.settlement_currency,
                    status,
                    rng.choices(methods, method_weights)[0],
                    created,
                )
            )
    return rows


def build_money_objects(
    build: LedgerBuild,
    tickets: Sequence[Ticket],
    deck_all: Mapping[str, DeckTicket],
    book: MerchantBook,
    config: WorldConfig,
) -> tuple[tuple[Refund, ...], tuple[Dispute, ...], tuple[Payout, ...]]:
    """Refunds, disputes and payouts derived from the ledger and from what the tickets ask."""

    def cited_by(sub_intent: str) -> set[str]:
        return {
            reference
            for ticket in tickets
            if deck_all[ticket.ticket_id].label.sub_intent == sub_intent
            for reference in build.cited[ticket.ticket_id]
        }

    every_cited = {reference for references in build.cited.values() for reference in references}
    return (
        build_refunds(build.transactions, cited_by("refund_status"), config),
        build_disputes(build.transactions, every_cited, cited_by("chargeback"), config),
        build_payouts(build.transactions, book.merchants, config),
    )


def ledger_report(
    tickets: Sequence[Ticket],
    deck_all: Mapping[str, DeckTicket],
    build: LedgerBuild,
    count: int = 20,
) -> str:
    """Cited ledger rows beside the annotation of their ticket, for the human check of gate G4."""
    rows = {row.transaction_id: row for row in build.transactions}
    lines = [
        "| ticket | role | sub-intent | annotated TX | annotated amount | ledger amount | status |",
        "|---|---|---|---|---|---|---|",
    ]
    shown = 0
    for ticket in sorted(tickets, key=lambda item: item.ticket_id):
        label = deck_all[ticket.ticket_id].label
        if not build.cited[ticket.ticket_id] or not label.amount or shown >= count:
            continue
        row = rows[build.cited[ticket.ticket_id][0]]
        lines.append(
            f"| {ticket.ticket_id} | {ticket.role} | {label.sub_intent} | {row.transaction_id} | "
            f"{label.amount} {label.currency} | {row.amount_minor / 100:.2f} {row.currency} | "
            f"{row.status} |"
        )
        shown += 1
    return "\n".join(lines)


def main() -> None:
    """Build the ledger and write ``ledger_check.md`` with 20 rows beside their annotation."""
    import argparse
    import logging
    from pathlib import Path

    from flow.world.config import DEFAULT_CONFIG_PATH, load_world_config
    from flow.world.deck import load_deck
    from flow.world.sampling import sample_roles
    from flow.world.timeline import build_people

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    config = load_world_config(parser.parse_args().config)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    deck_tickets = load_deck(config.resolve(config.paths.deck_dir), config.text_newline)
    manifest = sample_roles(deck_tickets, config)
    book, tickets, deck = build_people(deck_tickets, manifest, config)
    selected = {item.card_id: item for item in manifest.tickets}
    build = build_ledger(tickets, deck, selected, book, config)
    refunds, disputes, payouts = build_money_objects(build, tickets, deck, book, config)
    target = config.resolve(config.paths.artifacts_dir) / "reports" / "ledger_check.md"
    target.write_text(ledger_report(tickets, deck, build) + "\n", encoding="utf-8", newline="\n")
    logging.getLogger(__name__).info(
        "%d transactions, %d refunds, %d disputes, %d payouts, %d shared references; %s",
        len(build.transactions),
        len(refunds),
        len(disputes),
        len(payouts),
        len(build.shared_references),
        target,
    )


if __name__ == "__main__":
    main()
