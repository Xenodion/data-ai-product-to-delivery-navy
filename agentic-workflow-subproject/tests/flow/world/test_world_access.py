"""The flow reads the world through its existing tool result types."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from flow import tools, world_access
from flow.contracts import ContextPlan, FlowConfig, Ticket, load_config
from flow.policy import _source_status_conflict
from flow.world.build import build_world
from flow.world.config import PROJECT_ROOT, SampleConfig, load_world_config
from flow.world.deck import load_deck

KNOWLEDGE = PROJECT_ROOT / "flow" / "fixtures" / "knowledge.json"
LATE = datetime(2026, 11, 12, tzinfo=UTC)


@pytest.fixture()
def world(write_deck: Callable[..., Path], tmp_path: Path) -> tuple[FlowConfig, sqlite3.Row]:
    config = load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=10, history=20, dev=6),
            "merchant_target": 9,
            "transactions_per_merchant": 8,
        }
    )
    database = tmp_path / "world.sqlite"
    build_world(load_deck(write_deck()), config, KNOWLEDGE, database)
    with sqlite3.connect(database) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id = 'TX-123456'"
        ).fetchone()
    flow_config = load_config().model_copy(update={"world_database_path": str(database)})
    return flow_config, row


def _plan(row: sqlite3.Row, **overrides: object) -> ContextPlan:
    values = {
        "desk": "payments",
        "merchant_id": row["merchant_id"],
        "sub_intent": "status_inquiry",
        "ledger_required": True,
        "knowledge_required": True,
        "transaction_id": row["transaction_id"],
        "status": "planned",
    }
    return ContextPlan(**(values | overrides))


def test_cited_transaction_maps_to_an_exact_id_result(world) -> None:
    config, row = world
    result = world_access.lookup_ledger(_plan(row), config, LATE)
    assert result.status == "exact_id"
    assert result.source_ids == ("world:transactions:TX-123456",)
    facts = {fact.field: fact.value for fact in result.facts}
    assert facts["transaction_status"] == row["status"]
    assert facts["transaction_currency"] == row["currency"]
    amount = f"{row['amount_minor'] // 100}.{row['amount_minor'] % 100:02d}"
    assert facts["transaction_amount"] == amount
    assert amount in result.allowed_figures
    assert [f.field for f in result.facts].count("transaction_status") == 1


def test_another_merchant_gets_wrong_merchant_without_the_row(world) -> None:
    config, row = world
    result = world_access.lookup_ledger(_plan(row, merchant_id="M-OTHER"), config, LATE)
    assert result.status == "wrong_merchant"
    assert result.facts == ()


def test_unknown_reference_is_not_found(world) -> None:
    config, row = world
    assert world_access.lookup_ledger(
        _plan(row, transaction_id="TX-999999"), config, LATE
    ).status == ("not_found")


def test_a_ticket_cannot_see_a_transaction_created_after_it(world) -> None:
    config, row = world
    created = datetime.fromisoformat(row["created_at"])
    result = world_access.lookup_ledger(_plan(row), config, created - timedelta(minutes=1))
    assert result.status == "not_found"


def test_the_world_connection_is_read_only(world) -> None:
    config, _ = world
    connection = world_access._open_read_only(config, 0.0)
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("DELETE FROM transactions")
    connection.close()


def test_policies_come_back_approved_valid_and_bounded(world) -> None:
    config, row = world
    result = world_access.search_policies(
        _plan(row, sub_intent="delayed_credit"), config, date(2026, 11, 12)
    )
    assert result.status == "found"
    assert len(result.facts) <= config.max_knowledge_results
    assert {fact.field for fact in result.facts} == {"approved_guidance"}
    assert set(result.source_ids) <= {fact.source_id for fact in result.facts}


def test_draft_and_unknown_sub_intent_policies_are_never_returned(world) -> None:
    config, row = world
    draft = world_access.search_policies(
        _plan(row, sub_intent="status_inquiry"), config, date(2026, 11, 12)
    )
    assert all("unapproved" not in source_id for source_id in draft.source_ids)
    empty = world_access.search_policies(
        _plan(row, sub_intent="no_such_intent"), config, date(2026, 11, 12)
    )
    assert empty.status == "empty"


def test_retired_policy_is_not_valid_before_its_start_date(world) -> None:
    config, row = world
    early = world_access.search_policies(
        _plan(row, sub_intent="delayed_credit"), config, date(2020, 1, 1)
    )
    assert early.status == "empty"


def test_gather_evidence_uses_the_world_when_configured(world) -> None:
    config, row = world
    ticket = Ticket(
        ticket_id="x",
        merchant_id=row["merchant_id"],
        body="Where is TX-123456?",
        created_at=LATE,
    )
    evidence = tools.gather_evidence(ticket, _plan(row), config)
    assert evidence.ledger.status == "exact_id"
    assert evidence.retrieval.status in {"found", "empty"}


def test_default_configuration_still_uses_the_fixture_files() -> None:
    assert load_config().world_database_path is None


def test_status_conflict_check_still_fires_with_world_facts(world) -> None:
    config, row = world
    facts = world_access.lookup_ledger(_plan(row), config, LATE).facts
    stored = row["status"]
    claim = "Your payment is refunded." if stored != "refunded" else "Your payment has failed."
    assert _source_status_conflict(claim, facts) or stored in {"under_review", "disputed"}
