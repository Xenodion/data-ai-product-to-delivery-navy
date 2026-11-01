"""Score the predictions CSV of the inference step against a split: python scripts/score_predictions.py <predictions.csv> <split>.

The predictions file comes from the pipeline (columns user_input, extracted_response); <split> is val, test_natural or test_traps.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_baselines import DATASET, SHOWN, show
from src.scoring import by_trap, load_split, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("split", choices=("val", "test_natural", "test_traps"))
    args = parser.parse_args()
    tickets, truths, traps = load_split(DATASET / f"{args.split}.csv")
    preds = pd.read_csv(args.predictions, keep_default_na=False)
    if list(preds["user_input"]) != tickets:
        raise ValueError(
            f"{args.predictions} does not hold the tickets of {args.split}, in the same order"
        )
    raws = list(preds["extracted_response"])
    print(f"{args.split} ({len(truths)} tickets)")
    show("pred", score(truths, raws))
    print(
        "other: "
        + " ".join(
            f"{k}={v:.3f}" for k, v in score(truths, raws).items() if k not in SHOWN
        )
    )
    if args.split == "test_traps":
        for trap, row in by_trap(truths, raws, traps).items():
            print(f"  {trap:28} n={row[0]:3} desk={row[1]:.2f} cost={row[2]:.2f}")


if __name__ == "__main__":
    main()
