"""Score a complete prediction CSV, or explicitly inspect a non-final val prefix.

The predictions file comes from the pipeline (columns user_input, extracted_response); <split> is val, test_natural or test_traps.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.qualifier.scripts.run_baselines import DATASET, SHOWN, show
from research.qualifier.src.scoring import by_trap, load_split, score
from research.qualifier.src.router_evaluation import evaluate_router
from research.qualifier.src.tracking import log_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("split", choices=("val", "test_natural", "test_traps"))
    parser.add_argument("--mlflow", action="store_true", help="log this evaluation to the configured MLflow server")
    parser.add_argument(
        "--allow-partial-diagnostic",
        action="store_true",
        help="score a prefix for diagnosis only; cannot be combined with --mlflow",
    )
    parser.add_argument("--system-id", help="system label, e.g. B3 or D-q4 (required with --mlflow)")
    parser.add_argument("--model-id", default="unknown", help="immutable source model identifier/revision when known")
    parser.add_argument("--tracking-origin", default="local", choices=("local", "vertex", "historical_import"))
    args = parser.parse_args()
    if args.mlflow and not args.system_id:
        parser.error("--system-id is required when --mlflow is set")
    if args.mlflow and args.allow_partial_diagnostic:
        parser.error("partial diagnostic predictions cannot be logged as an evaluation")
    tickets, truths, traps = load_split(DATASET / f"{args.split}.csv")
    preds = pd.read_csv(args.predictions, keep_default_na=False)
    required_columns = {"user_input", "extracted_response"}
    missing = required_columns - set(preds.columns)
    if missing:
        raise ValueError(f"Prediction file is missing required columns: {sorted(missing)}")
    if len(preds) != len(tickets) and not args.allow_partial_diagnostic:
        raise ValueError(
            f"Final scoring requires all {len(tickets)} rows for {args.split}; "
            f"found {len(preds)}. Use --allow-partial-diagnostic only for a non-final local check."
        )
    if len(preds) > len(tickets):
        raise ValueError(f"Prediction file has {len(preds)} rows; {args.split} has only {len(tickets)}")
    if preds.empty:
        raise ValueError("Prediction file is empty")
    if args.allow_partial_diagnostic and args.split != "val":
        raise ValueError("Partial diagnostic scoring is restricted to val; test splits remain sealed")
    # A diagnostic prefix is allowed only for val, and is never logged to MLflow.
    tickets, truths, traps = tickets[: len(preds)], truths[: len(preds)], traps[: len(preds)]
    if list(preds["user_input"]) != tickets:
        raise ValueError(
            f"{args.predictions} does not hold the tickets of {args.split}, in the same order"
        )
    raws = list(preds["extracted_response"])
    print(f"{args.split} ({len(truths)} tickets)")
    metrics = score(truths, raws)
    router = evaluate_router(truths, raws)
    show("pred", metrics)
    print("Router initial decision (offline):", router)
    print(
        "other: "
        + " ".join(
            f"{k}={v:.3f}" for k, v in score(truths, raws).items() if k not in SHOWN
        )
    )
    if args.split == "test_traps":
        for trap, row in by_trap(truths, raws, traps).items():
            print(f"  {trap:28} n={row[0]:3} desk={row[1]:.2f} cost={row[2]:.2f}")
    if args.mlflow:
        extra = {f"router.{key}": value for key, value in router["counts"].items()}
        extra.update({f"router.{key}": value for key, value in router["rates"].items() if value is not None})
        matrix_path = DATASET.parent.parent / "logs" / "mlflow" / "router_matrices" / f"{args.system_id}-{args.split}-action-matrix.json"
        matrix_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_path.write_text(json.dumps(router["action_matrix"], indent=2) + "\n", encoding="utf-8")
        run_id, created = log_evaluation(
            system_id=args.system_id,
            split=args.split,
            metrics=metrics,
            dataset_path=DATASET / f"{args.split}.csv",
            source_path=args.predictions,
            stage="selection" if args.split == "val" else "final",
            tracking_origin=args.tracking_origin,
            model_id=args.model_id,
            extra_metrics=extra,
            extra_artifacts=[{"path": str(matrix_path), "artifact_path": "router_evaluation"}],
        )
        print(f"MLflow {args.system_id} {args.split}: {run_id} ({'created' if created else 'already tracked'})")


if __name__ == "__main__":
    main()
