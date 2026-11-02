"""Instruction shared by the training, inference and serving steps.

KFP components cannot import local modules, so the pipelines pass INSTRUCTION to them as a parameter.
Built from the contract in `dataset_build/schema.py` so that the two cannot drift.
"""

from src.dataset_build.schema import (
    CURRENCIES,
    OTHER,
    SENTIMENTS,
    SUB_INTENTS,
    UNDEFINED,
    URGENCIES,
)

_SUB_INTENT_LIST = "; ".join(
    f"{intent}: {', '.join(subs)}" for intent, subs in SUB_INTENTS.items()
)

INSTRUCTION = (
    "You read one support ticket sent by a merchant of a B2B payments company, in French or English. "
    "Answer with one JSON object and nothing else, with exactly these keys, all string values: "
    f"intent ({', '.join(SUB_INTENTS)}, {OTHER} or {UNDEFINED}), "
    f"sub_intent (one of: {_SUB_INTENT_LIST}; or {OTHER} or {UNDEFINED}), "
    "transaction_id (TX- followed by 6 digits, or empty), "
    "amount (a decimal with a dot and two decimals, no thousands separator, or empty), "
    f"currency (one of {', '.join(CURRENCIES)}, or empty), "
    f"urgency ({', '.join(URGENCIES)} or {UNDEFINED}), "
    f"sentiment ({', '.join(SENTIMENTS)} or {UNDEFINED}). "
    'Use "" for transaction_id, amount or currency that is absent from the ticket. '
    f'Use "{UNDEFINED}" for a field you cannot determine from the ticket, and "{OTHER}" for a request '
    f"you understand but that fits no listed intent or sub-intent. Never guess."
)


def build_user_message(ticket: str, instruction: str = INSTRUCTION) -> str:
    """Return the user turn of the chat: the instruction followed by the ticket."""
    return f"{instruction}\n\nTicket:\n{ticket}"
