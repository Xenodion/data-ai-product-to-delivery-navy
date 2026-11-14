"""Tier-2, local read-only synthetic SQL ledger and deterministic Text Search."""

import json
import re
import sqlite3
import time
import unicodedata
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from flow import world_access
from flow.contracts import (
    ContextPlan,
    Desk,
    EvidenceFact,
    EvidenceResult,
    FlowConfig,
    LedgerToolResult,
    RetrievalToolResult,
    Ticket,
    load_config,
)

FLOW_DIR = Path(__file__).parent


class _LedgerRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    merchant_id: str
    transaction_id: str
    status: str
    updated_at: str
    source_id: str
    source_version: str


class _LedgerFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    records: tuple[_LedgerRecord, ...]


class _KnowledgeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    version: str
    desk: Desk
    sub_intents: tuple[str, ...]
    title: str
    content: str
    keywords: tuple[str, ...]
    status: str
    valid_from: date
    valid_until: date | None = None


class _KnowledgeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    documents: tuple[_KnowledgeDocument, ...]


@lru_cache(maxsize=4)
def _ledger_records(path: Path) -> tuple[_LedgerRecord, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _LedgerFixture.model_validate(raw).records


@lru_cache(maxsize=4)
def _knowledge_documents(path: Path) -> tuple[_KnowledgeDocument, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _KnowledgeFixture.model_validate(raw).documents


def _not_called(plan: ContextPlan) -> EvidenceResult:
    return EvidenceResult(
        ledger=LedgerToolResult(status="not_run" if plan.ledger_required else "not_required"),
        retrieval=RetrievalToolResult(
            status="not_run" if plan.knowledge_required else "not_required"
        ),
    )


def lookup_ledger(plan: ContextPlan, config: FlowConfig | None = None) -> LedgerToolResult:
    """Use parameterized SQL against an ephemeral, query-only view of the fixture."""
    cfg = config or load_config()
    if not plan.ledger_required:
        return LedgerToolResult(status="not_required")
    if not cfg.ledger_enabled:
        return LedgerToolResult(status="unavailable")
    if not plan.transaction_id:
        return LedgerToolResult(status="unavailable")

    started = time.perf_counter()
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(":memory:")
        connection.execute(
            "CREATE TABLE ledger (merchant_id TEXT, transaction_id TEXT, status TEXT, "
            "updated_at TEXT, source_id TEXT, source_version TEXT)"
        )
        ledger_path = FLOW_DIR / cfg.ledger_fixture_path
        connection.executemany(
            "INSERT INTO ledger VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    record.merchant_id,
                    record.transaction_id,
                    record.status,
                    record.updated_at,
                    record.source_id,
                    record.source_version,
                )
                for record in _ledger_records(ledger_path)
            ],
        )
        deadline = started + cfg.tool_timeout_seconds
        connection.set_progress_handler(
            lambda: int(time.perf_counter() > deadline), 100
        )
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            "SELECT merchant_id, transaction_id, status, updated_at, source_id, source_version "
            "FROM ledger WHERE transaction_id = ? AND merchant_id = ?",
            (plan.transaction_id, plan.merchant_id),
        ).fetchall()
        if len(rows) > 1:
            result = LedgerToolResult(status="candidate_selection")
        elif not rows:
            foreign = connection.execute(
                "SELECT 1 FROM ledger WHERE transaction_id = ? LIMIT 1",
                (plan.transaction_id,),
            ).fetchone()
            result = (
                LedgerToolResult(
                    status="wrong_merchant",
                    foreign_identifiers=(plan.transaction_id,),
                )
                if foreign
                else LedgerToolResult(status="not_found")
            )
        else:
            merchant_id, transaction_id, status, updated_at, source_id, source_version = rows[0]
            fact = EvidenceFact(
                field="transaction_status",
                value=status,
                source_id=source_id,
                source_version=source_version,
            )
            date_fact = EvidenceFact(
                field="record_updated_at",
                value=updated_at,
                source_id=source_id,
                source_version=source_version,
            )
            result = LedgerToolResult(
                status="exact_id",
                merchant_id=merchant_id,
                verified_transaction_id=transaction_id,
                source_ids=(source_id,),
                facts=(fact, date_fact),
                allowed_figures=(updated_at,),
            )
        if time.perf_counter() - started > cfg.tool_timeout_seconds:
            return LedgerToolResult(status="unavailable")
        return result
    except (OSError, sqlite3.Error, json.JSONDecodeError, ValidationError, ValueError):
        return LedgerToolResult(status="unavailable")
    finally:
        if connection is not None:
            connection.close()


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _normalize(value)) if len(token) > 2}


