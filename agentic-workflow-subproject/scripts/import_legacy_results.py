"""Import locally available historical prediction results into MLflow.

No Vertex/GCS API is used. B3 is included only when a local prediction export
exists and matches the frozen dataset split exactly.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scoring import load_split, score
from src.router_evaluation import evaluate_router
from src.tracking import (
    build_dataset_manifest,
    log_evaluation,
)

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "data" / "dataset"
RESULTS_DIR = ROOT / "docs" / "results"

# Each path is a prediction export already present in the repository/worktree.
# Missing files are reported and skipped; there is no remote download fallback.
LEGACY_RESULTS = [
    ("B0", "test_natural", RESULTS_DIR / "b0_test_natural_predictions.csv"),
    ("B0", "test_traps", RESULTS_DIR / "b0_test_traps_predictions.csv"),
    ("B1", "test_natural", RESULTS_DIR / "b1_test_natural_predictions.csv"),
    ("B1", "test_traps", RESULTS_DIR / "b1_test_traps_predictions.csv"),
    ("B2", "test_natural", RESULTS_DIR / "b2_test_natural_predictions.csv"),
    ("B2", "test_traps", RESULTS_DIR / "b2_test_traps_predictions.csv"),
    ("D", "val", RESULTS_DIR / "d_qwen2.5-3b_full_run_val_predictions.csv"),
    ("D-q8", "val", RESULTS_DIR / "d_q8_full_run_val_predictions.csv"),
    ("D-q4", "val", RESULTS_DIR / "d_q4_full_run_val_predictions.csv"),
    ("D", "test_natural", RESULTS_DIR / "d_gpu_test_natural_predictions.csv"),
    ("D", "test_traps", RESULTS_DIR / "d_gpu_test_traps_predictions.csv"),
    ("D-q8", "test_natural", RESULTS_DIR / "d_q8_test_natural_predictions.csv"),
    ("D-q8", "test_traps", RESULTS_DIR / "d_q8_test_traps_predictions.csv"),
    ("D-q4", "test_natural", RESULTS_DIR / "d_q4_test_natural_predictions.csv"),
    ("D-q4", "test_traps", RESULTS_DIR / "d_q4_test_traps_predictions.csv"),
    ("B3", "val", ROOT / "data" / "runs" / "base_val_predictions.csv"),
    ("B3", "test_natural", ROOT / "data" / "runs" / "base_test_natural_predictions.csv"),
    ("B3", "test_traps", ROOT / "data" / "runs" / "base_test_traps_predictions.csv"),
]

TIMINGS = {
    "val": RESULTS_DIR / "d_compact_full_run_timings.json",
    "test_natural": RESULTS_DIR / "d_compact_test_natural_timings.json",
    "test_traps": RESULTS_DIR / "d_compact_test_traps_timings.json",
}


def _source_metrics(
    source: Path, split: str
) -> tuple[dict[str, float], dict[str, float], dict[str, Any]]:
    tickets, truths, trap_tags = load_split(DATASET_DIR / f"{split}.csv")
    predictions = pd.read_csv(source, keep_default_na=False)
    if "user_input" not in predictions or "extracted_response" not in predictions:
        raise ValueError(f"{source} is missing required prediction columns")
    found_tickets = list(predictions["user_input"])
    if len(found_tickets) != len(set(found_tickets)):
        raise ValueError(f"{source} contains duplicate input tickets")
    if found_tickets != tickets:
        raise ValueError(
            f"{source} does not match all {split} rows in the same order; "
            "refusing to score or import it"
        )
    raw_outputs = list(predictions["extracted_response"])
    metrics = score(truths, raw_outputs)
    router = evaluate_router(truths, raw_outputs)
    router_metrics = {f"router.{key}": value for key, value in router["counts"].items()}
    router_metrics.update({f"router.{key}": value for key, value in router["rates"].items() if value is not None})
    return metrics, router_metrics, {"evaluation_n": len(tickets), "dataset_sha256": None,
                                  "router_matrix": router["action_matrix"]}


def _legacy_params(system_id: str) -> dict[str, Any]:
    if system_id == "B2":
        return {"regularization_C": 10.0, "model_family": "tfidf_logistic_regression"}
    if system_id in {"D", "D-q8", "D-q4", "B3"}:
        return {"base_model": "Qwen/Qwen2.5-3B-Instruct"}
    return {}


def _timing_metadata(
    system_id: str, split: str
) -> tuple[dict[str, float], dict[str, Any], list[dict[str, str]], dict[str, Any]]:
    if system_id == "D" and split == "test_natural":
        monthly = 255.0
        return (
            {
                "estimated_monthly_inference_cost_eur": monthly,
                "inference_cost_per_1000_eur": monthly / 36.0,
            },
            {"inference_cost_model": "always_on_T4_endpoint"},
            [],
            {
                "estimated_monthly_inference_cost_eur": {
                    "status": "estimated",
                    "source": "docs/compact_variants.md; T4 endpoint running 24/7 scenario",
                },
                "inference_cost_per_1000_eur": {
                    "status": "estimated",
                    "source": "docs/compact_variants.md; €255/month divided by 36,000 tickets",
                },
            },
        )
    if system_id not in {"D-q8", "D-q4"} or not TIMINGS[split].is_file():
        return {}, {}, [], {}
    timing_path = TIMINGS[split]
    report = json.loads(timing_path.read_text(encoding="utf-8"))
    key = "q8" if system_id == "D-q8" else "q4"
    values = report.get(key, {})
    if not values:
        return {}, {}, [], {}
    mean = float(values["seconds_mean"])
    metrics = {
        "latency_mean_seconds": mean,
        "latency_median_seconds": float(values["seconds_median"]),
        "latency_p95_seconds": float(values["seconds_p95"]),
        "model_size_mb": float(values["gguf_mb"]),
        # Estimate from the published scenario assumptions, not a billing export.
        "estimated_monthly_inference_cost_eur": mean * 36_000 * 0.00008,
        "inference_cost_per_1000_eur": mean * 1000 * 0.00008,
    }
    params = {
        "inference_machine": report.get("cpu_model", report.get("machine", "unknown")),
        "inference_cpu_count": report.get("cpu_count", "unknown"),
        "timed_tickets": report.get("tickets", "unknown"),
    }
    evidence = {
        "latency_mean_seconds": {"status": "measured", "source": str(timing_path)},
        "latency_median_seconds": {"status": "measured", "source": str(timing_path)},
        "latency_p95_seconds": {"status": "measured", "source": str(timing_path)},
        "model_size_mb": {"status": "measured", "source": str(timing_path)},
        "estimated_monthly_inference_cost_eur": {
            "status": "estimated",
            "source": "scoring_protocol.md section 6; 36,000 tickets/month × €0.00008 per CPU-second",
        },
        "inference_cost_per_1000_eur": {
            "status": "estimated",
            "source": "scoring_protocol.md section 6; €0.00008 per CPU-second",
        },
    }
    artifacts = [{"path": str(timing_path), "artifact_path": "timings"}]
    return metrics, params, artifacts, evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate inputs and print intended imports without MLflow")
    parser.add_argument("--include-b3", action="store_true", help="include a local B3 export if it passes exact split checks")
    parser.add_argument("--system-id", action="append", choices=sorted({item[0] for item in LEGACY_RESULTS}), help="limit work to this system (repeatable)")
    parser.add_argument("--split", action="append", choices=sorted({item[1] for item in LEGACY_RESULTS}), help="limit work to this split (repeatable)")
    args = parser.parse_args()

    manifest = build_dataset_manifest(DATASET_DIR)
    manifest_path = ROOT / "docs" / "results" / "dataset_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    completed = []
    for system_id, split, source in LEGACY_RESULTS:
        if args.system_id and system_id not in args.system_id:
            continue
        if args.split and split not in args.split:
            continue
        if system_id == "B3" and not args.include_b3:
            continue
        if not source.is_file():
            print(f"SKIP missing local source: {source.relative_to(ROOT)}")
            continue
        try:
            metrics, router_metrics, context = _source_metrics(source, split)
        except (KeyError, ValueError) as exc:
            print(f"INVALID {source.relative_to(ROOT)}: {exc}")
            continue

        extra_metrics: dict[str, float] = {**router_metrics}
        extra_params: dict[str, Any] = _legacy_params(system_id)
        extra_artifacts: list[dict[str, str]] = []
        metric_history: dict[str, list[tuple[int, float]]] = {}
        evidence: dict[str, Any] = {
            key: {"status": "measured", "source": str(source.relative_to(ROOT))}
            for key in metrics
        }
        if system_id in {"D", "D-q8", "D-q4"}:
            timed_metrics, timing_params, timing_artifacts, timing_evidence = _timing_metadata(system_id, split)
            extra_metrics.update(timed_metrics)
            extra_params.update(timing_params)
            extra_artifacts.extend(timing_artifacts)
            evidence.update(timing_evidence)
        if system_id == "D" and split == "val":
            loss_path = RESULTS_DIR / "d_qwen2.5-3b_full_run_log_history.json"
            if loss_path.is_file():
                extra_artifacts.append({"path": str(loss_path), "artifact_path": "training"})
                for row in json.loads(loss_path.read_text(encoding="utf-8")):
                    for source_key, metric_name in (("loss", "train_loss"), ("eval_loss", "eval_loss")):
                        if source_key in row and "step" in row:
                            metric_history.setdefault(metric_name, []).append((int(row["step"]), float(row[source_key])))

        selection_status = (
            "champion" if system_id == "D-q4" and split == "test_natural"
            else "reference" if system_id.startswith("B")
            else "candidate"
        )
        if args.dry_run:
            completed.append({"system_id": system_id, "split": split, "source": str(source.relative_to(ROOT)), "n": context["evaluation_n"]})
            continue
        matrix_dir = ROOT / "logs" / "mlflow" / "router_matrices"
        matrix_dir.mkdir(parents=True, exist_ok=True)
        matrix_path = matrix_dir / f"{system_id}-{split}-action-matrix.json"
        matrix_path.write_text(json.dumps(context["router_matrix"], indent=2) + "\n", encoding="utf-8")
        extra_artifacts.append({"path": str(matrix_path), "artifact_path": "router_evaluation"})
        run_id, created = log_evaluation(
            system_id=system_id,
            split=split,
            metrics=metrics,
            dataset_path=DATASET_DIR / f"{split}.csv",
            source_path=source,
            params=extra_params,
            stage="selection" if split == "val" else "final",
            tracking_origin="historical_import",
            model_id=_legacy_params(system_id).get("base_model", "unknown"),
            selection_status=selection_status,
            extra_metrics=extra_metrics,
            metric_history=metric_history,
            extra_artifacts=extra_artifacts,
            metric_evidence=evidence,
        )
        completed.append({"run_id": run_id, "created": created, "system_id": system_id, "split": split})

    print(json.dumps({"dry_run": args.dry_run, "dataset_manifest": str(manifest_path.relative_to(ROOT)), "results": completed}, indent=2))


if __name__ == "__main__":
    main()
