"""Plan of every history thread: size, timing, outcome and fact sheet, all decided by code."""

import re
import sqlite3
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time, timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict

from flow.world.config import WorldConfig
from flow.world.deck import DeckTicket
from flow.world.desks import outcome_desk
from flow.world.rng import stage_rng
from flow.world.text_signals import extract_references
from flow.world.validate import STAMP_FORMAT


class PlannedMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    turn_index: int
    author_kind: str
    sent_at: AwareDatetime


class ThreadPlan(BaseModel):
    """What the model is asked to write; the opening message is turn 1 and is never rewritten."""

    model_config = ConfigDict(frozen=True)

    ticket_id: str
    desk: str
    sub_intent: str
    language: str
    channel: str
    state: str  # closed or open_awaiting_merchant
    opening: str
    messages: tuple[PlannedMessage, ...]  # turns 2..n
    facts: tuple[str, ...]
    policy: str

    def stamps(self) -> tuple[str, ...]:
        return tuple(m.sent_at.strftime(STAMP_FORMAT) for m in self.messages)


def digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _facts(conn: sqlite3.Connection, merchant_id: str, opening: str) -> tuple[str, ...]:
    name, plan = conn.execute(
        "SELECT name, plan FROM merchants WHERE merchant_id = ?", (merchant_id,)
    ).fetchone()
    lines = [f"Merchant: {name}, plan {plan}"]
    for reference in extract_references(opening):
        row = conn.execute(
            "SELECT amount_minor, currency, status, created_at FROM transactions "
            "WHERE transaction_id = ? AND merchant_id = ?",
            (reference, merchant_id),
        ).fetchone()
        if row:
            amount = f"{row[0] // 100}.{row[0] % 100:02d}"
            lines.append(f"{reference}: {amount} {row[1]}, status {row[2]}, created {row[3][:10]}")
    return tuple(lines)


def _policy(conn: sqlite3.Connection, desk: str, sub_intent: str) -> str:
    row = conn.execute(
        "SELECT p.text FROM policies p JOIN policy_sub_intents s "
        "ON s.source_id = p.source_id AND s.version = p.version "
        "WHERE p.status = 'approved' AND p.desk = ? AND s.sub_intent = ? "
        "ORDER BY p.source_id LIMIT 1",
        (desk, sub_intent),
    ).fetchone()
    return row[0] if row else ""


def plan_threads(
    conn: sqlite3.Connection, deck: Mapping[str, DeckTicket], config: WorldConfig
) -> tuple[ThreadPlan, ...]:
    """One plan per history ticket of a world v0 database, in ticket-id order."""
    rng = stage_rng(config.seed, "thread-plan")
    weights = config.threads.exchange_weights
    rows = conn.execute(
        "SELECT t.ticket_id, t.merchant_id, t.opened_at, t.thread_state, m.body "
        "FROM tickets t JOIN messages m ON m.ticket_id = t.ticket_id AND m.turn_index = 1 "
        "WHERE t.role = 'history' ORDER BY t.ticket_id"
    ).fetchall()
    plans = []
    for ticket_id, merchant_id, opened_at, state, opening in rows:
        card = deck[ticket_id]
        label_desk = outcome_desk(card.label)
        exchanges = rng.choices(list(weights), list(weights.values()))[0]
        moment = _parse(opened_at)
        steps = []
        low, high = config.threads.reply_hours
        chase_low, chase_high = config.threads.chase_days
        for turn in range(2, 3 + 2 * exchanges):
            agent = turn % 2 == 0
            delta = (
                timedelta(minutes=rng.randint(low * 60, high * 60))
                if agent
                else timedelta(days=rng.randint(chase_low, chase_high), minutes=rng.randint(0, 600))
            )
            moment += delta
            steps.append(PlannedMessage(turn_index=turn, author_kind="agent" if agent else "merchant", sent_at=moment))
        plans.append(
            ThreadPlan(
                ticket_id=ticket_id,
                desk=label_desk,
                sub_intent=card.label.sub_intent,
                language=card.language,
                channel=card.channel,
                state=state,
                opening=opening,
                messages=tuple(steps),
                facts=_facts(conn, merchant_id, opening),
                policy=_policy(conn, label_desk, card.label.sub_intent),
            )
        )
    return tuple(plans)


def _parse(stamp: str) -> datetime:
    return datetime.strptime(stamp, STAMP_FORMAT).replace(tzinfo=UTC)


def last_allowed(config: WorldConfig) -> datetime:
    """Threads must end before the current window opens."""
    start = config.window_end - timedelta(days=config.dates.open_days)
    return datetime.combine(start, time(0), tzinfo=UTC)


def plan_summary(plans: Sequence[ThreadPlan]) -> dict[str, int]:
    return {
        "threads": len(plans),
        "messages_to_write": sum(len(p.messages) for p in plans),
        "closed": sum(p.state == "closed" for p in plans),
    }
