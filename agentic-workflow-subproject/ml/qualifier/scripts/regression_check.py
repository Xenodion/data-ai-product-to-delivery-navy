"""Regression gate of the Qualifier on the eval-set (issue #19): exit 1 when it fails.

    uv run python ml/qualifier/scripts/regression_check.py

Replays the stored predictions; no model, no network, no cost. To refresh the predictions after a
change of prompt, schema, model or eval-set, run `uv run python -m flow.regression_predict` on a
machine with the local Qualifier.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.qualifier.src.regression_eval import (  # noqa: E402
    expected_fingerprint,
    load_predictions,
    load_thresholds,
    load_triples,
    resolve,
    run_gate,
)

SHOWN = ("valid_json_rate", "desk_accuracy", "auto_routed_rate", "urgent_wrong_desk", "silent_error_rate")


def main() -> int:
    thresholds = load_thresholds()
    source = thresholds["source"]
    eval_set, predictions_path, manifest_path = (resolve(source[k]) for k in ("eval_set", "predictions", "manifest"))
    triples = load_triples(eval_set)
    if not predictions_path.exists() or not manifest_path.exists():
        print(f"FAIL: no stored predictions at {predictions_path.name}; run `python -m flow.regression_predict`.")
        return 1
    report = run_gate(
        triples,
        load_predictions(predictions_path),
        json.loads(manifest_path.read_text(encoding="utf-8")),
        expected_fingerprint(eval_set, resolve(source["flow_config"])),
        thresholds,
    )
    print(f"{len(triples)} test triples from {eval_set.name}")
    for name in SHOWN:
        print(f"  {name:<20} {report.metrics[name]:.4f}")
    if report.passed:
        print("PASS")
        return 0
    for failure in report.failures:
        print(f"FAIL: {failure}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
