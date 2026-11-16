"""Ledger rows, the two realism rules and the money objects, on a micro deck."""

import json
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest
from world_test_factories import DEFAULT_TARGET, make_row, write_split_file

from flow.world.config import SampleConfig, WorldConfig, load_world_config
from flow.world.deck import load_deck
from flow.world.ledger import build_ledger, build_money_objects
from flow.world.money import format_amount, to_minor
from flow.world.sampling import sample_roles
from flow.world.timeline import build_people


def _target(**overrides: str) -> str:
    return json.dumps({**DEFAULT_TARGET, **overrides})


@pytest.fixture()
def config() -> WorldConfig:
    return load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=4, history=8, dev=2),
            "merchant_target": 3,
            "transactions_per_merchant": 10,
        }
    )


@pytest.fixture()
def world(tmp_path: Path, config: WorldConfig):
    """A deck with a plain, a duplicate_charge, an amount_mismatch and a malformed ticket."""
    rows = {
        "train": [
            make_row(
                f"t-{i}",
                f"Where is TX-{100000 + i}? Paid 100.00 EUR.",
                target=_target(transaction_id=f"TX-{100000 + i}"),
            )
            for i in range(4)
        ]
        + [
            make_row(
                "t-dup",
                "Charged twice TX-200001.",
                target=_target(
                    transaction_id="TX-200001", sub_intent="duplicate_charge", intent="dispute"
                ),
            ),
            make_row(
                "t-mis",
                "Wrong amount TX-200002.",
                target=_target(
                    transaction_id="TX-200002",
                    sub_intent="amount_mismatch",
                    intent="dispute",
                    amount="100.00",
                ),
            ),
            make_row(
                "t-bad",
                "Where is TX-12?",
                target=_target(transaction_id="", amount="", currency=""),
            ),
        ],
        "val": [make_row(f"v-{i}", "no ref", target=_target(transaction_id="")) for i in range(3)],
        "test_natural": [
            make_row(f"n-{i}", f"See TX-30000{i}.", target=_target(transaction_id=f"TX-30000{i}"))
            for i in range(4)
        ],
        "test_traps": [make_row("x-0", "trap")],
    }
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    for split, split_rows in rows.items():
        write_split_file(deck_dir / f"{split}.csv", split_rows)
    deck_tickets = load_deck(deck_dir)
    small = config.model_copy(update={"sample": SampleConfig(current=4, history=8, dev=2)})
    manifest = sample_roles(deck_tickets, small)
    book, tickets, deck = build_people(deck_tickets, manifest, small)
    selected = {item.card_id: item for item in manifest.tickets}
    build = build_ledger(tickets, deck, selected, book, small)
    return small, book, tickets, deck, build


def test_to_minor_and_format_amount_round_trip_two_decimals() -> None:
    assert to_minor("1373.20") == 137320
    assert to_minor("0.005") == 1
    assert format_amount(137320) == "1373.20"


def test_cited_reference_gets_one_row_under_its_merchant_with_the_annotated_amount(world) -> None:
    _, _, tickets, deck, build = world
    rows = {row.transaction_id: row for row in build.transactions}
    for ticket in tickets:
        label = deck[ticket.ticket_id].label
        if ticket.ticket_id.startswith(("t-", "n-")) and label.transaction_id:
            row = rows[label.transaction_id]
            assert row.merchant_id == ticket.merchant_id
            if label.sub_intent == "status_inquiry":
                assert row.amount_minor == to_minor(label.amount)


def test_ledger_identifiers_are_unique_and_malformed_references_add_nothing(world) -> None:
    _, _, _, _, build = world
    ids = [row.transaction_id for row in build.transactions]
    assert len(ids) == len(set(ids))
    assert "TX-12" not in ids
    assert build.cited["t-bad"] == ()


def test_duplicate_charge_adds_a_second_identical_charge_minutes_later(world) -> None:
    config, _, _, _, build = world
    first = next(row for row in build.transactions if row.transaction_id == "TX-200001")
    twins = [
        row
        for row in build.transactions
        if row.transaction_id != first.transaction_id
        and row.merchant_id == first.merchant_id
        and row.amount_minor == first.amount_minor
        and row.created_at - first.created_at
        == timedelta(minutes=config.ledger.duplicate_gap_minutes)
    ]
    assert len(twins) == 1


def test_amount_mismatch_ledger_amount_differs_by_about_the_configured_share(world) -> None:
    config, _, _, _, build = world
    row = next(row for row in build.transactions if row.transaction_id == "TX-200002")
    share = abs(row.amount_minor - 10000) / 10000
    assert share == pytest.approx(config.ledger.amount_mismatch_pct, abs=0.01)


def test_cited_transactions_are_created_before_their_ticket_opens(world) -> None:
    _, _, tickets, _, build = world
    rows = {row.transaction_id: row for row in build.transactions}
    for ticket in tickets:
        for reference in build.cited[ticket.ticket_id]:
            assert rows[reference].created_at <= ticket.opened_at - timedelta(days=1)
            settled = rows[reference].settled_at
            assert settled is None or settled <= ticket.opened_at


def test_every_merchant_gets_the_configured_number_of_filler_rows(world) -> None:
    config, book, _, _, build = world
    counts = {m.merchant_id: 0 for m in book.merchants}
    cited = {r for refs in build.cited.values() for r in refs}
    for row in build.transactions:
        if row.transaction_id not in cited and not row.transaction_id.startswith("TX-2000"):
            counts[row.merchant_id] += 1
    assert all(count >= config.transactions_per_merchant for count in counts.values())


def test_money_objects_follow_the_transactions(world) -> None:
    config, book, tickets, deck, build = world
    refunds, disputes, payouts = build_money_objects(build, tickets, deck, book, config)
    rows = {row.transaction_id: row for row in build.transactions}
    assert all(rows[r.transaction_id].status == "refunded" for r in refunds)
    assert all(r.amount_minor <= rows[r.transaction_id].amount_minor for r in refunds)
    for dispute in disputes:
        assert dispute.due_at > dispute.opened_at
        assert rows[dispute.transaction_id].status in ("disputed", "settled")
    refunded = {r.transaction_id for r in refunds}
    assert refunded == {
        row.transaction_id
        for row in build.transactions
        if row.status == "refunded" and row.settled_at
    }
    assert len({p.payout_id for p in payouts}) == len(payouts)
    for payout in payouts:
        assert payout.amount_minor > 0
        assert (payout.status == "paid") == (payout.paid_at is not None)
        assert (payout.status == "held") == (payout.held_reason is not None)


def test_build_ledger_is_deterministic(world) -> None:
    config, book, tickets, deck, build = world
    selected = {t.ticket_id: _selected_stub(t) for t in tickets}
    again = build_ledger(tickets, deck, selected, book, config)
    assert again.transactions == build.transactions


def _selected_stub(ticket):
    from flow.world.sampling import SelectedTicket

    return SelectedTicket(
        card_id=ticket.ticket_id,
        split="train",
        role=ticket.role,
        latest_bound=None,
        earliest_full_date=None,
    )


def test_shared_reference_belongs_to_one_ticket_only(
    write_deck: Callable[..., Path], config: WorldConfig
) -> None:
    deck_tickets = load_deck(write_deck())
    manifest = sample_roles(deck_tickets, config)
    book, tickets, deck = build_people(deck_tickets, manifest, config)
    selected = {item.card_id: item for item in manifest.tickets}
    build = build_ledger(tickets, deck, selected, book, config)
    owners = [r for refs in build.cited.values() for r in refs]
    assert len(owners) == len(set(owners))
