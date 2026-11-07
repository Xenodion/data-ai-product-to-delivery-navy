import pandas as pd

from ml.confidence.src.analysis import deferral_curve, with_score


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "routed": [True, True, True, True],
        "silent": [False, True, False, True],
        "urgent_wrong_desk": [False, True, False, False],
        "p_intent": [0.999, 0.6, 0.9, 0.99],
        "p_urgency": [0.9999, 0.99, float("nan"), 0.5],
    })


def test_with_score_takes_the_lowest_probability_and_ignores_missing() -> None:
    score = with_score(_frame(), ["intent", "urgency"])
    assert list(score.round(4)) == [0.999, 0.6, 0.9, 0.5]


def test_deferral_curve_counts_what_is_left_after_deferring() -> None:
    frame = _frame()
    curve = deferral_curve(frame, with_score(frame, ["intent", "urgency"]), [0.0, 0.7])
    assert list(curve["silent_left"]) == [2, 0]
    assert list(curve["urgent_wrong_desk_left"]) == [1, 0]
    assert list(curve["deferred"]) == [0, 2]
    assert list(curve["deferred_that_were_right"]) == [0, 0]
