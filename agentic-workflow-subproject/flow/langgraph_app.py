"""Checkpointable LangGraph orchestration for the initial ticket pipeline and review."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any, Literal, TypedDict, cast
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from flow.contracts import Desk, FlowDeps, PipelineWork, Ticket, TicketRun, load_config
from flow.human_actions import (
    approve_reply,
    close_manual,
    edit_draft,
    handoff_to_rerouter,
    send_simulated,
    write_reply,
)
from flow.pipeline import reroute
from flow.metrics_store import MetricsStore
from flow.pipeline_steps import (
    context_plan_step,
    drafter_step,
    evidence_gate_step,
    field_check_step,
    finalize_step,
    intake_step,
    needs_human_routing,
    policy_check_step,
    qualifier_step,
    routing_step,
    tools_step,
)


class FlowState(TypedDict, total=False):
    """Serializable graph state. Dependencies stay in the graph closure."""

    ticket: dict[str, Any]
    previous_run: dict[str, Any] | None
    ticket_run: dict[str, Any]
    pipeline_work: dict[str, Any]
    human_command: dict[str, Any]
    action_error: str | None
    send_error: str | None
    metrics: dict[str, Any]
    lifecycle_events: list[dict[str, Any]]
    node_attempts: dict[str, int]
    flow_id: str


def _run(state: FlowState) -> TicketRun:
    return TicketRun.model_validate(state["ticket_run"])


def _record_node(
    state: FlowState,
    node_id: str,
    started: float,
    outcome: str,
    *,
    metrics: dict[str, Any] | None = None,
    ticket_run: TicketRun | None = None,
    metrics_store: MetricsStore | None = None,
    **state_updates: Any,
) -> dict[str, Any]:
    node_metrics = dict(state.get("metrics", {}))
    counts = dict(node_metrics.get("node_executions_total", {}))
    counts[f"{node_id}:{outcome}"] = counts.get(f"{node_id}:{outcome}", 0) + 1
    durations = {
        key: list(value)
        for key, value in node_metrics.get("node_duration_ms", {}).items()
    }
    duration_ms = round((monotonic() - started) * 1000, 3)
    durations.setdefault(node_id, []).append(duration_ms)
    start_text = node_metrics.get("flow_started_at")
    elapsed_ms = None
    if start_text:
        elapsed_ms = round(
            (datetime.now(UTC) - datetime.fromisoformat(start_text)).total_seconds() * 1000,
            3,
        )
    node_metrics.update(
        {
            "node_executions_total": counts,
            "node_duration_ms": durations,
            "resume_count": node_metrics.get("resume_count", 0) + int(outcome == "resumed"),
        }
    )
    if elapsed_ms is not None:
        node_metrics["flow_duration_ms"] = elapsed_ms
    if metrics:
        node_metrics.update(metrics)
    event = {"node_id": node_id, "outcome": outcome, "duration_ms": duration_ms}
    result: dict[str, Any] = {
        "metrics": node_metrics,
        "lifecycle_events": [*state.get("lifecycle_events", []), event],
    }
    if ticket_run is not None:
        result["ticket_run"] = ticket_run.model_dump(mode="json")
    result.update(state_updates)
    attempts = dict(state.get("node_attempts", {}))
    attempt = attempts.get(node_id, 0) + 1
    attempts[node_id] = attempt
    result["node_attempts"] = attempts
    if metrics_store is not None:
        persisted_metrics = dict(metrics or {})
        if (
            elapsed_ms is not None
            and node_id in {"simulated_send", "apply_human_action"}
            and persisted_metrics.get("business_status") in {"sent_open", "sent_closed", "closed_manual"}
        ):
            persisted_metrics["flow_duration_ms"] = elapsed_ms
        metrics_store.record_node(
            event_id=f"{state['flow_id']}:{node_id}:{attempt}",
            flow_id=state["flow_id"],
            node_id=node_id,
            outcome=outcome,
            duration_ms=duration_ms,
            # Aggregate only measurements emitted by this node; the in-memory
            # snapshot includes values from earlier nodes and must not be replayed.
            metrics=persisted_metrics,
        )
    return result


def build_ticket_graph(
    deps: FlowDeps,
    *,
    checkpointer: Any | None = None,
) -> Any:
    """Build a resumable graph; pass a durable checkpointer outside local demos."""

    config = deps.flow_config or load_config()
    checkpoint_store = checkpointer if checkpointer is not None else InMemorySaver()
    metrics_store = (
        MetricsStore((Path(__file__).resolve().parent.parent / config.metrics_db_path).resolve())
        if config.metrics_enabled
        else None
    )

    def apply_pipeline_step(state: FlowState, node_id: str, operation: Callable[..., PipelineWork], *args: Any) -> dict[str, Any]:
        started = monotonic()
        try:
            work = PipelineWork.model_validate(state["pipeline_work"])
            updated = operation(work, *args)
        except Exception:
            _record_node(
                state,
                node_id,
                started,
                "failed",
                metrics={"safe_error_code": f"{node_id.upper()}_FAILED"},
                metrics_store=metrics_store,
            )
            raise
        node_metrics: dict[str, Any] = {}
        if node_id == "qualifier" and updated.qualifier and updated.qualifier.model_version != "not_run":
            node_metrics["qualifier_latency_ms"] = round(updated.qualifier.latency_seconds * 1000, 3)
        elif node_id == "evidence_gate" and updated.evidence_decision:
            node_metrics["evidence_mode"] = updated.evidence_decision.mode
        elif node_id == "policy_check" and updated.policy_check:
            node_metrics["policy_outcome"] = updated.policy_check.status
        elif node_id == "drafter" and updated.draft:
            node_metrics["drafter_latency_ms"] = round(updated.draft.latency_seconds * 1000, 3)
            node_metrics["drafter_cost_usd"] = round(updated.draft.cost_usd, 8)
        return _record_node(
            state,
            node_id,
            started,
            "succeeded",
            metrics=node_metrics,
            ticket_run=None,
            metrics_store=metrics_store,
            pipeline_work=updated.model_dump(mode="json"),
        )

    def begin_intake(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        try:
            ticket = Ticket.model_validate(state["ticket"])
            previous = TicketRun.model_validate(state["previous_run"]) if state.get("previous_run") else None
            work = intake_step(ticket, deps, previous)
        except Exception:
            _record_node(state, "intake", started, "failed", metrics_store=metrics_store)
            raise
        return _record_node(
            state, "intake", started, "succeeded", metrics_store=metrics_store,
            pipeline_work=work.model_dump(mode="json"),
        )

    def qualifier_node(state: FlowState) -> dict[str, Any]:
        return apply_pipeline_step(state, "qualifier", qualifier_step, deps)

    def step_node(node_id: str, operation: Callable[..., PipelineWork], *args: Any) -> Callable[[FlowState], dict[str, Any]]:
        def invoke(state: FlowState) -> dict[str, Any]:
            return apply_pipeline_step(state, node_id, operation, *args)
        return invoke

    def finalize_pipeline(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        try:
            work = PipelineWork.model_validate(state["pipeline_work"])
            result = finalize_step(work, deps)
        except Exception:
            _record_node(state, "finalize_ticket", started, "failed", metrics_store=metrics_store)
            raise
        metrics = {
            "business_status": result.status,
        }
        return _record_node(
            state, "finalize_ticket", started, "succeeded", metrics=metrics,
            ticket_run=result, metrics_store=metrics_store,
        )

    def route_after_intake(state: FlowState) -> Literal["qualifier", "finalize_ticket"]:
        work = PipelineWork.model_validate(state["pipeline_work"])
        return "finalize_ticket" if work.early_run is not None else "qualifier"

    def route_after_routing(state: FlowState) -> Literal["finalize_ticket", "context_plan"]:
        return "finalize_ticket" if needs_human_routing(PipelineWork.model_validate(state["pipeline_work"])) else "context_plan"

    def route_after_evidence(state: FlowState) -> Literal["finalize_ticket", "drafter"]:
        work = PipelineWork.model_validate(state["pipeline_work"])
        return "finalize_ticket" if work.evidence_decision and work.evidence_decision.mode == "no_draft" else "drafter"

    def route_after_finalize(state: FlowState) -> Literal["prepare_human_wait", "__end__"]:
        if _run(state).status in {"awaiting_validation", "awaiting_reroute", "manual_handling"}:
            return "prepare_human_wait"
        return END

    def prepare_human_wait(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        metrics = dict(state.get("metrics", {}))
        metrics["interrupt_count"] = metrics.get("interrupt_count", 0) + 1
        return _record_node(
            state,
            "human_wait",
            started,
            "waiting_human",
            metrics=metrics,
            metrics_store=metrics_store,
        )

    def allowed_actions(run: TicketRun) -> list[str]:
        draft = next((item for item in reversed(run.drafts) if not item.stale), None)
        if run.status == "awaiting_validation":
            actions = ["write", "approve", "handoff"]
            if draft is not None:
                actions.append("edit")
            return actions
        if run.status == "awaiting_reroute":
            return ["reroute", "write"]
        if run.status == "manual_handling":
            return ["close"]
        return []

    def request_human_action(state: FlowState) -> dict[str, Any]:
        run = _run(state)
        draft = next((item for item in reversed(run.drafts) if not item.stale), None)
        actions = allowed_actions(run)
        command = interrupt(
            {
                "kind": "ticket_review",
                "ticket_id": run.ticket.ticket_id,
                "business_status": run.status,
                "desk": run.desk,
                "reason_codes": list(run.reason_codes),
                "current_draft_version": draft.version if draft else None,
                "available_actions": actions,
                "action_error": state.get("action_error"),
            }
        )
        started = monotonic()
        return {
            **_record_node(
                state,
                "human_review",
                started,
                "resumed",
                metrics_store=metrics_store,
            ),
            "human_command": command,
            "action_error": None,
        }

    def apply_human_action(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        run = _run(state)
        command = state.get("human_command", {})
        action = command.get("action")
        actor = command.get("actor")
        try:
            if action not in allowed_actions(run):
                raise ValueError("action is not allowed from the current state")
            if not isinstance(actor, str) or not actor.strip():
                raise ValueError("human action requires a non-empty actor")

            if action == "approve":
                updated = approve_reply(run, actor=actor)
            elif action == "edit":
                updated = edit_draft(run, command.get("text", ""), actor=actor)
            elif action == "write":
                updated = write_reply(run, command.get("text", ""), actor=actor)
            elif action == "handoff":
                updated = handoff_to_rerouter(
                    run, actor=actor, reason=command.get("reason", "")
                )
            elif action == "reroute":
                updated = reroute(
                    run,
                    cast(Desk, command["desk"]),
                    deps,
                    actor=actor,
                    reason=command.get("reason", ""),
                )
            elif action == "close":
                updated = close_manual(run, actor=actor, reason=command.get("reason", ""))
            else:
                raise ValueError("unsupported human action")
        except (ValueError, KeyError, TypeError):
            return {
                **_record_node(
                    state,
                    "apply_human_action",
                    started,
                    "rejected",
                    metrics_store=metrics_store,
                ),
                "action_error": "ACTION_REJECTED",
            }

        counts = dict(state.get("metrics", {}).get("human_actions_total", {}))
        counts[action] = counts.get(action, 0) + 1
        return _record_node(
            state,
            "apply_human_action",
            started,
            "succeeded",
            metrics={"human_actions_total": counts, "human_action": action, "business_status": updated.status},
            ticket_run=updated,
            metrics_store=metrics_store,
            action_error=None,
        )

    def route_after_human_action(
        state: FlowState,
    ) -> Literal["prepare_human_wait", "prepare_send_wait", "__end__"]:
        if state.get("action_error"):
            return "prepare_human_wait"
        status = _run(state).status
        if status == "ready_to_send":
            return "prepare_send_wait"
        if status in {"sent_open", "sent_closed", "closed_manual"}:
            return END
        return "prepare_human_wait"

    def prepare_send_wait(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        metrics = dict(state.get("metrics", {}))
        metrics["interrupt_count"] = metrics.get("interrupt_count", 0) + 1
        return _record_node(
            state,
            "send_wait",
            started,
            "waiting_human",
            metrics=metrics,
            metrics_store=metrics_store,
        )

    def request_send_confirmation(state: FlowState) -> dict[str, Any]:
        run = _run(state)
        command = interrupt(
            {
                "kind": "simulated_send_confirmation",
                "ticket_id": run.ticket.ticket_id,
                "business_status": run.status,
                "approved_by": run.approved_by,
                "required_disposition": ["leave_open", "close"],
                "disposition_must_be_explicit": True,
                "final_policy_status": run.final_policy_check.status
                if run.final_policy_check
                else "pending_final_gate",
                "requires_explicit_send_action": True,
                "send_error": state.get("send_error"),
            }
        )
        started = monotonic()
        return {
            **_record_node(
                state,
                "send_confirmation",
                started,
                "resumed",
                metrics_store=metrics_store,
            ),
            "human_command": command,
            "send_error": None,
        }

    def perform_simulated_send(state: FlowState) -> dict[str, Any]:
        started = monotonic()
        run = _run(state)
        command = state.get("human_command", {})
        try:
            if command.get("action") != "send":
                raise ValueError("an explicit send action is required")
            updated = send_simulated(
                run,
                actor=command.get("actor", ""),
                idempotency_key=command.get("idempotency_key", ""),
                disposition=command.get("disposition", ""),
                override_reason=command.get("override_reason"),
            )
        except (ValueError, KeyError, TypeError):
            return {
                **_record_node(
                    state,
                    "simulated_send",
                    started,
                    "rejected",
                    metrics_store=metrics_store,
                ),
                "send_error": "SEND_ACTION_REJECTED",
            }
        old = state.get("metrics", {})
        send_counts = dict(old.get("simulated_send_total", {}))
        gate = updated.final_policy_check.status if updated.final_policy_check else "not_run"
        send_outcome = (
            "sent"
            if updated.status in {"sent_open", "sent_closed"}
            else "blocked"
            if gate == "blocked"
            else "failed"
        )
        send_counts[send_outcome] = send_counts.get(send_outcome, 0) + 1
        disposition_counts = dict(old.get("send_disposition_total", {}))
        if send_outcome == "sent":
            disposition = updated.send_disposition or "unknown"
            disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
        return _record_node(
            state,
            "simulated_send",
            started,
            send_outcome,
            metrics={
                "simulated_send_total": send_counts,
                "send_disposition_total": disposition_counts,
                "send_disposition": updated.send_disposition,
                "final_gate_outcome": gate,
                "business_status": updated.status,
            },
            ticket_run=updated,
            metrics_store=metrics_store,
            send_error=None,
        )

    def route_after_send(
        state: FlowState,
    ) -> Literal["prepare_human_wait", "prepare_send_wait", "__end__"]:
        if state.get("send_error"):
            return "prepare_send_wait"
        run = _run(state)
        if run.status == "awaiting_validation":
            return "prepare_human_wait"
        return END

    builder = StateGraph(FlowState)
    builder.add_node("intake", begin_intake)
    builder.add_node("qualifier", qualifier_node)
    builder.add_node("field_check", step_node("field_check", field_check_step))
    builder.add_node("routing", step_node("routing", routing_step, deps))
    builder.add_node("context_plan", step_node("context_plan", context_plan_step, deps))
    builder.add_node("tools", step_node("tools", tools_step, deps))
    builder.add_node("evidence_gate", step_node("evidence_gate", evidence_gate_step))
    builder.add_node("drafter", step_node("drafter", drafter_step, deps))
    builder.add_node("policy_check", step_node("policy_check", policy_check_step))
    builder.add_node("finalize_ticket", finalize_pipeline)
    builder.add_node("prepare_human_wait", prepare_human_wait)
    builder.add_node("human_review", request_human_action)
    builder.add_node("apply_human_action", apply_human_action)
    builder.add_node("send_confirmation", request_send_confirmation)
    builder.add_node("prepare_send_wait", prepare_send_wait)
    builder.add_node("simulated_send", perform_simulated_send)
    builder.add_edge(START, "intake")
    builder.add_conditional_edges(
        "intake",
        route_after_intake,
        path_map={"qualifier": "qualifier", "finalize_ticket": "finalize_ticket"},
    )
    builder.add_edge("qualifier", "field_check")
    builder.add_edge("field_check", "routing")
    builder.add_conditional_edges(
        "routing", route_after_routing,
        path_map={"finalize_ticket": "finalize_ticket", "context_plan": "context_plan"},
    )
    builder.add_edge("context_plan", "tools")
    builder.add_edge("tools", "evidence_gate")
    builder.add_conditional_edges(
        "evidence_gate", route_after_evidence,
        path_map={"finalize_ticket": "finalize_ticket", "drafter": "drafter"},
    )
    builder.add_edge("drafter", "policy_check")
    builder.add_edge("policy_check", "finalize_ticket")
    builder.add_conditional_edges(
        "finalize_ticket", route_after_finalize,
        path_map={"prepare_human_wait": "prepare_human_wait", END: END},
    )
    builder.add_edge("prepare_human_wait", "human_review")
    builder.add_edge("human_review", "apply_human_action")
    builder.add_conditional_edges(
        "apply_human_action",
        route_after_human_action,
        path_map={
            "prepare_human_wait": "prepare_human_wait",
            "prepare_send_wait": "prepare_send_wait",
            END: END,
        },
    )
    builder.add_edge("prepare_send_wait", "send_confirmation")
    builder.add_edge("send_confirmation", "simulated_send")
    builder.add_conditional_edges(
        "simulated_send",
        route_after_send,
        path_map={
            "prepare_human_wait": "prepare_human_wait",
            "prepare_send_wait": "prepare_send_wait",
            END: END,
        },
    )
    return builder.compile(checkpointer=checkpoint_store)


def initial_state(ticket: Ticket, previous_run: TicketRun | None = None) -> FlowState:
    """Create a safe typed graph input without evaluator/oracle fields."""

    return {
        "ticket": ticket.model_dump(mode="json"),
        "previous_run": previous_run.model_dump(mode="json") if previous_run else None,
        "flow_id": str(uuid4()),
        "metrics": {
            "flow_started_at": datetime.now(UTC).isoformat(),
            "node_executions_total": {},
            "node_duration_ms": {},
            "human_actions_total": {},
            "simulated_send_total": {},
            "interrupt_count": 0,
            "resume_count": 0,
        },
        "lifecycle_events": [],
        "node_attempts": {},
    }


def make_ticket_step(deps: FlowDeps) -> Callable[[Ticket, FlowDeps], TicketRun]:
    """Adapt the graph to the existing batch runner; a human pause remains checkpointed."""

    graph = build_ticket_graph(deps)

    def run_one(ticket: Ticket, _deps: FlowDeps) -> TicketRun:
        result = graph.invoke(
            initial_state(ticket),
            config={"configurable": {"thread_id": f"{ticket.ticket_id}:{ticket.turn}"}},
        )
        return TicketRun.model_validate(result["ticket_run"])

    return run_one
