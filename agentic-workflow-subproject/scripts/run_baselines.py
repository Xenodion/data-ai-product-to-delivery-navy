"""Fit B0-B2 on train, tune B2's C on val, print the val table. ``--final`` also scores the two test sets.

Run: uv run --with scikit-learn python scripts/run_baselines.py [--final] [--save]
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.baselines import fit_tfidf, predict_majority, predict_rules, predict_tfidf
from src.scoring import by_trap, load_split, paired_bootstrap, score, severities
from src.tracking import log_evaluation, metric_summary_for_traps

DATASET = Path("data/dataset")
SHOWN = (
    "n",
    "valid_json_rate",
    "desk_accuracy",
    "urgent_wrong_desk",
    "silent_error_rate",
    "auto_routed_rate",
    "needless_triage_rate",
    "macro_f1_intent",
    "exact_transaction_id",
    "exact_amount",
    "accuracy_urgency",
    "recall_high_urgency",
    "severity_score",
)
C_GRID = (0.3, 1.0, 3.0, 10.0)


def show(name: str, result: dict[str, float]) -> None:
    print(f"{name:4}", " ".join(f"{k}={result[k]:.3f}" for k in SHOWN))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--final", action="store_true", help="also score test_natural and test_traps"
    )
    parser.add_argument(
        "--save", action="store_true", help="save predictions CSVs into docs/results/"
    )
    parser.add_argument(
        "--mlflow", action="store_true", help="track scoring runs in the local/configured MLflow server"
    )
    args = parser.parse_args()
    train_x, train_y, _ = load_split(DATASET / "train.csv")
    val_x, val_y, _ = load_split(DATASET / "val.csv")
    best_c = min(
        C_GRID,
        key=lambda c: score(
            val_y, predict_tfidf(fit_tfidf(train_x, train_y, c), val_x)
        )["severity_score"],
    )
    models = fit_tfidf(train_x, train_y, best_c)
    systems = {
        "B0": lambda x: predict_majority(train_y, x),
        "B1": predict_rules,
        "B2": lambda x: predict_tfidf(models, x),
    }

    def track(split: str, features, labels, trap_tags, predictions) -> None:
        if not args.mlflow:
            return
        out_dir = Path("logs/mlflow/baseline_predictions")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{split}.csv"
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=("user_input", "reference", "extracted_response", "valid_json"),
            )
            writer.writeheader()
            for ticket, label, raw in zip(features, labels, predictions):
                writer.writerow({
                    "user_input": ticket,
                    "reference": label.model_dump_json(),
                    "extracted_response": raw or "",
                    "valid_json": bool(raw),
                })
        result = score(labels, predictions)
        trap_metrics = (
            metric_summary_for_traps(by_trap(labels, predictions, trap_tags))
            if split == "test_traps"
            else {}
        )
        run_id, created = log_evaluation(
            system_id=current_system[0],
            split=split,
            metrics=result,
            dataset_path=DATASET / f"{split}.csv",
            source_path=out_path,
            params=({"regularization_C": best_c} if current_system[0] == "B2" else {}),
            stage="selection" if split == "val" else "final",
            tracking_origin="local",
            extra_metrics=trap_metrics,
            metric_evidence={
                name: {"status": "measured", "source": "src/scoring.py"}
                for name in result
            },
        )
        print(f"MLflow {current_system[0]} {split}: {run_id} ({'created' if created else 'already tracked'})")

    print(f"val ({len(val_y)} tickets), B2 C={best_c}")
    for current_system in systems.items():
        name, predict = current_system
        raw_predictions = predict(val_x)
        show(name, score(val_y, raw_predictions))
        track("val", val_x, val_y, load_split(DATASET / "val.csv")[2], raw_predictions)
    if not args.final:
        return
    test_x, test_y, _ = load_split(DATASET / "test_natural.csv")
    preds = {name: predict(test_x) for name, predict in systems.items()}
    print(f"test_natural ({len(test_y)} tickets)")
    for name, raws in preds.items():
        show(name, score(test_y, raws))
        current_system = (name, systems[name])
        track("test_natural", test_x, test_y, [], raws)
    best = min(("B1", "B2"), key=lambda n: score(test_y, preds[n])["severity_score"])
    for name in ("B0", "B1", "B2"):
        if name != best:
            mean, low, high = paired_bootstrap(
                severities(test_y, preds[name]), severities(test_y, preds[best])
            )
            print(f"severity {name} - {best}: {mean:.3f} [{low:.3f}, {high:.3f}]")
    trap_x, trap_y, trap_tags = load_split(DATASET / "test_traps.csv")
    trap_preds = {}
    for name, predict in systems.items():
        print(f"test_traps {name}: (tickets, desk accuracy, severity) per trap")
        trap_raws = predict(trap_x)
        trap_preds[name] = trap_raws
        current_system = (name, predict)
        track("test_traps", trap_x, trap_y, trap_tags, trap_raws)
        for trap, row in by_trap(trap_y, trap_raws, trap_tags).items():
            print(f"  {trap:28} n={row[0]:3} desk={row[1]:.2f} severity={row[2]:.2f}")

    if args.save:
        out_dir = Path("docs/results")
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, raws in preds.items():
            rows = [
                {
                    "user_input": x,
                    "reference": y.model_dump_json(),
                    "extracted_response": r,
                    "valid_json": True,
                }
                for x, y, r in zip(test_x, test_y, raws)
            ]
            p = out_dir / f"{name.lower()}_test_natural_predictions.csv"
            pd.DataFrame(rows).to_csv(p, index=False)
            print(f"Saved {name} test_natural predictions to {p}")
        for name, raws in trap_preds.items():
            rows = [
                {
                    "user_input": x,
                    "reference": y.model_dump_json(),
                    "extracted_response": r,
                    "valid_json": True,
                }
                for x, y, r in zip(trap_x, trap_y, raws)
            ]
            p = out_dir / f"{name.lower()}_test_traps_predictions.csv"
            pd.DataFrame(rows).to_csv(p, index=False)
            print(f"Saved {name} test_traps predictions to {p}")


if __name__ == "__main__":
    main()
