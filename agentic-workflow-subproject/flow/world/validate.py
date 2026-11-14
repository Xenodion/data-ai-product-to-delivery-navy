"""Invariants of the world (design section 9), checked on the finished database."""

import sqlite3
from collections.abc import Collection, Mapping, Sequence
from datetime import timedelta

from flow.world.config import WorldConfig
from flow.world.deck import DeckTicket
from flow.world.sampling import SelectedTicket
from flow.world.text_signals import extract_references

ROLE_SPLITS = {
    "current": {"test_natural"},
    "dev": {"val"},
    "history": {"train", "val"},
}
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def validate_world(
    conn: sqlite3.Connection,
    selected: Sequence[SelectedTicket],
    deck: Mapping[str, DeckTicket],
    shared_references: Collection[str],
    config: WorldConfig,
    threads_generated: bool = False,
) -> list[str]:
    """Return every violation found (empty when the world is valid).

    Thread-end rules need the generated replies, so they run only when ``threads_generated``.
    """
    problems: list[str] = []
    open_start = (config.window_end - timedelta(days=config.dates.open_days)).isoformat()
    reference_end = f"{config.reference_date.isoformat()}T23:59:59Z"
    tickets = {
        row[0]: row
        for row in conn.execute(
            "SELECT t.ticket_id, t.merchant_id, t.role, t.opened_at, t.contact_id, m.sector "
            "FROM tickets t JOIN merchants m USING (merchant_id)"
        )
    }
    if set(tickets) != {item.card_id for item in selected}:
        problems.append("tickets differ from the sampled list")
    for item in selected:
        row = tickets.get(item.card_id)
        if row is None:
            continue
        card = deck[item.card_id]
        if row[2] != item.role:
            problems.append(f"{item.card_id}: stored role {row[2]} differs from the sample")
        if item.split not in ROLE_SPLITS[item.role]:
            problems.append(f"{item.card_id}: split {item.split} cannot be role {item.role}")
        if row[5] != card.sector:
            problems.append(f"{item.card_id}: merchant sector {row[5]} differs from {card.sector}")
        if item.latest_bound and row[3][:10] < item.latest_bound.isoformat():
            problems.append(f"{item.card_id}: opened before a date its text cites")
        if row[2] == "history" and row[3][:10] >= open_start:
            problems.append(f"{item.card_id}: history ticket opened inside the current window")
        if row[3] > reference_end:
            problems.append(f"{item.card_id}: opened after the reference date")
        problems += _reference_problems(conn, item.card_id, row[1], card, shared_references)
    for row in conn.execute(
        "SELECT t.ticket_id FROM tickets t JOIN contacts c USING (contact_id) "
        "WHERE c.merchant_id <> t.merchant_id"
    ):
        problems.append(f"{row[0]}: contact belongs to another merchant")
    for ticket_id, body, direction in conn.execute(
        "SELECT ticket_id, body, direction FROM messages WHERE turn_index = 1"
    ):
        if body != deck[ticket_id].text or direction != "inbound":
            problems.append(f"{ticket_id}: turn 1 is not the unchanged deck text")
    for row in conn.execute(
        "SELECT ticket_id FROM tickets WHERE ticket_id NOT IN "
        "(SELECT ticket_id FROM messages WHERE turn_index = 1)"
    ):
        problems.append(f"{row[0]}: no first message")
    for table, column in (("transactions", "created_at"), ("messages", "sent_at")):
        late = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} > ?", (reference_end,))
        if late.fetchone()[0]:
            problems.append(f"{table}: rows dated after the reference date")
    history_late = conn.execute(
        "SELECT COUNT(*) FROM messages m JOIN tickets t USING (ticket_id) "
        "WHERE t.role = 'history' AND m.sent_at >= ?",
        (f"{open_start}T00:00:00Z",),
    ).fetchone()[0]
    if history_late:
        problems.append("history messages dated inside the current window")
    refund_excess = conn.execute(
        "SELECT COUNT(*) FROM refunds r JOIN transactions t USING (transaction_id) "
        "WHERE r.amount_minor > t.amount_minor"
    ).fetchone()[0]
    if refund_excess:
        problems.append("refunds above their transaction amount")
    if threads_generated:
        problems += _thread_problems(conn)
    return problems


def _reference_problems(
    conn: sqlite3.Connection,
    ticket_id: str,
    merchant_id: str,
    card: DeckTicket,
    shared_references: Collection[str],
) -> list[str]:
    problems = []
    for reference in dict.fromkeys((card.label.transaction_id, *extract_references(card.text))):
        if not reference:
            continue
        owner = conn.execute(
            "SELECT merchant_id FROM transactions WHERE transaction_id = ?", (reference,)
        ).fetchone()
        if owner is None or (owner[0] != merchant_id and reference not in shared_references):
            problems.append(f"{ticket_id}: reference {reference} missing or under another merchant")
    return problems


def _thread_problems(conn: sqlite3.Connection) -> list[str]:
    problems = []
    for ticket_id, state in conn.execute(
        "SELECT ticket_id, thread_state FROM tickets WHERE role = 'history'"
    ):
        messages = conn.execute(
            "SELECT author_kind, sent_at FROM messages WHERE ticket_id = ? ORDER BY turn_index",
            (ticket_id,),
        ).fetchall()
        stamps = [stamp for _, stamp in messages]
        if stamps != sorted(set(stamps)):
            problems.append(f"{ticket_id}: timestamps are not strictly increasing")
        if state in ("closed", "open_awaiting_merchant") and messages[-1][0] != "agent":
            problems.append(f"{ticket_id}: thread does not end on an agent message")
        has_outcome = conn.execute(
            "SELECT 1 FROM ticket_outcomes WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
        if (state == "closed") != bool(has_outcome):
            problems.append(f"{ticket_id}: outcome does not match the thread state")
    return problems
