"""Read-only access to the merchant world database behind the existing tool result types.

The functions mirror ``lookup_ledger`` and ``search_knowledge`` of ``flow.tools``: same statuses,
same ``LedgerToolResult`` and ``RetrievalToolResult`` shapes, no new contract field. Every query is
parameterized, bounded, scoped to the planned merchant and dated by ``as_of`` so that a ticket can
never see a row created after it was opened.
"""

import sqlite3
import time
from datetime import UTC, date, datetime
from pathlib import Path

from flow.contracts import (
    ContextPlan,
    EvidenceFact,
    FlowConfig,
    LedgerToolResult,
    RetrievalToolResult,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORLD_VERSION = "world-v0"
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MINOR_PER_UNIT = 100
PROGRESS_STEPS = 100


def resolve_world_path(config: FlowConfig) -> Path:
    """Absolute path of the world database; a relative path is read from the project root."""
    path = Path(config.world_database_path or "")
    return path if path.is_absolute() else PROJECT_ROOT / path


def _open_read_only(config: FlowConfig, started: float) -> sqlite3.Connection:
    uri = f"file:{resolve_world_path(config).as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    deadline = started + config.tool_timeout_seconds
    connection.set_progress_handler(lambda: int(time.perf_counter() > deadline), PROGRESS_STEPS)
    connection.execute("PRAGMA query_only = ON")
    return connection


def _amount_text(minor: int) -> str:
    return f"{minor // MINOR_PER_UNIT}.{minor % MINOR_PER_UNIT:02d}"


def lookup_ledger(plan: ContextPlan, config: FlowConfig, as_of: datetime) -> LedgerToolResult:
    """Look up the cited transaction of the planned merchant, as it stood at ``as_of``."""
    if not plan.ledger_required:
        return LedgerToolResult(status="not_required")
    if not config.ledger_enabled or not plan.transaction_id:
        return LedgerToolResult(status="unavailable")
    started = time.perf_counter()
    connection: sqlite3.Connection | None = None
    try:
        connection = _open_read_only(config, started)
        row = connection.execute(
            "SELECT merchant_id, amount_minor, currency, status, created_at, settled_at "
            "FROM transactions WHERE transaction_id = ? AND created_at < ?",
            (plan.transaction_id, as_of.astimezone(UTC).strftime(STAMP_FORMAT)),
        ).fetchone()
        if time.perf_counter() - started > config.tool_timeout_seconds:
            return LedgerToolResult(status="unavailable")
        if row is None:
            return LedgerToolResult(status="not_found")
        merchant_id, amount_minor, currency, status, created_at, settled_at = row
        if merchant_id != plan.merchant_id:
            return LedgerToolResult(
                status="wrong_merchant", foreign_identifiers=(plan.transaction_id,)
            )
        source_id = f"world:transactions:{plan.transaction_id}"
        updated_at = settled_at or created_at
        amount = _amount_text(amount_minor)

        def fact(field: str, value: str) -> EvidenceFact:
            return EvidenceFact(
                field=field, value=value, source_id=source_id, source_version=WORLD_VERSION
            )

        return LedgerToolResult(
            status="exact_id",
            merchant_id=merchant_id,
            verified_transaction_id=plan.transaction_id,
            source_ids=(source_id,),
            facts=(
                fact("transaction_status", status),
                fact("record_updated_at", updated_at),
                fact("transaction_amount", amount),
                fact("transaction_currency", currency),
            ),
            allowed_figures=(updated_at, amount),
        )
    except sqlite3.Error:
        return LedgerToolResult(status="unavailable")
    finally:
        if connection is not None:
            connection.close()


def search_policies(plan: ContextPlan, config: FlowConfig, as_of: date) -> RetrievalToolResult:
    """Return at most ``max_knowledge_results`` approved, valid policies for desk and sub-intent."""
    if not plan.knowledge_required:
        return RetrievalToolResult(status="not_required")
    if not config.knowledge_enabled:
        return RetrievalToolResult(status="unavailable")
    started = time.perf_counter()
    connection: sqlite3.Connection | None = None
    try:
        connection = _open_read_only(config, started)
        rows = connection.execute(
            "SELECT p.source_id, p.version, p.text FROM policies p "
            "JOIN policy_sub_intents s ON s.source_id = p.source_id AND s.version = p.version "
            "WHERE p.status = 'approved' AND p.desk = ? AND s.sub_intent = ? "
            "AND p.valid_from <= ? AND (p.valid_until IS NULL OR p.valid_until >= ?) "
            "ORDER BY p.source_id LIMIT ?",
            (
                plan.desk,
                plan.sub_intent,
                as_of.isoformat(),
                as_of.isoformat(),
                config.max_knowledge_results,
            ),
        ).fetchall()
        if time.perf_counter() - started > config.tool_timeout_seconds:
            return RetrievalToolResult(status="unavailable")
        if not rows:
            return RetrievalToolResult(status="empty")
        return RetrievalToolResult(
            status="found",
            source_ids=tuple(source_id for source_id, _, _ in rows),
            facts=tuple(
                EvidenceFact(
                    field="approved_guidance",
                    value=text,
                    source_id=source_id,
                    source_version=version,
                )
                for source_id, version, text in rows
            ),
        )
    except sqlite3.Error:
        return RetrievalToolResult(status="unavailable")
    finally:
        if connection is not None:
            connection.close()
