"""Build concise, slide-ready figures from MLflow evaluation runs.

The command reads the configured MLflow tracking store and writes SVG/PNG
exports to docs/figures/. It does not access Vertex AI or GCS directly.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "notebooks"))

import matplotlib.pyplot as plt
import mlflow
import pandas as pd
from mlflow import MlflowClient

import _viz as viz
from src.tracking import EXPERIMENT_NAME, TRACKING_URI, log_record, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def load_runs() -> list[dict]:
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient(tracking_uri=TRACKING_URI)
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise RuntimeError(f"MLflow experiment not found: {EXPERIMENT_NAME}")
    runs = client.search_runs([experiment.experiment_id], max_results=1000)
    records = []
    for run in runs:
        tags = run.data.tags
        if tags.get("project") != "navy-qualifier" or not tags.get("system_id"):
            continue
        records.append(
            {
                "run_id": run.info.run_id,
                "system_id": tags["system_id"],
                "split": tags.get("split", "unknown"),
                "run_type": tags.get("run_type", "unknown"),
                "selection_status": tags.get("selection_status", "unknown"),
                **run.data.metrics,
            }
        )
    return records


def _runs_for(records: list[dict], split: str) -> list[dict]:
    rows = [r for r in records if r.get("split") == split and r.get("run_type") == "evaluation"]
    latest: dict[str, dict] = {}
    for row in rows:
        latest.setdefault(row["system_id"], row)
    return list(latest.values())


def _export(fig, name: str, source_runs: list[dict], *, dry_run: bool) -> list[str]:
    paths = viz.save(fig, name)
    plt.close(fig)
    path_strings = [str(path) for path in paths]
    if not dry_run:
        run_id, created = log_record(
            run_name=f"qualifier-figure-{name}",
            run_type="figure_export",
            tracking_key=(
                f"figure:{name}:{','.join(sorted(r['run_id'] for r in source_runs))}:"
                f"{','.join(sha256_file(Path(p)) for p in path_strings)}"
            ),
            tags={
                "project": "navy-qualifier",
                "system_id": "aggregate",
                "stage": "final",
                "split": "multi",
                "tracking_origin": "local",
                "selection_status": "reference",
                "source_run_ids": ",".join(sorted(r["run_id"] for r in source_runs)),
            },
            params={"figure_name": name},
            artifacts=[{"path": p, "artifact_path": "figures"} for p in path_strings],
        )
        print(f"Logged {name} to MLflow {run_id} ({'new' if created else 'already logged'})")
    return path_strings


def _tradeoff(records: list[dict], *, dry_run: bool) -> list[str] | None:
    rows = [r for r in _runs_for(records, "test_natural") if r.get("estimated_monthly_inference_cost_eur") is not None and r.get("silent_error_rate") is not None]
    if not rows:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for row in rows:
        system = row["system_id"]
        cost = row["estimated_monthly_inference_cost_eur"]
        errors = row["silent_error_rate"] * 100
        ax.scatter(cost, errors, s=110, color=viz.SYSTEM_COLORS.get(system, viz.NEUTRAL), edgecolor="white", linewidth=1.2, zorder=3)
        ax.annotate(system, (cost, errors), xytext=(7, 6), textcoords="offset points", fontsize=9, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlabel("Estimated inference cost per month (€; log scale)")
    ax.set_ylabel("Silent errors per 100 tickets")
    ax.grid(axis="x", visible=False)
    viz.headline(fig, "Quality vs monthly serving cost", "test_natural • lower-left is better • cost assumptions are logged per run")
    return _export(fig, "06_quality_cost_front", rows, dry_run=dry_run)


def _risk_comparison(records: list[dict], *, dry_run: bool) -> list[str] | None:
    rows = _runs_for(records, "test_natural")
    rows = [r for r in rows if r.get("silent_error_rate") is not None and r.get("urgent_wrong_desk_rate") is not None]
    if not rows:
        return None
    rows.sort(key=lambda r: r["silent_error_rate"])
    labels = [r["system_id"] for r in rows]
    colors = [viz.SYSTEM_COLORS.get(name, viz.NEUTRAL) for name in labels]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    for ax, metric, title in (
        (axes[0], "silent_error_rate", "Silent errors / 100"),
        (axes[1], "urgent_wrong_desk_rate", "Urgent tickets sent to wrong desk (%)"),
    ):
        values = [r[metric] * (100 if metric == "urgent_wrong_desk_rate" else 100) for r in rows]
        y = range(len(labels))
        ax.barh(y, values, color=colors, height=0.64)
        ax.set_yticks(list(y), labels)
        ax.invert_yaxis()
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=viz.INK)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("% of tickets" if metric == "urgent_wrong_desk_rate" else "Tickets per 100")
        for yi, value in enumerate(values):
            ax.text(value + max(values + [1]) * .025, yi, f"{value:.1f}", va="center", fontsize=9, color=viz.INK)
        ax.set_xlim(0, max(values + [1]) * 1.24)
    viz.headline(fig, "Two risks to compare", "test_natural • lower is better • urgent denominator: high-priority tickets only")
    return _export(fig, "07_silent_urgent_risk", rows, dry_run=dry_run)


def _validation_base_vs_finetuned(records: list[dict], *, dry_run: bool) -> list[str] | None:
    """Compare the same-size prompted base (B3) and tuned model (D) on val."""
    by_system = {row["system_id"]: row for row in _runs_for(records, "val")}
    systems = [name for name in ("B2", "B3", "D") if name in by_system]
    rows = [by_system[name] for name in systems]
    if len(rows) < 2 or any(
        row.get("silent_error_rate") is None or row.get("urgent_wrong_desk_rate") is None
        for row in rows
    ):
        return None
    colors = [viz.SYSTEM_COLORS.get(name, viz.NEUTRAL) for name in systems]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.3))
    for ax, metric, title, scale, xlabel in (
        (axes[0], "silent_error_rate", "Silent errors / 100", 100, "Tickets per 100"),
        (axes[1], "urgent_wrong_desk_rate", "Urgent tickets to wrong desk", 100, "% of urgent tickets"),
    ):
        values = [by_system[name][metric] * scale for name in systems]
        positions = list(range(len(systems)))
        ax.barh(positions, values, color=colors, height=0.62)
        ax.set_yticks(positions, systems)
        ax.invert_yaxis()
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=viz.INK)
        ax.set_xlabel(xlabel)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, max(values + [1]) * 1.3)
        for y, value in zip(positions, values):
            ax.text(value + max(values + [1]) * .025, y, f"{value:.1f}", va="center", fontsize=9, color=viz.INK)
    counts = sorted({int(row.get("evaluation_n", 0)) for row in rows})
    count_label = ", ".join(map(str, counts))
    viz.headline(fig, "Prompted base vs fine-tuned model", f"validation only • B3 and D share Qwen2.5-3B • n={count_label}")
    return _export(fig, "11_val_base_vs_finetuned", rows, dry_run=dry_run)


def _efficiency(records: list[dict], *, dry_run: bool) -> list[str] | None:
    rows = [r for r in _runs_for(records, "test_natural") if r.get("latency_mean_seconds") is not None and r.get("silent_error_rate") is not None]
    if not rows:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for row in rows:
        system = row["system_id"]
        x = row["latency_mean_seconds"]
        y = row["silent_error_rate"] * 100
        ax.scatter(x, y, s=110, color=viz.SYSTEM_COLORS.get(system, viz.NEUTRAL), edgecolor="white", linewidth=1.2, zorder=3)
        ax.annotate(system, (x, y), xytext=(7, 6), textcoords="offset points", fontsize=9, fontweight="bold")
    ax.set_xlabel("Mean generation latency (seconds per ticket)")
    ax.set_ylabel("Silent errors per 100 tickets")
    ax.grid(axis="x", visible=False)
    viz.headline(fig, "Quality vs ticket latency", "test_natural • bubble area is not encoded; compare position only")
    return _export(fig, "08_quality_latency", rows, dry_run=dry_run)


def _trap_diagnostic(records: list[dict], *, dry_run: bool) -> list[str] | None:
    rows = _runs_for(records, "test_traps")
    by_system = {r["system_id"]: r for r in rows}
    if not by_system:
        return None
    preferred = [name for name in ("B2", "D", "D-q4", "B3") if name in by_system]
    if len(preferred) < 2:
        return None
    selected = [by_system[name] for name in preferred]
    trap_keys = sorted(
        {
            key.split(".")[1]
            for row in selected
            for key in row
            if key.startswith("trap.") and key.endswith(".severity_score")
        }
    )
    if not trap_keys:
        return None
    # Sort by B2 severity when present; show the ten most costly families.
    trap_keys.sort(key=lambda t: by_system.get("B2", {}).get(f"trap.{t}.severity_score", 0), reverse=True)
    trap_keys = trap_keys[:10]
    fig, ax = plt.subplots(figsize=(9.5, max(5.0, len(trap_keys) * .42)))
    width = .78 / len(selected)
    positions = list(range(len(trap_keys)))
    for idx, row in enumerate(selected):
        values = [row.get(f"trap.{trap}.severity_score", 0) for trap in trap_keys]
        offsets = [p - .39 + width / 2 + idx * width for p in positions]
        ax.barh(offsets, values, height=width * .9, label=row["system_id"], color=viz.SYSTEM_COLORS.get(row["system_id"], viz.NEUTRAL))
    ax.set_yticks(positions, [t.replace("_", " ") for t in trap_keys])
    ax.invert_yaxis()
    ax.set_xlabel("Mean severity points (lower is better)")
    ax.legend(title="System", ncol=min(4, len(selected)), loc="lower right")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    viz.headline(fig, "Where trap tickets still fail", "test_traps • diagnostic only • small-family counts remain in run metrics")
    return _export(fig, "09_trap_family_severity", selected, dry_run=dry_run)


def _training_curve(records: list[dict], *, dry_run: bool) -> list[str] | None:
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient(tracking_uri=TRACKING_URI)
    candidates = [r for r in _runs_for(records, "val") if r["system_id"] == "D"]
    if not candidates:
        return None
    run = candidates[0]
    try:
        history_path = Path(client.download_artifacts(run["run_id"], "training/d_qwen2.5-3b_full_run_log_history.json"))
    except Exception:
        try:
            history_path = Path(client.download_artifacts(run["run_id"], "training/log_history.json"))
        except Exception:
            return None
    history = json.loads(history_path.read_text(encoding="utf-8"))
    train = [(item.get("step"), item.get("loss")) for item in history if item.get("step") is not None and item.get("loss") is not None]
    val = [(item.get("step"), item.get("eval_loss")) for item in history if item.get("step") is not None and item.get("eval_loss") is not None]
    if not train and not val:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    if train:
        ax.plot([x for x, _ in train], [y for _, y in train], color=viz.NEUTRAL, linewidth=1.2, label="Train loss")
    if val:
        ax.plot([x for x, _ in val], [y for _, y in val], color=viz.ACCENT, marker="o", markersize=3.5, linewidth=1.8, label="Validation loss")
    ax.set_xlabel("Optimizer step")
    ax.set_ylabel("Loss")
    ax.legend()
    ax.grid(axis="x", visible=False)
    viz.headline(fig, "Training loss over time", "Lower loss is not the final model-selection metric")
    return _export(fig, "10_training_loss", [run], dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="write figures without logging figure runs to MLflow")
    args = parser.parse_args()
    viz.setup()
    records = load_runs()
    exports = {}
    for name, builder in (
        ("validation_base_vs_finetuned", _validation_base_vs_finetuned),
        ("quality_cost", _tradeoff),
        ("silent_urgent", _risk_comparison),
        ("quality_latency", _efficiency),
        ("trap_diagnostic", _trap_diagnostic),
        ("training_loss", _training_curve),
    ):
        exports[name] = builder(records, dry_run=args.dry_run)
    print(json.dumps(exports, indent=2))


if __name__ == "__main__":
    main()
