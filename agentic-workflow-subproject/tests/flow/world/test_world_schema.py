import sqlite3
from pathlib import Path

import pytest

SCHEMA = Path(__file__).resolve().parents[3] / "flow" / "world" / "schema.sql"
STAMP = "2026-03-01T10:00:00Z"
EXPECTED_TABLES = {
    "merchants",
    "merchant_currencies",
    "contacts",
    "transactions",
    "refunds",
    "disputes",
    "payouts",
    "tickets",
    "ticket_outcomes",
    "messages",
    "policies",
    "policy_sub_intents",
}


@pytest.fixture()
def db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO merchants VALUES ('M-1', 'Atelier Test', 'retail', 'fr', 'FR', 'EUR', 'small', "
        "'standard', 120, 'verified', 'low', '2025-06-01')"
    )
    connection.execute("INSERT INTO contacts VALUES ('C-1', 'M-1', 'founder', 'fr')")
    return connection


def _ticket(db: sqlite3.Connection, ticket_id: str, role: str, state: str) -> None:
    db.execute(
        "INSERT INTO tickets VALUES (?, 'M-1', 'C-1', ?, 'formal_email', 'fr', ?, ?)",
        (ticket_id, STAMP, role, state),
    )


def test_schema_creates_every_expected_table(db: sqlite3.Connection) -> None:
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert names == EXPECTED_TABLES


def test_schema_accepts_current_ticket_waiting_for_agent(db: sqlite3.Connection) -> None:
    _ticket(db, "T-1", "current", "open_awaiting_agent")


@pytest.mark.parametrize("role", ["current", "dev"])
@pytest.mark.parametrize("state", ["closed", "open_awaiting_merchant"])
def test_schema_rejects_non_history_ticket_not_waiting_for_agent(
    db: sqlite3.Connection, role: str, state: str
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _ticket(db, "T-1", role, state)


@pytest.mark.parametrize("state", ["closed", "open_awaiting_merchant"])
def test_schema_accepts_history_ticket_closed_or_awaiting_merchant(
    db: sqlite3.Connection, state: str
) -> None:
    _ticket(db, "T-1", "history", state)


def test_schema_rejects_history_ticket_waiting_for_agent(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _ticket(db, "T-1", "history", "open_awaiting_agent")


def test_schema_rejects_ticket_of_unknown_merchant(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO tickets VALUES ('T-1', 'M-X', 'C-1', ?, 'formal_email', 'fr', 'current', "
            "'open_awaiting_agent')",
            (STAMP,),
        )


def test_schema_rejects_message_whose_author_contradicts_direction(db: sqlite3.Connection) -> None:
    _ticket(db, "T-1", "current", "open_awaiting_agent")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO messages VALUES ('MSG-1', 'T-1', 1, 'inbound', ?, 'hello', 'agent')",
            (STAMP,),
        )


def test_schema_rejects_duplicate_turn_index_within_a_ticket(db: sqlite3.Connection) -> None:
    _ticket(db, "T-1", "current", "open_awaiting_agent")
    db.execute(
        "INSERT INTO messages VALUES ('MSG-1', 'T-1', 1, 'inbound', ?, 'hello', 'merchant')",
        (STAMP,),
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO messages VALUES ('MSG-2', 'T-1', 1, 'inbound', ?, 'again', 'merchant')",
            (STAMP,),
        )


def test_schema_rejects_dispute_due_before_it_opened(db: sqlite3.Connection) -> None:
    db.execute(
        "INSERT INTO transactions VALUES ('TX-100001', 'M-1', 1000, 'EUR', 'settled', 'card', ?, ?)",
        (STAMP, STAMP),
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO disputes VALUES ('D-1', 'TX-100001', 'open', 'fraud', '2026-03-05T00:00:00Z', "
            "'2026-03-01T00:00:00Z')"
        )


def test_schema_rejects_non_positive_amount(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO transactions VALUES ('TX-100001', 'M-1', 0, 'EUR', 'settled', 'card', ?, NULL)",
            (STAMP,),
        )


def test_schema_rejects_policy_sub_intent_of_unknown_policy(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO policy_sub_intents VALUES ('POL-1', 'v1', 'chargeback')")


def test_schema_accepts_policy_applying_to_several_sub_intents(db: sqlite3.Connection) -> None:
    db.execute(
        "INSERT INTO policies VALUES ('POL-1', 'v1', 'disputes', 'en', 'approved', '2026-01-01', NULL, "
        "'compliance', 'Dispute handling', 'text')"
    )
    db.executemany(
        "INSERT INTO policy_sub_intents VALUES ('POL-1', 'v1', ?)",
        [("chargeback",), ("duplicate_charge",)],
    )
    assert db.execute("SELECT COUNT(*) FROM policy_sub_intents").fetchone()[0] == 2


def test_schema_accepts_a_triage_outcome_for_a_closed_history_ticket(
    db: sqlite3.Connection,
) -> None:
    _ticket(db, "T-1", "history", "closed")
    db.execute(
        "INSERT INTO ticket_outcomes VALUES ('T-1', 'triage', 'closed_no_action', ?)", (STAMP,)
    )


def test_schema_rejects_an_unknown_outcome_desk(db: sqlite3.Connection) -> None:
    _ticket(db, "T-1", "history", "closed")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO ticket_outcomes VALUES ('T-1', 'billing', 'resolved', ?)", (STAMP,))


def test_schema_keeps_triage_out_of_policies(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO policies VALUES ('POL-1', 'v1', 'triage', 'en', 'approved', '2026-01-01', NULL, "
            "'compliance', 'Triage', 'text')"
        )
