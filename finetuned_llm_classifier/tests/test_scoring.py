import json

import pytest

from src.dataset_build.schema import TicketLabel
from src.scoring import by_trap, macro_f1, paired_bootstrap, score, ticket_cost

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


def test_ticket_cost_follows_the_cost_matrix():
    truth = label()
    assert ticket_cost(truth, label()) == 0
    assert ticket_cost(truth, label(intent="OTHER", sub_intent="OTHER")) == 1
    assert ticket_cost(truth, None) == 1
    assert ticket_cost(truth, label(amount="11.00")) == 5
    assert ticket_cost(truth, label(intent="dispute", sub_intent="chargeback")) == 3
    urgent = label(urgency="high")
    assert ticket_cost(urgent, label(intent="dispute", sub_intent="chargeback")) == 10


def test_score_counts_invalid_output_as_wrong_and_triaged():
    truths = [label(), label(urgency="high")]
    res = score(truths, [raw(), "not json"])
    assert res["valid_json_rate"] == 0.5
    assert res["desk_accuracy"] == 0.5
    assert res["urgent_wrong_desk"] == 0  # triage is not a wrong desk
    assert res["recall_high_urgency"] == 0
    assert res["cost_per_ticket"] == 0.5


def test_score_urgent_ticket_in_wrong_desk_and_confident_wrong():
    truths = [label(urgency="high")]
    res = score(
        truths, [raw(intent="dispute", sub_intent="chargeback", urgency="high")]
    )
    assert res["urgent_wrong_desk"] == 1
    assert res["confident_and_wrong"] == 1
    assert res["cost_per_ticket"] == 10
    assert res["cost_per_ticket_urgent_doubled"] == 20


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
