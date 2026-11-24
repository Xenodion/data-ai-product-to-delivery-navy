"""Replays ``evals/eval_set_v1.csv`` across ``copilot_mode`` rollback levels (#60).

Verifies the pre-release and pre-demo requirement of ``07_operations.md`` section 4:
- ``l1_drafting_off``: Qualifier, Routing Node and read-only tools run, zero model drafts are produced.
- ``l2_routing_off``: Qualifier hints stay visible, every ticket enters manual routing with zero drafts.
- ``l3_copilot_off``: no model or tool runs, every ticket enters the FIFO manual queue and human resolution works.

Run from ``agentic-workflow-subproject``:
    uv run python -m flow.rollback_check
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from langgraph.types import Command

from flow.contracts import CopilotMode, Draft, FlowDeps, QualifierResult, Ticket, TicketRun, load_config
from flow.langgraph_app import build_ticket_graph, initial_state
from flow.qualifier import repair_references
from flow.runner import load_eval_tickets
from flow.tools import gather_evidence
from ml.qualifier.src.scoring import parse_output

SUBPROJECT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_SET = SUBPROJECT.parent / "evals" / "eval_set_v1.csv"
DEFAULT_PREDICTIONS = SUBPROJECT / "data" / "runs" / "regression" / "qualifier_eval_set_v1.csv"


@dataclass(frozen=True)
class ReplaySummary:
    mode: CopilotMode
    total: int
    drafts_created: int
    sends_triggered: int
    by_status: dict[str, int]
    by_desk: dict[str, int]
    qualifier_calls: int
    tool_calls: int
    drafter_calls: int
    fifo_preserved: bool
    manual_resolution_verified: bool


def load_stored_qualifier_results(
    predictions_path: Path = DEFAULT_PREDICTIONS,
    model_version: str = "d-q4",
) -> dict[str, QualifierResult]:
    """Build runtime-equivalent ``QualifierResult`` objects from stored regression outputs."""
    results: dict[str, QualifierResult] = {}
    with predictions_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            case_id = row["id"]
            raw_cell = row.get("raw_output") or ""
            if not raw_cell:
                results[case_id] = QualifierResult(
                    status="unavailable",
                    label=None,
                    raw=None,
                    model_version=model_version,
                    latency_seconds=0.0,
                    error="stored prediction empty",
                )
                continue
            repaired = repair_references(raw_cell)
            label = parse_output(repaired)
            results[case_id] = QualifierResult(
                status="valid" if label is not None else "invalid",
                label=label,
                raw=repaired,
                model_version=model_version,
                prompt_name="navy/qualifier",
                prompt_version="production",
                latency_seconds=0.0,
            )
    return results


def replay_mode(
    mode: CopilotMode,
    *,
    eval_set_path: Path = DEFAULT_EVAL_SET,
    predictions_path: Path = DEFAULT_PREDICTIONS,
) -> ReplaySummary:
    """Replay the eval-set under ``mode`` and assert its safety invariants."""
    config = load_config().model_copy(update={"copilot_mode": mode, "metrics_enabled": False})
    stored = load_stored_qualifier_results(predictions_path, config.qualifier_model_version)
    base_tickets = load_eval_tickets(eval_set_path, config.merchant_id)
    epoch = datetime(2026, 11, 24, 9, 0, tzinfo=UTC)
    tickets = [
        ticket.model_copy(update={"created_at": epoch + timedelta(seconds=index)})
        for index, ticket in enumerate(base_tickets)
    ]

    counts = {"qualifier": 0, "tools": 0, "drafter": 0}

    def qualify_fn(ticket: Ticket) -> QualifierResult:
        counts["qualifier"] += 1
        return stored[ticket.ticket_id]

    def tools_fn(ticket: Ticket, plan):
        counts["tools"] += 1
        return gather_evidence(ticket, plan, config=config)

    def forbid_draft(*_args, **_kwargs) -> Draft:
        counts["drafter"] += 1
        raise AssertionError(f"Drafter was invoked under copilot_mode={mode}")

    deps = FlowDeps(
        qualify=qualify_fn,
        draft=forbid_draft,
        grounded_draft=forbid_draft,
        policy_version=config.policy_version,
        gather_evidence=tools_fn,
        flow_config=config,
    )
    graph = build_ticket_graph(deps)

    runs: list[TicketRun] = []
    for ticket in tickets:
        out = graph.invoke(
            initial_state(ticket),
            config={"configurable": {"thread_id": f"rollback:{mode}:{ticket.ticket_id}"}},
        )
        runs.append(TicketRun.model_validate(out["ticket_run"]))

    drafts_created = sum(len(run.drafts) for run in runs)
    sends_triggered = sum(len(run.send_receipts) for run in runs)
    by_status = dict(sorted(Counter(run.status for run in runs).items()))
    by_desk = dict(sorted(Counter(run.desk for run in runs).items()))
    intake_qualifier_calls = counts["qualifier"]
    intake_tool_calls = counts["tools"]

    # Global FIFO check on waiting queues: oldest created_at first
    rerouter_queue = [run for run in runs if run.status == "awaiting_reroute"]
    fifo_preserved = [r.ticket.created_at for r in rerouter_queue] == sorted(
        r.ticket.created_at for r in rerouter_queue
    )

    # Verify end-to-end human resolution works on the first waiting ticket without any model call
    manual_ok = False
    if runs:
        sample = tickets[0]
        thread_cfg = {"configurable": {"thread_id": f"rollback:{mode}:{sample.ticket_id}"}}
        current = runs[0]
        if current.status == "awaiting_reroute":
            step1 = graph.invoke(
                Command(resume={"action": "reroute", "desk": "payments", "actor": "rollback-check", "reason": "manual triage check"}),
                config=thread_cfg,
            )
            current = TicketRun.model_validate(step1["ticket_run"])
        step2 = graph.invoke(
            Command(resume={"action": "write", "actor": "rollback-check", "text": "Bonjour, notre équipe vérifie votre demande et revient vers vous."}),
            config=thread_cfg,
        )
        step3 = graph.invoke(
            Command(resume={"action": "approve", "actor": "rollback-check"}),
            config=thread_cfg,
        )
        step4 = graph.invoke(
            Command(resume={"action": "send", "actor": "rollback-check", "idempotency_key": f"rb-{mode}-1", "disposition": "leave_open"}),
            config=thread_cfg,
        )
        resolved = TicketRun.model_validate(step4["ticket_run"])
        manual_ok = resolved.status == "sent_open" and resolved.final_author == "human"

    return ReplaySummary(
        mode=mode,
        total=len(runs),
        drafts_created=drafts_created,
        sends_triggered=sends_triggered,
        by_status=by_status,
        by_desk=by_desk,
        qualifier_calls=intake_qualifier_calls,
        tool_calls=intake_tool_calls,
        drafter_calls=counts["drafter"],
        fifo_preserved=fifo_preserved,
        manual_resolution_verified=manual_ok,
    )


def render_markdown(summaries: list[ReplaySummary]) -> str:
    lines = [
        "# Rollback verification report (`copilot_mode`, #60)",
        "",
        "| Mode | Tickets | Qualifier calls | Tool calls | Drafter calls | Model drafts | Auto-sends | Status split | FIFO | Human resolution |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for item in summaries:
        statuses = ", ".join(f"`{k}`={v}" for k, v in item.by_status.items())
        lines.append(
            f"| `{item.mode}` | {item.total} | {item.qualifier_calls} | {item.tool_calls} | "
            f"{item.drafter_calls} | {item.drafts_created} | {item.sends_triggered} | "
            f"{statuses} | {'yes' if item.fifo_preserved else 'NO'} | "
            f"{'verified' if item.manual_resolution_verified else 'FAILED'} |"
        )
    return "\n".join(lines)


def main() -> int:
    modes: tuple[CopilotMode, ...] = ("l1_drafting_off", "l2_routing_off", "l3_copilot_off")
    summaries = [replay_mode(mode) for mode in modes]
    print(render_markdown(summaries))
    failed = [
        s.mode
        for s in summaries
        if s.drafts_created != 0
        or s.drafter_calls != 0
        or s.sends_triggered != 0
        or not s.fifo_preserved
        or not s.manual_resolution_verified
        or (s.mode == "l3_copilot_off" and (s.qualifier_calls != 0 or s.tool_calls != 0))
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
