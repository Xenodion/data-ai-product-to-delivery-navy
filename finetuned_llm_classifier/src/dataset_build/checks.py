"""Deterministic checks of a written ticket against its card (free, run on every ticket)."""

import re

from src.dataset_build.cards import Card
from src.dataset_build.schema import CURRENCIES

TX_LIKE = re.compile(r"TX[- ]?\d{3}", re.IGNORECASE)
URGENCY_WORDS = re.compile(
    r"urgent|urgence|immediate|imm.diat|asap|as soon as possible|dringend|sofort|inmediat|subito|lo antes posible",
    re.IGNORECASE,
)
LONG_FORM_TAILS = frozenset({"signature", "disclaimer", "quoted_thread"})
CURRENCY_TOKEN = re.compile(r"[€£$]|\b(?:" + "|".join(CURRENCIES) + r")\b")


def check_ticket(card: Card, subject: str, body: str) -> list[str]:
    """Return the violation codes of a ticket; an empty list means it passed."""
    text = f"{subject}\n{body}"
    problems: list[str] = []
    if not body.strip():
        problems.append("empty_body")
    if (card.subject_mode == "absent") != (not subject.strip()):
        problems.append("subject_mode_not_respected")

    given = [
        surface
        for surface in (
            card.id_surface,
            card.id_second_surface,
            card.amount_surface,
            card.amount_second_surface,
            card.currency_only,
        )
        if surface
    ]
    if any(surface not in text for surface in given):
        problems.append("surface_missing")

    if card.id_case == "subject_only" and (
        card.id_surface not in subject or card.id_surface in body
    ):
        problems.append("reference_not_in_subject_only")
    if card.id_case == "quoted_only" and card.id_surface in subject:
        problems.append("quoted_reference_in_subject")

    if card.label.urgency == "low" and URGENCY_WORDS.search(text):
        problems.append("urgency_wording_on_low")
    if (
        card.sentinel_kind == "truncated"
        and not LONG_FORM_TAILS & set(card.noise)
        and _ends_cleanly(body)
    ):
        problems.append("not_truncated")

    rest = text
    for surface in sorted(given, key=len, reverse=True):
        rest = rest.replace(surface, " ")
    if TX_LIKE.search(rest):
        problems.append("extra_reference")
    if CURRENCY_TOKEN.search(rest):
        problems.append("extra_currency")
    return sorted(set(problems))


def _ends_cleanly(body: str) -> bool:
    """True when the text ends like a finished message: sentence punctuation, but not an ellipsis."""
    tail = body.rstrip()
    return tail[-1:] in tuple('.!?)"»') and not tail.endswith(("...", "…"))
