from datetime import UTC, datetime
from functools import partial
import sqlite3

from langgraph.types import Command

from flow.contracts import Draft, FlowDeps, QualifierResult, Ticket, load_config
from flow.langgraph_app import build_ticket_graph, initial_state
from flow.tools import gather_evidence
from ml.qualifier.src.dataset_build.schema import TicketLabel


def _deps(label: TicketLabel, config):
    qualifier = QualifierResult(
        status="valid", label=label, raw=label.model_dump_json(),
        model_version="fake-qualifier-v1", latency_seconds=0.001,
    )

    def grounded_draft(ticket, _qualifier, desk, version, *, evidence):
        source = next(fact.source_id for fact in evidence.facts if fact.field == "approved_guidance")
        text = (
            "Support can explain the documented evidence submission process. "
            f"[{source}]"
        )
        return Draft(
            version=version, text=text, desk=desk, model="fake-drafter-v1",
            prompt_version="fake-v1", cost_usd=0, latency_seconds=0.002,
            evidence_mode=evidence.mode, source_ids=evidence.source_ids,
            source_versions=tuple(sorted({(fact.source_id, fact.source_version) for fact in evidence.facts})),
        )

    return FlowDeps(
        qualify=lambda _ticket: qualifier,
        draft=lambda *_args: (_ for _ in ()).throw(AssertionError("grounded writer expected")),
        grounded_draft=grounded_draft,
        policy_version=config.policy_version,
        gather_evidence=partial(gather_evidence, config=config),
        flow_config=config,
    )


def test_full_graph_waits_for_human_approval_and_explicit_send(tmp_path) -> None:
    metrics_path = tmp_path / "flow-metrics.sqlite"
    config = load_config().model_copy(update={
        "metrics_enabled": True, "metrics_db_path": str(metrics_path),
    })
    label = TicketLabel(
        intent="dispute", sub_intent="chargeback", transaction_id="TX-000430",
        amount="", currency="", urgency="high", sentiment="neutral",
    )
    deps = _deps(label, config)
    graph = build_ticket_graph(deps)
    ticket = Ticket(
        ticket_id="flow-e2e-chargeback", merchant_id=config.merchant_id,
        body="Please review chargeback evidence for transaction TX-000430.",
        created_at=datetime(2026, 11, 9, tzinfo=UTC),
    )
    graph_config = {"configurable": {"thread_id": ticket.ticket_id}}

    waiting = graph.invoke(initial_state(ticket), config=graph_config)
    run = waiting["ticket_run"]
    assert run["status"] == "awaiting_validation"
    assert run["evidence_decision"]["mode"] == "factual"
    assert run["evidence_decision"]["source_ids"] == [
        "ledger_tx_000430", "kb_disputes_chargeback_v1"
    ]
    node_ids = {event["node_id"] for event in waiting["lifecycle_events"]}
    assert {
        "intake", "qualifier", "field_check", "routing", "context_plan", "tools",
        "evidence_gate", "drafter", "policy_check", "finalize_ticket",
    } <= node_ids

    send_wait = graph.invoke(
        Command(resume={"action": "approve", "actor": "reviewer-1"}),
        config=graph_config,
    )
    assert send_wait["ticket_run"]["status"] == "ready_to_send"
    sent = graph.invoke(
        Command(resume={
            "action": "send", "actor": "reviewer-1", "idempotency_key": "e2e-send-1",
            "disposition": "leave_open",
        }),
        config=graph_config,
    )
    assert sent["ticket_run"]["status"] == "sent_open"
    assert len(sent["ticket_run"]["send_receipts"]) == 1
    with sqlite3.connect(metrics_path) as connection:
        recorded_nodes = {
            row[0] for row in connection.execute("SELECT DISTINCT node_id FROM flow_metric_events")
        }
        aggregate_count = connection.execute(
            "SELECT COUNT(*) FROM flow_metric_aggregates"
        ).fetchone()[0]
        metric_payloads = [row[0] for row in connection.execute(
            "SELECT safe_metrics_json FROM flow_metric_events"
        )]
    assert {"intake", "qualifier", "tools", "evidence_gate", "policy_check", "simulated_send"} <= recorded_nodes
    assert aggregate_count > 0
    assert all(ticket.body not in payload for payload in metric_payloads)


