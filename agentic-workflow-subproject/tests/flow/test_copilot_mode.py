"""Tests for the four-position ``copilot_mode`` rollback switch (#60)."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import partial

import pytest
from langgraph.types import Command
from pydantic import ValidationError

from flow.contracts import CopilotMode, Draft, FlowDeps, QualifierResult, Ticket, load_config
from flow.langgraph_app import build_ticket_graph, initial_state
from flow.pipeline import process, reroute
from flow.tools import gather_evidence
from ml.qualifier.src.dataset_build.schema import TicketLabel

TICKET = Ticket(
    ticket_id="mode-case-1",
    merchant_id="M-DEMO",
    body="Please review chargeback evidence for transaction TX-000430.",
    created_at=datetime(2026, 11, 20, tzinfo=UTC),
)
LABEL = TicketLabel(
    intent="dispute",
    sub_intent="chargeback",
    transaction_id="TX-000430",
    amount="",
    currency="",
    urgency="high",
    sentiment="neutral",
)


def _qualifier(label: TicketLabel = LABEL) -> QualifierResult:
    return QualifierResult(
        status="valid",
        label=label,
        raw=label.model_dump_json(),
        model_version="fake-qualifier-v1",
        latency_seconds=0.001,
    )


def _grounded_writer(ticket: Ticket, _q: QualifierResult, desk: str, version: int, *, evidence) -> Draft:
    source = evidence.source_ids[0] if evidence.source_ids else "kb_disputes_chargeback_v1"
    return Draft(
        version=version,
        text=f"We reviewed the documented evidence requirements. [{source}]",
        desk=desk,  # type: ignore[arg-type]
        model="fake-drafter-v1",
        prompt_version="fake-v1",
        cost_usd=0.0,
        latency_seconds=0.001,
        evidence_mode=evidence.mode,
        source_ids=evidence.source_ids,
        source_versions=tuple(sorted({(f.source_id, f.source_version) for f in evidence.facts})),
    )


def _deps(
    mode: CopilotMode,
    *,
    forbid_qualifier: bool = False,
    forbid_drafter: bool = False,
    forbid_tools: bool = False,
) -> FlowDeps:
    cfg = load_config().model_copy(update={"copilot_mode": mode, "metrics_enabled": False})

    def qualify_fn(_ticket: Ticket) -> QualifierResult:
        if forbid_qualifier:
            raise AssertionError(f"Qualifier must not run when copilot_mode={mode}")
        return _qualifier()

    def draft_fn(*_args, **_kwargs) -> Draft:
        if forbid_drafter:
            raise AssertionError(f"Drafter must not run when copilot_mode={mode}")
        return _grounded_writer(*_args, **_kwargs)

    def tools_fn(*args, **kwargs):
        if forbid_tools:
            raise AssertionError(f"Tools must not run when copilot_mode={mode}")
        return gather_evidence(*args, config=cfg, **kwargs)

    return FlowDeps(
        qualify=qualify_fn,
        draft=lambda *_a: (_ for _ in ()).throw(AssertionError("grounded writer expected")),
        grounded_draft=draft_fn,
        policy_version=cfg.policy_version,
        gather_evidence=tools_fn,
        flow_config=cfg,
    )


def test_load_config_reads_default_and_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NAVY_COPILOT_MODE", raising=False)
    assert load_config().copilot_mode == "full"

    monkeypatch.setenv("NAVY_COPILOT_MODE", "l1_drafting_off")
    assert load_config().copilot_mode == "l1_drafting_off"

    monkeypatch.setenv("NAVY_COPILOT_MODE", "invalid_level")
    with pytest.raises(ValidationError):
        load_config()


def test_judge_off_preserves_routing_context_and_drafting() -> None:
    run = process(TICKET, _deps("judge_off"))
    assert run.desk == "disputes"
    assert run.status == "awaiting_validation"
    assert len(run.drafts) == 1
    assert run.final_author == "model"


def test_l1_drafting_off_keeps_routing_and_context_without_calling_drafter() -> None:
    deps = _deps("l1_drafting_off", forbid_drafter=True)
    graph = build_ticket_graph(deps)
    cfg = {"configurable": {"thread_id": "l1-thread"}}

    waiting = graph.invoke(initial_state(TICKET), config=cfg)
    run = waiting["ticket_run"]
    nodes = [ev["node_id"] for ev in waiting["lifecycle_events"]]

    assert "drafter" not in nodes
    assert "policy_check" not in nodes
    assert run["desk"] == "disputes"
    assert run["status"] == "awaiting_validation"
    assert run["drafts"] == []
    assert run["final_text"] is None
    assert run["evidence_decision"]["mode"] == "factual"
    assert "ledger_tx_000430" in run["evidence_decision"]["source_ids"]
    assert "DRAFTING_OFF" in run["reason_codes"]

    # Human writes, approves and sends through the final compliance gate
    written = graph.invoke(
        Command(resume={"action": "write", "actor": "agent-1", "text": "We received your chargeback request for TX-000430 and are checking the file."}),
        config=cfg,
    )
    assert written["ticket_run"]["final_author"] == "human"
    approved = graph.invoke(Command(resume={"action": "approve", "actor": "agent-1"}), config=cfg)
    assert approved["ticket_run"]["status"] == "ready_to_send"
    sent = graph.invoke(
        Command(resume={"action": "send", "actor": "agent-1", "idempotency_key": "l1-send-1", "disposition": "leave_open"}),
        config=cfg,
    )
    assert sent["ticket_run"]["status"] == "sent_open"


def test_l1_drafting_off_reroute_recomputes_context_without_drafting() -> None:
    deps = _deps("l1_drafting_off", forbid_drafter=True)
    first = process(TICKET, deps)
    corrected = reroute(first, "payments", deps, actor="agent-1", reason="payment status check")
    assert corrected.desk == "payments"
    assert corrected.status == "awaiting_validation"
    assert corrected.drafts == ()
    assert "DRAFTING_OFF" in corrected.reason_codes


def test_l2_routing_off_keeps_qualifier_hints_and_sends_all_tickets_to_rerouter() -> None:
    deps = _deps("l2_routing_off", forbid_drafter=True, forbid_tools=True)
    run = process(TICKET, deps)
    assert run.qualifier.status == "valid"
    assert run.qualifier.label is not None and run.qualifier.label.intent == "dispute"
    assert run.decision.priority == "high"
    assert run.desk == "triage"
    assert run.status == "awaiting_reroute"
    assert run.drafts == ()
    assert "ROUTING_OFF" in run.reason_codes

    # Once a person confirms the desk at L2, context loads without producing a model draft
    deps_with_tools = _deps("l2_routing_off", forbid_drafter=True, forbid_tools=False)
    assigned = reroute(run, "disputes", deps_with_tools, actor="router-1", reason="confirmed dispute desk")
    assert assigned.desk == "disputes"
    assert assigned.status == "awaiting_validation"
    assert assigned.drafts == ()
    assert assigned.evidence_decision is not None
    assert "DRAFTING_OFF" in assigned.reason_codes


def test_l3_copilot_off_skips_all_models_and_keeps_manual_queue_working() -> None:
    deps = _deps("l3_copilot_off", forbid_qualifier=True, forbid_drafter=True, forbid_tools=True)
    graph = build_ticket_graph(deps)
    cfg = {"configurable": {"thread_id": "l3-thread"}}

    waiting = graph.invoke(initial_state(TICKET), config=cfg)
    run = waiting["ticket_run"]
    nodes = [ev["node_id"] for ev in waiting["lifecycle_events"]]

    assert nodes == ["intake", "finalize_ticket", "human_wait"]
    assert run["qualifier"]["status"] == "unavailable"
    assert run["qualifier"]["model_version"] == "not_run"
    assert run["desk"] == "triage"
    assert run["status"] == "awaiting_reroute"
    assert run["drafts"] == []
    assert run["reason_codes"] == ["COPILOT_OFF"]

    # Manual desk assignment -> manual reply -> approval -> final gate -> simulated send
    routed = graph.invoke(
        Command(resume={"action": "reroute", "desk": "disputes", "actor": "agent-2", "reason": "manual triage"}),
        config=cfg,
    )
    assert routed["ticket_run"]["status"] == "manual_handling"
    assert routed["ticket_run"]["desk"] == "disputes"

    written = graph.invoke(
        Command(resume={"action": "write", "actor": "agent-2", "text": "Hello, our disputes team is reviewing TX-000430."}),
        config=cfg,
    )
    assert written["ticket_run"]["status"] == "awaiting_validation"
    approved = graph.invoke(Command(resume={"action": "approve", "actor": "agent-2"}), config=cfg)
    assert approved["ticket_run"]["status"] == "ready_to_send"
    sent = graph.invoke(
        Command(resume={"action": "send", "actor": "agent-2", "idempotency_key": "l3-send-1", "disposition": "close"}),
        config=cfg,
    )
    assert sent["ticket_run"]["status"] == "sent_closed"