def search_knowledge(
    ticket: Ticket,
    plan: ContextPlan,
    *,
    as_of: date | None = None,
    config: FlowConfig | None = None,
) -> RetrievalToolResult:
    """Return at most two approved, current passages for the routed desk/sub-intent."""
    cfg = config or load_config()
    if not plan.knowledge_required:
        return RetrievalToolResult(status="not_required")
    if not cfg.knowledge_enabled:
        return RetrievalToolResult(status="unavailable")
    started = time.perf_counter()
    today = as_of or ticket.created_at.astimezone(UTC).date()
    try:
        query_tokens = _tokens(ticket.message_text)
        knowledge_path = FLOW_DIR / cfg.knowledge_fixture_path
        eligible = [
            document
            for document in _knowledge_documents(knowledge_path)
            if document.status == "approved"
            and document.desk == plan.desk
            and plan.sub_intent in document.sub_intents
            and document.valid_from <= today
            and (document.valid_until is None or document.valid_until >= today)
        ]
        scored = sorted(
            (
                (len(query_tokens & _tokens(" ".join((*document.keywords, document.title)))), document)
                for document in eligible
            ),
            key=lambda item: (-item[0], item[1].source_id),
        )
        ranked = [
            document
            for score, document in scored
            if score >= cfg.knowledge_min_overlap_tokens
        ][: cfg.max_knowledge_results]
        if time.perf_counter() - started > cfg.tool_timeout_seconds:
            return RetrievalToolResult(status="unavailable")
        if not ranked:
            return RetrievalToolResult(status="empty")

        facts = tuple(
            EvidenceFact(
                field="approved_guidance",
                value=document.content,
                source_id=document.source_id,
                source_version=document.version,
            )
            for document in ranked
        )
        return RetrievalToolResult(
            status="found",
            source_ids=tuple(document.source_id for document in ranked),
            facts=facts,
        )
    except (OSError, json.JSONDecodeError, ValidationError, ValueError):
        return RetrievalToolResult(status="unavailable")


def _future_result(future: Future, fallback: object):
    try:
        return future.result()
    except Exception:  # noqa: BLE001 - a failed source becomes unavailable, never fabricated
        return fallback


def gather_evidence(
    ticket: Ticket, plan: ContextPlan, config: FlowConfig | None = None
) -> EvidenceResult:
    """Invoke only planned SQL/Text Search tools, awaiting both when both are required."""
    cfg = config or load_config()
    if plan.status != "planned":
        return _not_called(plan)

    ledger_result = (
        LedgerToolResult(status="unavailable")
        if plan.ledger_required and not cfg.ledger_enabled
        else LedgerToolResult(status="not_required")
        if not plan.ledger_required
        else None
    )
    retrieval_result = (
        RetrievalToolResult(status="unavailable")
        if plan.knowledge_required and not cfg.knowledge_enabled
        else RetrievalToolResult(status="not_required")
        if not plan.knowledge_required
        else None
    )

    needs_ledger = ledger_result is None
    needs_retrieval = retrieval_result is None
    with ThreadPoolExecutor(max_workers=max(1, int(needs_ledger) + int(needs_retrieval))) as pool:
        as_of = ticket.created_at.astimezone(UTC)
        if cfg.world_database_path:  # optional world database behind the same result types
            ledger_future = (
                pool.submit(world_access.lookup_ledger, plan, cfg, as_of) if needs_ledger else None
            )
            retrieval_future = (
                pool.submit(world_access.search_policies, plan, cfg, as_of.date())
                if needs_retrieval
                else None
            )
        else:
            ledger_future = pool.submit(lookup_ledger, plan, cfg) if needs_ledger else None
            retrieval_future = (
                pool.submit(search_knowledge, ticket, plan, as_of=as_of.date(), config=cfg)
                if needs_retrieval
                else None
            )
        # Both future results are awaited before the evidence gate may run.
        if ledger_future is not None:
            ledger_result = _future_result(ledger_future, LedgerToolResult(status="unavailable"))
        if retrieval_future is not None:
            retrieval_result = _future_result(
                retrieval_future, RetrievalToolResult(status="unavailable")
            )

    return EvidenceResult(ledger=ledger_result, retrieval=retrieval_result)
