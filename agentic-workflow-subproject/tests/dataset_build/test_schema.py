import pytest
from pydantic import ValidationError

from src.dataset_build.schema import TicketLabel

VALID = {
    "intent": "payment_status",
    "sub_intent": "delayed_credit",
    "transaction_id": "TX-994821",
    "amount": "12500.00",
    "currency": "EUR",
    "urgency": "high",
    "sentiment": "negative",
}


def test_ticket_label_accepts_valid_label_and_sentinels():
    TicketLabel(**VALID)
    TicketLabel(
        **{
            **VALID,
            "intent": "OTHER",
            "sub_intent": "OTHER",
            "transaction_id": "",
            "amount": "",
            "currency": "",
        }
    )
    TicketLabel(**{**VALID, "transaction_id": "UNDEFINED", "urgency": "UNDEFINED"})


@pytest.mark.parametrize(
    "override",
    [
        {"intent": "other"},  # sentinels are uppercase
        {
            "intent": "OTHER",
            "sub_intent": "delayed_credit",
        },  # sentinel intent forces the same sub_intent
        {"sub_intent": "webhook_down"},  # sub_intent of another intent
        {"urgency": ""},  # required field cannot be empty
        {"transaction_id": "TX-12345"},  # wrong digit count: UNDEFINED, not a guess
        {"amount": "12,500.00"},
        {"currency": "$"},
        {"currency": None},  # no JSON null
    ],
)
def test_ticket_label_rejects_rule_violations(override):
    with pytest.raises(ValidationError):
        TicketLabel(**{**VALID, **override})
