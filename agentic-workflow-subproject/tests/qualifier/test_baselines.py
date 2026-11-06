import json

from ml.qualifier.src.baselines import (
    extract_references,
    fit_tfidf,
    predict_majority,
    predict_rules,
    predict_tfidf,
)
from ml.qualifier.src.dataset_build.schema import TicketLabel
from ml.qualifier.src.scoring import parse_output

LABEL = TicketLabel(
    intent="dispute",
    sub_intent="chargeback",
    transaction_id="TX-123456",
    amount="10.00",
    currency="EUR",
    urgency="high",
    sentiment="negative",
)
TICKETS = [
    "URGENT chargeback on TX-123456, 10.00 EUR, unacceptable",
    "webhook endpoint returns 500, please help",
] * 6


def test_extract_references_handles_formats():
    assert extract_references("see TX-123456, 1.5k EUR") == {
        "transaction_id": "TX-123456",
        "amount": "1500.00",
        "currency": "EUR",
    }
    assert extract_references("charged 440,50 €")["amount"] == "440.50"
    assert extract_references("nothing here") == {
        "transaction_id": "",
        "amount": "",
        "currency": "",
    }


def test_baselines_always_emit_valid_outputs():
    labels = [
        LABEL,
        LABEL.model_copy(
            update={
                "intent": "technical_api",
                "sub_intent": "webhook_down",
                "urgency": "low",
                "sentiment": "neutral",
            }
        ),
    ] * 6
    for raws in (
        predict_rules(TICKETS),
        predict_majority(labels, TICKETS),
        predict_tfidf(fit_tfidf(TICKETS, labels), TICKETS),
    ):
        assert len(raws) == len(TICKETS) and all(parse_output(r) for r in raws)


def test_rules_read_chargeback_ticket():
    out = json.loads(predict_rules(TICKETS[:1])[0])
    assert (
        out["intent"],
        out["sub_intent"],
        out["urgency"],
        out["transaction_id"],
    ) == ("dispute", "chargeback", "high", "TX-123456")
