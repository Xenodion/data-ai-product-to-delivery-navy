"""Fit B0-B2 on train, tune B2's C on val, print the val table. ``--final`` also scores the two test sets.

Run: uv run --with scikit-learn python scripts/run_baselines.py [--final]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.baselines import fit_tfidf, predict_majority, predict_rules, predict_tfidf
from src.scoring import by_trap, costs, load_split, paired_bootstrap, score

DATASET = Path("data/dataset")
SHOWN = (
    "n",
    "valid_json_rate",
    "desk_accuracy",
    "urgent_wrong_desk",
    "confident_and_wrong",
    "abstention_rate",
    "macro_f1_intent",
    "exact_transaction_id",
    "exact_amount",
    "accuracy_urgency",
    "recall_high_urgency",
    "cost_per_ticket",
)
C_GRID = (0.3, 1.0, 3.0, 10.0)


def show(name: str, result: dict[str, float]) -> None:
    print(f"{name:4}", " ".join(f"{k}={result[k]:.3f}" for k in SHOWN))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--final", action="store_true", help="also score test_natural and test_traps"
    )
    args = parser.parse_args()
    train_x, train_y, _ = load_split(DATASET / "train.csv")
    val_x, val_y, _ = load_split(DATASET / "val.csv")
    best_c = min(
        C_GRID,
        key=lambda c: score(
            val_y, predict_tfidf(fit_tfidf(train_x, train_y, c), val_x)
        )["cost_per_ticket"],
    )
    models = fit_tfidf(train_x, train_y, best_c)
    systems = {
        "B0": lambda x: predict_majority(train_y, x),
        "B1": predict_rules,
        "B2": lambda x: predict_tfidf(models, x),
    }
    print(f"val ({len(val_y)} tickets), B2 C={best_c}")
    for name, predict in systems.items():
        show(name, score(val_y, predict(val_x)))
    if not args.final:
        return
    test_x, test_y, _ = load_split(DATASET / "test_natural.csv")
    preds = {name: predict(test_x) for name, predict in systems.items()}
    print(f"test_natural ({len(test_y)} tickets)")
    for name, raws in preds.items():
        show(name, score(test_y, raws))
    best = min(("B1", "B2"), key=lambda n: score(test_y, preds[n])["cost_per_ticket"])
    for name in ("B0", "B1", "B2"):
        if name != best:
            mean, low, high = paired_bootstrap(
                costs(test_y, preds[name]), costs(test_y, preds[best])
            )
            print(f"cost {name} - {best}: {mean:.3f} [{low:.3f}, {high:.3f}]")
    trap_x, trap_y, trap_tags = load_split(DATASET / "test_traps.csv")
    for name, predict in systems.items():
        print(f"test_traps {name}: (tickets, desk accuracy, cost) per trap")
        for trap, row in by_trap(trap_y, predict(trap_x), trap_tags).items():
            print(f"  {trap:28} n={row[0]:3} desk={row[1]:.2f} cost={row[2]:.2f}")


if __name__ == "__main__":
    main()
