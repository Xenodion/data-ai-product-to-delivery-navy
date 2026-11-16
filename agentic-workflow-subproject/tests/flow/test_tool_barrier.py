from datetime import UTC, datetime
from threading import Event, Lock, Thread

import flow.tools as tools
from flow.contracts import (
    ContextPlan,
    EvidenceFact,
    LedgerToolResult,
    RetrievalToolResult,
    Ticket,
    load_config,
)


def test_sql_and_rag_are_both_started_and_joined_before_return(monkeypatch) -> None:
    both_started = Event()
    release = Event()
    returned = Event()
    lock = Lock()
    started_count = 0

    def signal_both():
        nonlocal started_count
        with lock:
            started_count += 1
            if started_count == 2:
                both_started.set()
        assert release.wait(timeout=5), "test did not release the two tool calls"

    def fake_sql(plan, _config):
        signal_both()
        return LedgerToolResult(
            status="exact_id", merchant_id=plan.merchant_id,
            verified_transaction_id=plan.transaction_id, source_ids=("ledger-test",),
            facts=(EvidenceFact(
                field="transaction_status", value="processing",
                source_id="ledger-test", source_version="v1",
            ),),
        )

    def fake_rag(_ticket, _plan, *, as_of, config):
        signal_both()
        return RetrievalToolResult(
            status="found", source_ids=("kb-test",), facts=(EvidenceFact(
                field="approved_guidance", value="approved", source_id="kb-test", source_version="v1",
            ),),
        )

    monkeypatch.setattr(tools, "lookup_ledger", fake_sql)
    monkeypatch.setattr(tools, "search_knowledge", fake_rag)
    plan = ContextPlan(
        desk="payments", merchant_id="M-DEMO", sub_intent="status_inquiry",
        ledger_required=True, knowledge_required=True, transaction_id="TX-000430",
        status="planned",
    )
    ticket = Ticket(
        ticket_id="parallel-tools", merchant_id="M-DEMO", body="status TX-000430",
        created_at=datetime(2026, 11, 9, tzinfo=UTC),
    )
    results = []

    def run_tools():
        results.append(tools.gather_evidence(ticket, plan, load_config()))
        returned.set()

    worker = Thread(target=run_tools)
    worker.start()
    assert both_started.wait(timeout=2), "SQL and RAG should start concurrently"
    assert not returned.is_set(), "gather_evidence must wait while both tools are outstanding"
    release.set()
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert returned.is_set()
    assert results[0].ledger.status == "exact_id"
    assert results[0].retrieval.status == "found"
