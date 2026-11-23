"""Latency, cost and quality report from the local metrics store (issue #20).

    uv run python -m flow.metrics_report                      # whole store, Markdown on stdout
    uv run python -m flow.metrics_report --since 2026-11-23 --out .local/reports/metrics.md

Reads `metrics_db_path` of `flow/config.toml` (SQLite written by `flow/metrics_store.py`). Read-only.
It prints aggregates only: no ticket ID, no merchant ID, no text (the store holds none of the text).
The thresholds are layer 0 of `07_operations.md`; they are starting values from synthetic runs.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

QUALIFIER_P95_SLO_S = 18.0      # 07_operations.md layer 0: 1.5 x the 11.8 s measured on CPU
TIMEOUT_SHARE_ACT = 0.05        # 07_operations.md layer 0: timeouts above 5 % of the period
QUALITY_FIELDS = ("qualifier_status", "evidence_mode", "policy_outcome", "final_gate_outcome", "human_action", "business_status")


@dataclass
class Report:
    events: int = 0
    flows: int = 0
    first: str | None = None
    last: str | None = None
    node_durations: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    node_outcomes: dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    qualifier_latency_ms: list[float] = field(default_factory=list)
    drafter_latency_ms: list[float] = field(default_factory=list)
    drafter_cost_usd: list[float] = field(default_factory=list)
    quality: dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))


def percentile(values: list[float], q: float) -> float | None:
    """Nearest-rank percentile; None for an empty sample (never reported as zero)."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), round(q * len(ordered) + 0.5)))
    return ordered[rank - 1]


def load_report(db_path: Path, since: str | None = None) -> Report:
    report = Report()
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        query = "SELECT flow_id, node_id, outcome, occurred_at, duration_ms, safe_metrics_json FROM flow_metric_events"
        params: tuple[str, ...] = ()
        if since:
            query += " WHERE occurred_at >= ?"
            params = (since,)
        flows = set()
        for flow_id, node_id, outcome, occurred_at, duration_ms, metrics_json in connection.execute(query, params):
            report.events += 1
            flows.add(flow_id)
            report.first = min(report.first or occurred_at, occurred_at)
            report.last = max(report.last or occurred_at, occurred_at)
            report.node_durations[node_id].append(float(duration_ms))
            report.node_outcomes[node_id][outcome] += 1
            metrics = json.loads(metrics_json)
            for name in ("qualifier_latency_ms", "drafter_latency_ms", "drafter_cost_usd"):
                if isinstance(metrics.get(name), (int, float)):
                    getattr(report, name).append(float(metrics[name]))
            for name in QUALITY_FIELDS:
                if name in metrics:
                    report.quality[name][str(metrics[name])] += 1
        report.flows = len(flows)
    finally:
        connection.close()
    return report


def _fmt(value: float | None, unit: str = "", digits: int = 0) -> str:
    return "n/a" if value is None else f"{value:,.{digits}f}{unit}"


def alerts(report: Report) -> list[str]:
    out = []
    p95 = percentile(report.qualifier_latency_ms, 0.95)
    if p95 is not None and p95 / 1000 > QUALIFIER_P95_SLO_S:
        out.append(f"Qualifier p95 {p95 / 1000:.1f} s is above the {QUALIFIER_P95_SLO_S:.0f} s objective")
    statuses = report.quality.get("qualifier_status", Counter())  # valid, invalid or unavailable
    total = sum(statuses.values())
    unavailable = statuses.get("unavailable", 0)
    if total and unavailable / total > TIMEOUT_SHARE_ACT:
        out.append(f"Qualifier unavailable on {unavailable / total:.1%} of calls (act above {TIMEOUT_SHARE_ACT:.0%}): copilot to L1 for new tickets")
    return out


def render(report: Report, source: str) -> str:
    lines = [
        "# Copilot metrics report",
        "",
        f"Source: `{source}` · events {report.events} · flows {report.flows} · from {report.first or 'n/a'} to {report.last or 'n/a'}",
        "",
        "## Alerts (07_operations.md, layer 0)",
        "",
    ]
    found = alerts(report)
    lines += [f"- {a}" for a in found] if found else ["- none"]
    q, d = report.qualifier_latency_ms, report.drafter_latency_ms
    costs = report.drafter_cost_usd
    lines += [
        "",
        "## Latency and cost",
        "",
        "| Measure | n | p50 | p95 |",
        "|---|---:|---:|---:|",
        f"| Qualifier latency | {len(q)} | {_fmt(percentile(q, 0.5), ' ms')} | {_fmt(percentile(q, 0.95), ' ms')} |",
        f"| Drafter latency | {len(d)} | {_fmt(percentile(d, 0.5), ' ms')} | {_fmt(percentile(d, 0.95), ' ms')} |",
        "",
        f"Drafter cost: {_fmt(sum(costs) if costs else None, ' USD', 4)} over {len(costs)} drafts"
        f" · {_fmt(sum(costs) / len(costs) if costs else None, ' USD', 5)} per draft"
        f" · {_fmt(sum(costs) / report.flows if costs and report.flows else None, ' USD', 5)} per flow."
        " Qualifier: local CPU, no per-call charge.",
        "",
        "## Nodes",
        "",
        "| Node | runs | p50 | p95 | outcomes |",
        "|---|---:|---:|---:|---|",
    ]
    for node, durations in sorted(report.node_durations.items()):
        outcomes = ", ".join(f"{k} {v}" for k, v in report.node_outcomes[node].most_common())
        lines.append(f"| {node} | {len(durations)} | {_fmt(percentile(durations, 0.5), ' ms')} | {_fmt(percentile(durations, 0.95), ' ms')} | {outcomes} |")
    lines += ["", "## Quality signals", "", "Shares with their denominator; a signal, not a verdict: labelled quality comes from the weekly audit (07_operations.md, layer 2).", ""]
    if not report.quality:
        lines.append("- no quality signal recorded")
    for name in QUALITY_FIELDS:
        counts = report.quality.get(name)
        if counts:
            total = sum(counts.values())
            shares = ", ".join(f"{k} {v}/{total} ({v / total:.0%})" for k, v in counts.most_common())
            lines.append(f"- **{name}**: {shares}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, help="metrics SQLite file (default: metrics_db_path of flow/config.toml)")
    parser.add_argument("--since", help="ISO date or timestamp, UTC (e.g. 2026-11-23)")
    parser.add_argument("--out", type=Path, help="write the Markdown report to this file")
    args = parser.parse_args()
    db = args.db
    if db is None:
        import tomllib

        root = Path(__file__).resolve().parent.parent
        with (root / "flow" / "config.toml").open("rb") as handle:
            db = root / tomllib.load(handle)["metrics_db_path"]
    if not db.exists():
        print(f"No metrics store at {db}: run the flow first (metrics_enabled = true).")
        return 1
    text = render(load_report(db, args.since), db.name)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
