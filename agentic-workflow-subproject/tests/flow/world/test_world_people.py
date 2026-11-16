"""Merchants, attribution and dates on a micro deck."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from flow.world.assign import assign_tickets, merchants_per_sector
from flow.world.config import SampleConfig, WorldConfig, load_world_config
from flow.world.deck import load_deck
from flow.world.errors import AttributionError
from flow.world.sampling import SelectedTicket, sample_roles
from flow.world.timeline import build_people, opened_at_dates


@pytest.fixture()
def config() -> WorldConfig:
    return load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=10, history=20, dev=6),
            "merchant_target": 9,
        }
    )


@pytest.fixture()
def world(write_deck: Callable[..., Path], config: WorldConfig):
    deck_tickets = load_deck(write_deck())
    manifest = sample_roles(deck_tickets, config)
    book, tickets, deck = build_people(deck_tickets, manifest, config)
    return manifest, book, tickets, deck


def test_merchants_per_sector_sums_to_target_with_one_merchant_minimum() -> None:
    shares = merchants_per_sector({"retail": 30, "saas": 5, "travel": 1}, 12)
    assert sum(shares.values()) == 12 - max(0, 12 - sum(shares.values()))
    assert all(share >= 1 for share in shares.values())
    assert shares["travel"] == 1


def test_merchants_per_sector_rejects_target_below_sector_count() -> None:
    with pytest.raises(AttributionError):
        merchants_per_sector({"retail": 3, "saas": 3}, 1)


def test_every_ticket_is_assigned_once_to_a_merchant_of_its_sector(world) -> None:
    manifest, book, tickets, deck = world
    sectors = {m.merchant_id: m.sector for m in book.merchants}
    assert sorted(t.ticket_id for t in tickets) == sorted(s.card_id for s in manifest.tickets)
    for ticket in tickets:
        assert sectors[ticket.merchant_id] == deck[ticket.ticket_id].sector


def test_every_merchant_holds_at_least_one_ticket(world) -> None:
    _, book, tickets, _ = world
    assert {m.merchant_id for m in book.merchants} == {t.merchant_id for t in tickets}


def test_contacts_carry_persona_and_language_of_their_tickets(world) -> None:
    _, book, tickets, deck = world
    contacts = {c.contact_id: c for c in book.contacts}
    for ticket in tickets:
        contact = contacts[ticket.contact_id]
        assert contact.merchant_id == ticket.merchant_id
        assert (contact.persona, contact.language) == (
            deck[ticket.ticket_id].persona,
            deck[ticket.ticket_id].language,
        )


def test_history_is_dated_before_the_open_window_and_open_tickets_inside_it(
    world, config: WorldConfig
) -> None:
    _, _, tickets, _ = world
    history_end = config.window_end - timedelta(days=config.dates.history_gap_days)
    open_start = config.window_end - timedelta(days=config.dates.open_days)
    for ticket in tickets:
        day = ticket.opened_at.date()
        if ticket.role == "history":
            assert config.window_start <= day <= history_end
        else:
            assert open_start <= day <= config.window_end
            assert ticket.thread_state == "open_awaiting_agent"
        assert ticket.thread_state != "open_awaiting_agent" or ticket.role != "history"


def test_a_ticket_is_never_opened_before_the_date_its_text_cites(config: WorldConfig) -> None:
    late = config.window_end - timedelta(days=5)
    selected = [
        SelectedTicket(
            card_id="h-1",
            split="train",
            role="history",
            latest_bound=config.window_start + timedelta(days=100),
            earliest_full_date=None,
        ),
        SelectedTicket(
            card_id="c-1",
            split="test_natural",
            role="current",
            latest_bound=late,
            earliest_full_date=None,
        ),
    ]
    opened = opened_at_dates(selected, config)
    assert opened["h-1"].date() >= config.window_start + timedelta(days=100)
    assert opened["c-1"].date() >= late


def test_a_date_cited_after_the_role_window_is_refused(config: WorldConfig) -> None:
    too_late = config.window_end - timedelta(days=config.dates.history_gap_days - 1)
    selected = [
        SelectedTicket(
            card_id="h-1",
            split="train",
            role="history",
            latest_bound=too_late,
            earliest_full_date=None,
        )
    ]
    with pytest.raises(AttributionError):
        opened_at_dates(selected, config)


def test_onboarding_precedes_every_cited_date_and_the_window(world, config: WorldConfig) -> None:
    manifest, book, tickets, _ = world
    cited = {s.card_id: s.earliest_full_date for s in manifest.tickets}
    onboarded = {m.merchant_id: m.onboarded_at for m in book.merchants}
    for ticket in tickets:
        assert onboarded[ticket.merchant_id] < config.window_start
        if cited[ticket.ticket_id]:
            assert onboarded[ticket.merchant_id] < cited[ticket.ticket_id]


def test_settlement_currency_is_a_held_currency(world) -> None:
    _, book, _, _ = world
    held: dict[str, set[str]] = {}
    for row in book.currencies:
        held.setdefault(row.merchant_id, set()).add(row.currency)
    for merchant in book.merchants:
        assert merchant.settlement_currency in held[merchant.merchant_id]


def test_build_people_is_deterministic(
    write_deck: Callable[..., Path], config: WorldConfig
) -> None:
    deck_tickets = load_deck(write_deck())
    manifest = sample_roles(deck_tickets, config)
    first = build_people(deck_tickets, manifest, config)
    second = build_people(deck_tickets, manifest, config)
    assert first[0].merchants == second[0].merchants
    assert first[1] == second[1]


def test_assignment_changes_with_the_seed(
    write_deck: Callable[..., Path], config: WorldConfig
) -> None:
    deck_tickets = load_deck(write_deck())
    manifest = sample_roles(deck_tickets, config)
    deck = {t.card_id: t for t in deck_tickets}
    other = config.model_copy(update={"seed": config.seed + 1})
    assert assign_tickets(manifest.tickets, deck, config) != assign_tickets(
        manifest.tickets, deck, other
    )
