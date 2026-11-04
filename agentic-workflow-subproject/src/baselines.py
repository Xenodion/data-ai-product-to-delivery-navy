"""Baselines of ``docs/scoring_protocol.md``: B0 majority class, B1 rules, B2 TF-IDF + logistic regression.

Each baseline maps ticket texts to raw JSON outputs of the contract, so ``src.scoring.score`` treats them like any model.
Reference fields (``transaction_id``, ``amount``, ``currency``) cannot be classified: B2 reuses the B1 extractors for them.
"""

import json
import re
from collections.abc import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from src.dataset_build.schema import (
    CURRENCIES,
    SENTINELS,
    SUB_INTENTS,
    TRANSACTION_ID_PATTERN,
    TicketLabel,
)
from src.scoring import majority_counts

CLASS_FIELDS = ("intent", "sub_intent", "urgency", "sentiment")
CURRENCY_SYMBOLS = {"€": "EUR", "$": "USD", "£": "GBP"}
AMOUNT_RE = re.compile(
    r"(\d[\d.,]*)\s*(k?)\s*(EUR|USD|GBP|CHF|CAD|SEK|DKK|NOK|PLN|€|\$|£)", re.IGNORECASE
)
# ponytail: first keyword hit wins; add weights or a lexicon if B1 must be stronger.
INTENT_KEYWORDS = {
    "payment_status": (
        "refund",
        "payout",
        "settlement",
        "credited",
        "payment",
        "transfer",
    ),
    "dispute": (
        "dispute",
        "chargeback",
        "charged twice",
        "fee",
        "double",
        "overcharged",
    ),
    "technical_api": (
        "api",
        "webhook",
        "token",
        "401",
        "500",
        "integration",
        "endpoint",
    ),
    "compliance": (
        "kyc",
        "compliance",
        "document",
        "verification",
        "frozen",
        "regulat",
    ),
}
SUB_INTENT_KEYWORDS = {
    "refund_status": ("refund",),
    "delayed_credit": ("delay", "not yet received"),
    "missing_payment": ("missing", "never received"),
    "chargeback": ("chargeback",),
    "duplicate_charge": ("twice", "duplicate", "double"),
    "unauthorised_fee": ("fee",),
    "amount_mismatch": ("wrong amount", "mismatch"),
    "webhook_down": ("webhook",),
    "auth_failure": ("401", "token", "auth"),
    "api_error": ("500", "error"),
    "kyc_update": ("kyc",),
    "account_hold": ("frozen", "hold", "blocked"),
    "document_request": ("document",),
    "regulatory_question": ("regulat",),
}
URGENT_WORDS = ("urgent", "asap", "immediately", "right now", "today", "blocked")
NEGATIVE_WORDS = (
    "unacceptable",
    "furious",
    "angry",
    "disappointed",
    "terrible",
    "ridiculous",
)
POSITIVE_WORDS = ("thank", "thanks", "appreciate", "great")


def _fix(fields: dict[str, str]) -> str:
    """Make ``sub_intent`` consistent with ``intent`` so the output is valid, then serialise."""
    intent, sub = fields["intent"], fields["sub_intent"]
    if intent in SENTINELS:
        fields["sub_intent"] = intent
    elif sub not in (*SUB_INTENTS[intent], *SENTINELS):
        fields["sub_intent"] = "OTHER"
    return json.dumps(TicketLabel(**fields).model_dump())


def _first_hit(text: str, table: dict[str, tuple[str, ...]], default: str) -> str:
    return next(
        (k for k, words in table.items() if any(w in text for w in words)), default
    )


def extract_references(ticket: str) -> dict[str, str]:
    """Regex extraction of the transaction id, amount and currency ("" when absent)."""
    tx = TRANSACTION_ID_PATTERN.search(ticket)
    amount, currency = "", ""
    if match := AMOUNT_RE.search(ticket):
        digits, kilo, cur = match.groups()
        number = (
            digits.replace(",", ".")
            if re.search(r",\d{2}$", digits)
            else digits.replace(",", "")
        )
        try:
            value = float(number) * (1000 if kilo else 1)
            amount = f"{value:.2f}"
        except ValueError:
            amount = ""
        currency = CURRENCY_SYMBOLS.get(cur, cur.upper())
        currency = currency if currency in CURRENCIES else ""
    return {
        "transaction_id": tx.group() if tx else "",
        "amount": amount,
        "currency": currency,
    }


def predict_rules(tickets: Sequence[str]) -> list[str]:
    """B1: keywords and regular expressions."""
    outputs = []
    for ticket in tickets:
        text = ticket.lower()
        intent = _first_hit(text, INTENT_KEYWORDS, "OTHER")
        sentiment = (
            "negative"
            if any(w in text for w in NEGATIVE_WORDS)
            else "positive"
            if any(w in text for w in POSITIVE_WORDS)
            else "neutral"
        )
        outputs.append(
            _fix(
                {
                    "intent": intent,
                    "sub_intent": _first_hit(
                        text, {k: v for k, v in SUB_INTENT_KEYWORDS.items()}, "OTHER"
                    ),
                    **extract_references(ticket),
                    "urgency": "high"
                    if any(w in text for w in URGENT_WORDS)
                    else "medium",
                    "sentiment": sentiment,
                }
            )
        )
    return outputs


def predict_majority(
    train_labels: Sequence[TicketLabel], tickets: Sequence[str]
) -> list[str]:
    """B0: the most frequent value of each field in train, whatever the ticket says."""
    fields = {
        f: majority_counts(train_labels, f).most_common(1)[0][0]
        for f in (*CLASS_FIELDS, "transaction_id", "amount", "currency")
    }
    return [_fix(dict(fields)) for _ in tickets]


def fit_tfidf(
    train_tickets: Sequence[str], train_labels: Sequence[TicketLabel], c: float = 1.0
) -> dict[str, object]:
    """B2: one TF-IDF + logistic regression model per classified field."""
    return {
        f: make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2),
            LogisticRegression(C=c, max_iter=1000),
        ).fit(train_tickets, [getattr(label, f) for label in train_labels])
        for f in CLASS_FIELDS
    }


def predict_tfidf(models: dict[str, object], tickets: Sequence[str]) -> list[str]:
    columns = {f: models[f].predict(list(tickets)) for f in CLASS_FIELDS}
    return [
        _fix(
            {
                **{f: str(columns[f][i]) for f in CLASS_FIELDS},
                **extract_references(ticket),
            }
        )
        for i, ticket in enumerate(tickets)
    ]