def test_documentary_route_does_not_call_sql(monkeypatch) -> None:
    import flow.tools

    def unexpected_sql(*_args, **_kwargs):
        raise AssertionError("SQL must not run for a documentary API request")

    monkeypatch.setattr(flow.tools, "lookup_ledger", unexpected_sql)
    config = load_config().model_copy(update={"metrics_enabled": False})
    label = TicketLabel(
        intent="technical_api", sub_intent="api_error", transaction_id="",
        amount="", currency="", urgency="medium", sentiment="neutral",
    )
    deps = _deps(label, config)
    graph = build_ticket_graph(deps)
    ticket = Ticket(
        ticket_id="flow-e2e-api-doc", merchant_id=config.merchant_id,
        body="We have an API error at the endpoint and response code.",
        created_at=datetime(2026, 11, 9, tzinfo=UTC),
    )
    result = graph.invoke(
        initial_state(ticket), config={"configurable": {"thread_id": ticket.ticket_id}}
    )
    assert result["ticket_run"]["context_plan"]["ledger_required"] is False
    assert result["ticket_run"]["context_plan"]["knowledge_required"] is True
    assert result["ticket_run"]["evidence_decision"]["mode"] == "documentary"


def test_final_compliance_block_returns_to_human_before_send() -> None:
    config = load_config().model_copy(update={"metrics_enabled": False})
    label = TicketLabel(
        intent="dispute", sub_intent="chargeback", transaction_id="TX-000430",
        amount="", currency="", urgency="high", sentiment="neutral",
    )
    graph = build_ticket_graph(_deps(label, config))
    ticket = Ticket(
        ticket_id="flow-e2e-final-gate", merchant_id=config.merchant_id,
        body="Please review chargeback evidence for transaction TX-000430.",
        created_at=datetime(2026, 11, 9, tzinfo=UTC),
    )
    graph_config = {"configurable": {"thread_id": ticket.ticket_id}}

    result = graph.invoke(initial_state(ticket), config=graph_config)
    result = graph.invoke(
        Command(resume={
            "action": "write", "actor": "reviewer-1",
            "text": "We guarantee a refund. [kb_disputes_chargeback_v1]",
        }), config=graph_config,
    )
    result = graph.invoke(
        Command(resume={"action": "approve", "actor": "reviewer-1"}),
        config=graph_config,
    )
    result = graph.invoke(
        Command(resume={
            "action": "send", "actor": "reviewer-1", "idempotency_key": "blocked-send",
            "disposition": "leave_open",
        }), config=graph_config,
    )
    blocked = result["ticket_run"]
    assert blocked["status"] == "awaiting_validation"
    assert blocked["final_policy_check"]["status"] == "blocked"
    assert "REFUND_PROMISE" in blocked["final_policy_check"]["findings"]
    assert blocked["send_receipts"] == []
    assert blocked["human_actions"][-1]["action"] == "send_blocked"

    result = graph.invoke(
        Command(resume={
            "action": "write", "actor": "reviewer-1",
            "text": "Support can explain the documented evidence submission process. "
            "[kb_disputes_chargeback_v1]",
        }), config=graph_config,
    )
    result = graph.invoke(
        Command(resume={"action": "approve", "actor": "reviewer-1"}),
        config=graph_config,
    )
    result = graph.invoke(
        Command(resume={
            "action": "send", "actor": "reviewer-1", "idempotency_key": "safe-send",
            "disposition": "leave_open",
        }), config=graph_config,
    )
    assert result["ticket_run"]["status"] == "sent_open"
    assert len(result["ticket_run"]["send_receipts"]) == 1
