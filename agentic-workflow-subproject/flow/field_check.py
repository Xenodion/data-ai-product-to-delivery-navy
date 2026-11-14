"""Non-blocking field verification against the merchant-authored message (node 3)."""

import re
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from flow.contracts import FieldCheckResult, FieldEvidence, Ticket
from ml.qualifier.src.dataset_build.schema import TicketLabel, UNDEFINED


def _reference_status(
    value: str, text: str, matches: Callable[[str, str], bool]
) -> FieldEvidence:
    if not value:
        return FieldEvidence(status="absent", value=value)
    if value == UNDEFINED:
        return FieldEvidence(status="unverified", value=value)
    return FieldEvidence(
        status="verified" if matches(value, text) else "unverified",
        value=value,
    )


def _id_mentioned(value: str, text: str) -> bool:
    target = re.sub(r"[^A-Z0-9]", "", value.upper())
    # Allow display variants such as ``TX 385 830`` for canonical ``TX-385830``.
    tokens = re.findall(r"[A-Z0-9]+", text.upper())
    return any(
        "".join(tokens[start : start + width]) == target
        for start in range(len(tokens))
        for width in range(1, 4)
    )


def _parse_amount(token: str) -> Decimal | None:
    compact = token.lower().replace("\u00a0", "").replace(" ", "")
    multiplier = Decimal("1000") if compact.endswith("k") else Decimal("1")
    if compact.endswith("k"):
        compact = compact[:-1]
    if "," in compact and "." in compact:
        decimal_mark = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands_mark = "." if decimal_mark == "," else ","
        compact = compact.replace(thousands_mark, "").replace(decimal_mark, ".")
    elif "," in compact or "." in compact:
        mark = "," if "," in compact else "."
        tail = compact.rsplit(mark, 1)[1]
        if len(tail) == 3:
            compact = compact.replace(mark, "")
        else:
            compact = compact.replace(mark, ".")
    try:
        return Decimal(compact) * multiplier
    except InvalidOperation:
        return None


_AMOUNT_TOKEN = re.compile(
    r"(?<![\w])\d+(?:[ ,.\u00a0]\d{3})*(?:[,.]\d{1,2})?\s?[kK]?(?![\w])"
)


def _amount_mentioned(value: str, text: str) -> bool:
    expected = _parse_amount(value)
    if expected is None:
        return False
    for match in _AMOUNT_TOKEN.finditer(text):
        candidate = _parse_amount(match.group())
        if candidate == expected:
            return True
    return False


_CURRENCY_MARKS = {
    "EUR": ("EUR", "€"),
    "USD": ("USD",),
    "GBP": ("GBP", "£"),
    "CHF": ("CHF",),
    "CAD": ("CAD",),
    "SEK": ("SEK",),
    "DKK": ("DKK",),
    "NOK": ("NOK",),
    "PLN": ("PLN", "zł"),
}


def _currency_mentioned(value: str, text: str) -> bool:
    upper = text.upper()
    return any(
        re.search(rf"(?<![A-Z]){re.escape(mark.upper())}(?![A-Z])", upper)
        if mark.isalpha()
        else mark in text
        for mark in _CURRENCY_MARKS.get(value, (value,))
    )


def check_fields(ticket: Ticket, label: TicketLabel) -> FieldCheckResult:
    """Mark model-extracted references verified only when the text supports them."""
    text = ticket.message_text
    return FieldCheckResult(
        transaction_id=_reference_status(label.transaction_id, text, _id_mentioned),
        amount=_reference_status(label.amount, text, _amount_mentioned),
        currency=_reference_status(label.currency, text, _currency_mentioned),
    )
