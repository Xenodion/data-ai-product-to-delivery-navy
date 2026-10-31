"""Output contract of the ticket reader: seven string fields, a closed taxonomy, two sentinels.

Every value is a string (no JSON null). Real class labels are lowercase snake_case. The sentinels
``UNDEFINED`` and ``OTHER`` are uppercase, so "uppercase" always means "a human decides". An empty string
means "absent from the ticket" and is only allowed on the nullable fields. Definitions of each value:
``docs/label_definitions.md``.
"""

import re
from collections.abc import Callable
from typing import Final

from pydantic import BaseModel, ConfigDict, model_validator

UNDEFINED: Final = "UNDEFINED"  # the ticket does not allow a decision (ambiguous, vague, malformed reference)
OTHER: Final = "OTHER"  # understood, but no desk or listed sub-intent fits
SENTINELS: Final = (OTHER, UNDEFINED)

SUB_INTENTS: Final[dict[str, tuple[str, ...]]] = {
    "payment_status": (
        "delayed_credit",
        "missing_payment",
        "status_inquiry",
        "refund_status",
    ),
    "dispute": (
        "unauthorised_fee",
        "chargeback",
        "duplicate_charge",
        "amount_mismatch",
    ),
    "technical_api": (
        "webhook_down",
        "api_error",
        "auth_failure",
        "integration_question",
    ),
    "compliance": (
        "kyc_update",
        "account_hold",
        "document_request",
        "regulatory_question",
    ),
}
URGENCIES: Final = ("high", "medium", "low")
SENTIMENTS: Final = ("negative", "neutral", "positive")
CURRENCIES: Final = ("EUR", "USD", "GBP", "CHF", "CAD", "SEK", "DKK", "NOK", "PLN")

TRANSACTION_ID_PATTERN: Final = re.compile(r"TX-\d{6}")
AMOUNT_PATTERN: Final = re.compile(r"\d+\.\d{2}")


class TicketLabel(BaseModel):
    """One labelled ticket. Validation is the deterministic rule set of the dataset, the scorer and serving."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    intent: str
    sub_intent: str
    transaction_id: str  # nullable: "" when the ticket holds no transaction reference
    amount: str  # nullable: "" when the ticket holds no amount
    currency: str  # nullable: "" when the ticket holds no currency
    urgency: str
    sentiment: str

    @model_validator(mode="after")
    def _check_rules(self) -> "TicketLabel":
        _require(self.intent in (*SUB_INTENTS, *SENTINELS), "intent", self.intent)
        if self.intent in SENTINELS:
            _require(
                self.sub_intent == self.intent,
                "sub_intent (must repeat the intent sentinel)",
                self.sub_intent,
            )
        else:
            _require(
                self.sub_intent in (*SUB_INTENTS[self.intent], *SENTINELS),
                "sub_intent",
                self.sub_intent,
            )
        _require(self.urgency in (*URGENCIES, UNDEFINED), "urgency", self.urgency)
        _require(
            self.sentiment in (*SENTIMENTS, UNDEFINED), "sentiment", self.sentiment
        )
        _require(
            _nullable_ok(self.transaction_id, TRANSACTION_ID_PATTERN.fullmatch),
            "transaction_id",
            self.transaction_id,
        )
        _require(
            _nullable_ok(self.amount, AMOUNT_PATTERN.fullmatch), "amount", self.amount
        )
        _require(
            _nullable_ok(self.currency, lambda v: v if v in CURRENCIES else None),
            "currency",
            self.currency,
        )
        return self


def _nullable_ok(value: str, is_valid: Callable[[str], object]) -> bool:
    return value in ("", UNDEFINED) or bool(is_valid(value))


def _require(condition: bool, field: str, value: str) -> None:
    if not condition:
        raise ValueError(f"invalid {field}: {value!r}")
