import json

from ml.qualifier.src.regression_eval import (
    expected_fingerprint,
    load_thresholds,
    load_triples,
    repository_prompt_sha,
    resolve,
    run_gate,
)

THRESHOLDS = load_thresholds()
SOURCE = THRESHOLDS["source"]
EVAL_SET = resolve(SOURCE["eval_set"])
TRIPLES = load_triples(EVAL_SET)
EXPECTED = expected_fingerprint(EVAL_SET, resolve(SOURCE["flow_config"]))


def perfect_predictions() -> dict[str, str | None]:
    return {t.case_id: t.expected.model_dump_json() for t in TRIPLES}


def test_eval_set_gives_100_valid_triples_with_urgent_cases() -> None:
    assert len(TRIPLES) == 100
    assert sum(t.expected.urgency == "high" for t in TRIPLES) > 0


def test_thresholds_name_only_metrics_of_the_scorer() -> None:
    report = run_gate(TRIPLES, perfect_predictions(), EXPECTED, EXPECTED, THRESHOLDS)
    names = set(THRESHOLDS["min"]) | set(THRESHOLDS["max"])
    assert names <= set(report.metrics)


def test_labels_replayed_as_predictions_pass_the_gate() -> None:
    report = run_gate(TRIPLES, perfect_predictions(), EXPECTED, EXPECTED, THRESHOLDS)
    assert report.passed, report.failures
    assert report.metrics["silent_error_rate"] == 0


def test_one_urgent_ticket_in_a_wrong_desk_fails_the_gate() -> None:
    predictions = perfect_predictions()
    urgent = next(t for t in TRIPLES if t.expected.urgency == "high" and t.expected.intent == "dispute")
    wrong = urgent.expected.model_copy(update={"intent": "technical_api", "sub_intent": "api_error"})
    predictions[urgent.case_id] = wrong.model_dump_json()
    report = run_gate(TRIPLES, predictions, EXPECTED, EXPECTED, THRESHOLDS)
    assert any("urgent_wrong_desk" in failure for failure in report.failures)


def test_invalid_outputs_below_the_bar_fail_the_gate() -> None:
    predictions = perfect_predictions()
    for triple in TRIPLES[:2]:
        predictions[triple.case_id] = "not json"
    report = run_gate(TRIPLES, predictions, EXPECTED, EXPECTED, THRESHOLDS)
    assert any("valid_json_rate" in failure for failure in report.failures)


def test_a_changed_prompt_makes_stored_predictions_stale() -> None:
    manifest = {**EXPECTED, "prompt_sha256": "0" * 64}
    report = run_gate(TRIPLES, perfect_predictions(), manifest, EXPECTED, THRESHOLDS)
    assert any("stale predictions" in failure and "prompt_sha256" in failure for failure in report.failures)


def test_a_missing_prediction_fails_the_gate() -> None:
    predictions = perfect_predictions()
    predictions.pop(TRIPLES[0].case_id)
    report = run_gate(TRIPLES, predictions, EXPECTED, EXPECTED, THRESHOLDS)
    assert any("have no prediction" in failure for failure in report.failures)


def test_fingerprint_tracks_the_repository_prompt() -> None:
    assert EXPECTED["prompt_sha256"] == repository_prompt_sha()
    assert json.loads(json.dumps(EXPECTED)) == EXPECTED
