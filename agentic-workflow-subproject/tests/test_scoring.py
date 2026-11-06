import json

import pytest

from research.qualifier.src.dataset_build.schema import TicketLabel
from research.qualifier.src.scoring import (
    by_trap,
    macro_f1,
    mean_interval,
    paired_bootstrap,
    score,
    silent_by_trap,
    ticket_severity,
)

BASE = {
    "intent": "payment_status",
    "sub_intent": "delayed_credit",
    "transaction_id": "TX-123456",
    "amount": "10.00",
    "currency": "EUR",
    "urgency": "low",
    "sentiment": "neutral",
}


def label(**over: str) -> TicketLabel:
    return TicketLabel(**{**BASE, **over})


def raw(**over: str) -> str:
    return json.dumps({**BASE, **over})


def test_ticket_severity_follows_the_cost_matrix():
    truth = label()
    assert ticket_severity(truth, label()) == 0
    assert ticket_severity(truth, label(intent="OTHER", sub_intent="OTHER")) == 1
    assert ticket_severity(truth, None) == 1
    assert ticket_severity(truth, label(amount="11.00")) == 5
    assert ticket_severity(truth, label(intent="dispute", sub_intent="chargeback")) == 3
    urgent = label(urgency="high")
    assert (
        ticket_severity(urgent, label(intent="dispute", sub_intent="chargeback")) == 10
    )


def test_score_counts_invalid_output_as_wrong_and_triaged():
    truths = [label(), label(urgency="high")]
    res = score(truths, [raw(), "not json"])
    assert res["valid_json_rate"] == 0.5
    assert res["desk_accuracy"] == 0.5
    assert res["urgent_wrong_desk"] == 0  # triage is not a wrong desk
    assert res["recall_high_urgency"] == 0
    assert res["severity_score"] == 0.5


def test_score_urgent_ticket_in_wrong_desk_is_a_silent_error():
    truths = [label(urgency="high")]
    res = score(
        truths, [raw(intent="dispute", sub_intent="chargeback", urgency="high")]
    )
    assert res["urgent_wrong_desk"] == 1
    assert res["silent_error_rate"] == 1
    assert res["severity_score"] == 10
    assert res["severity_score_urgent_doubled"] == 20


def test_macro_f1_perfect_and_half():
    assert macro_f1(["a", "b"], ["a", "b"]) == 1
    assert macro_f1(["a", "b"], ["a", "a"]) == pytest.approx(1 / 3 * 1)  # a: 2/3, b: 0


def test_paired_bootstrap_interval_excludes_zero_for_constant_gap():
    mean, low, high = paired_bootstrap([3.0] * 50, [1.0] * 50)
    assert mean == low == high == 2.0


def test_by_trap_splits_multi_trap_tags():
    truths = [label(), label()]
    res = by_trap(
        truths, [raw(), "bad"], ["id_lowercase|amount_k_suffix", "id_lowercase"]
    )
    assert res["id_lowercase"][0] == 2 and res["amount_k_suffix"][0] == 1
    assert res["id_lowercase"][1] == 0.5


def test_silent_error_needless_triage_and_auto_routed_rates():
    truths = [
        label(),
        label(),
        label(),
        label(intent="UNDEFINED", sub_intent="UNDEFINED"),
    ]
    raws = [
        raw(),  # right
        raw(amount="11.00"),  # silent: right desk, wrong reference
        raw(
            intent="OTHER", sub_intent="OTHER"
        ),  # sent to a human although a desk exists
        raw(),  # silent: routed although the label says UNDEFINED
    ]
    res = score(truths, raws)
    assert res["auto_routed_rate"] == 0.75
    assert res["silent_error_rate"] == 0.5
    assert res["needless_triage_rate"] == 0.25


def test_silent_by_trap_counts_per_family():
    truths = [label(), label(), label()]
    res = silent_by_trap(truths, [raw(), raw(amount="11.00"), "bad"], ["a|b", "a", "b"])
    assert res["a"] == (2, 0.5)
    assert res["b"] == (2, 0.0)  # an invalid output goes to a human: not silent


def test_mean_interval_of_a_constant_is_that_constant():
    assert mean_interval([2.0] * 20) == (2.0, 2.0, 2.0)
