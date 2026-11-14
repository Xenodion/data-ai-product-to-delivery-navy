"""Merchant profile and ticket history for the front end, read from the world database.

The flow's tools never call this module. Tickets of role ``current`` are held back for the final
evaluation and are only listed when ``FlowConfig.world_show_current`` is set.
"""

import sqlite3
import time
from typing import Any

from flow.contracts import FlowConfig
from flow.world_access import _open_read_only

HISTORY_LIMIT = 20
TRANSACTION_LIMIT = 10
EXCERPT_CHARS = 300


def merchant_context(config: FlowConfig, merchant_id: str) -> dict[str, Any] | None:
    """Profile, recent money activity and ticket history of one merchant; None if unknown."""
    roles = ("history", "dev", "current") if config.world_show_current else ("history", "dev")
    connection = _open_read_only(config, time.perf_counter())
    connection.row_factory = sqlite3.Row
    try:
        merchant = connection.execute(
            "SELECT * FROM merchants WHERE merchant_id = ?", (merchant_id,)
        ).fetchone()
        if merchant is None:
            return None
        marks = ",".join("?" * len(roles))
        tickets = connection.execute(
            "SELECT t.ticket_id, t.opened_at, t.channel, t.language, t.role, t.thread_state, "
            "substr(m.body, 1, ?) AS excerpt, o.desk, o.resolution "
            "FROM tickets t JOIN messages m ON m.ticket_id = t.ticket_id AND m.turn_index = 1 "
            "LEFT JOIN ticket_outcomes o ON o.ticket_id = t.ticket_id "
            f"WHERE t.merchant_id = ? AND t.role IN ({marks}) "
            "ORDER BY t.opened_at DESC LIMIT ?",
            (EXCERPT_CHARS, merchant_id, *roles, HISTORY_LIMIT),
        ).fetchall()
        transactions = connection.execute(
            "SELECT transaction_id, amount_minor, currency, status, created_at FROM transactions "
            "WHERE merchant_id = ? ORDER BY created_at DESC LIMIT ?",
            (merchant_id, TRANSACTION_LIMIT),
        ).fetchall()
        counts = connection.execute(
            "SELECT (SELECT count(*) FROM disputes d JOIN transactions x USING (transaction_id) "
            " WHERE x.merchant_id = :m AND d.status IN ('open', 'under_review')), "
            "(SELECT count(*) FROM payouts WHERE merchant_id = :m AND status = 'held')",
            {"m": merchant_id},
        ).fetchone()
        currencies = [
            r[0]
            for r in connection.execute(
                "SELECT currency FROM merchant_currencies WHERE merchant_id = ? ORDER BY currency",
                (merchant_id,),
            )
        ]
    finally:
        connection.close()
    return {
        "profile": {**dict(merchant), "currencies": currencies},
        "open_disputes": counts[0],
        "held_payouts": counts[1],
        "recent_transactions": [dict(r) for r in transactions],
        "tickets": [dict(r) for r in tickets],
    }
