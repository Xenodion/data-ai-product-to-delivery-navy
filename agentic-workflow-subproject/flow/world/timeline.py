"""Dates and ticket rows: when each sampled ticket was opened, and the state it is in."""

import argparse
import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from flow.world.assign import assign_tickets
from flow.world.config import DEFAULT_CONFIG_PATH, WorldConfig, load_world_config
from flow.world.deck import DeckTicket, load_deck
from flow.world.errors import AttributionError
from flow.world.merchants import MerchantBook, build_merchants
from flow.world.models import Ticket
from flow.world.rng import stage_rng
from flow.world.sampling import SampleManifest, SelectedTicket, sample_roles

LOGGER = logging.getLogger(__name__)
FIRST_HOUR, LAST_HOUR = 7, 19  # working hours, UTC


def opened_at_dates(selected: Sequence[SelectedTicket], config: WorldConfig) -> dict[str, datetime]:
    """Opening time of every ticket.

    History runs from the window start to ``history_gap_days`` before its end; ``current`` and
    ``dev`` fall in the last ``open_days``. A ticket is never opened before a date its text cites.

    Raises:
        AttributionError: a ticket cites a date later than the end of its role window.
    """
    window_end = config.window_end
    spans = {
        "history": (
            config.window_start,
            window_end - timedelta(days=config.dates.history_gap_days),
        ),
        "current": (window_end - timedelta(days=config.dates.open_days), window_end),
        "dev": (window_end - timedelta(days=config.dates.open_days), window_end),
    }
    rng = stage_rng(config.seed, "timeline")
    opened: dict[str, datetime] = {}
    for ticket in sorted(selected, key=lambda item: item.card_id):
        start, end = spans[ticket.role]
        if ticket.latest_bound is not None:
            start = max(start, ticket.latest_bound)
        if start > end:
            raise AttributionError(
                f"{ticket.card_id} cites {ticket.latest_bound} after its {ticket.role} window"
            )
        day = start + timedelta(days=rng.randint(0, (end - start).days))
        moment = time(rng.randint(FIRST_HOUR, LAST_HOUR), rng.randint(0, 59), rng.randint(0, 59))
        opened[ticket.card_id] = datetime.combine(day, moment, tzinfo=UTC)
    return opened


def build_tickets(
    selected: Sequence[SelectedTicket],
    deck: Mapping[str, DeckTicket],
    assignment: Mapping[str, str],
    book: MerchantBook,
    config: WorldConfig,
) -> tuple[Ticket, ...]:
    """Ticket rows: open and waiting for the agent, except history (closed or waiting)."""
    opened = opened_at_dates(selected, config)
    states = config.threads.end_state_weights
    rng = stage_rng(config.seed, "ticket-state")
    rows = []
    for ticket in sorted(selected, key=lambda item: item.card_id):
        card = deck[ticket.card_id]
        merchant_id = assignment[ticket.card_id]
        if ticket.role == "history":
            state = rng.choices(list(states), list(states.values()))[0]
        else:
            state = "open_awaiting_agent"
        rows.append(
            Ticket(
                ticket_id=ticket.card_id,
                merchant_id=merchant_id,
                contact_id=book.contact_id(merchant_id, card.persona, card.language),
                opened_at=opened[ticket.card_id],
                channel=card.channel,
                language=card.language,
                role=ticket.role,
                thread_state=state,
            )
        )
    return tuple(rows)


def timeline_report(
    tickets: Sequence[Ticket],
    deck: Mapping[str, DeckTicket],
    book: MerchantBook,
    count: int = 10,
) -> str:
    """Structured view of the busiest merchants (no ticket text) for the human check."""
    by_merchant: dict[str, list[Ticket]] = defaultdict(list)
    for ticket in tickets:
        by_merchant[ticket.merchant_id].append(ticket)
    merchants = {m.merchant_id: m for m in book.merchants}
    busiest = sorted(by_merchant, key=lambda m: (-len(by_merchant[m]), m))[:count]
    lines = []
    for merchant_id in busiest:
        merchant = merchants[merchant_id]
        lines += [
            (
                f"## {merchant_id} {merchant.name} ({merchant.sector}, {merchant.volume_tier}, "
                f"{merchant.settlement_currency}, onboarded {merchant.onboarded_at})"
            ),
            "",
            "| opened | role | state | desk intent / sub-intent | amount | persona |",
            "|---|---|---|---|---|---|",
        ]
        for ticket in sorted(by_merchant[merchant_id], key=lambda item: item.opened_at):
            label = deck[ticket.ticket_id].label
            amount = f"{label.amount} {label.currency}".strip() or "-"
            lines.append(
                f"| {ticket.opened_at:%Y-%m-%d} | {ticket.role} | {ticket.thread_state} | "
                f"{label.intent} / {label.sub_intent} | {amount} | {deck[ticket.ticket_id].persona} |"
            )
        lines.append("")
    return "\n".join(lines)


def build_people(
    deck_tickets: Sequence[DeckTicket], manifest: SampleManifest, config: WorldConfig
) -> tuple[MerchantBook, tuple[Ticket, ...], dict[str, DeckTicket]]:
    """Merchants, contacts and ticket rows for one sample."""
    deck = {ticket.card_id: ticket for ticket in deck_tickets}
    selected = {item.card_id: item for item in manifest.tickets}
    assignment = assign_tickets(manifest.tickets, deck, config)
    book = build_merchants(assignment, deck, selected, config)
    tickets = build_tickets(manifest.tickets, deck, assignment, book, config)
    return book, tickets, deck


def main() -> None:
    """Write the merchant timelines used for the human check of gate G3."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_world_config(arguments.config)
    deck_tickets = load_deck(config.resolve(config.paths.deck_dir), config.text_newline)
    manifest = sample_roles(deck_tickets, config)
    book, tickets, deck = build_people(deck_tickets, manifest, config)
    target = config.resolve(config.paths.artifacts_dir) / "reports" / "merchant_timelines.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(timeline_report(tickets, deck, book) + "\n", encoding="utf-8", newline="\n")
    LOGGER.info(
        "%d merchants, %d tickets; timelines: %s", len(book.merchants), len(tickets), target
    )


if __name__ == "__main__":
    main()
