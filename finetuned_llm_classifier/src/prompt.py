"""Instruction shared by the training, inference and serving steps.

KFP components cannot import local modules, so the pipelines pass INSTRUCTION to them as a parameter.
"""

INSTRUCTION = (
    "You read one support ticket sent by a merchant of a B2B payments company, in French or English. "
    "Answer with one JSON object and nothing else, with exactly these keys: "
    "intent (payment_status, dispute, technical_api, compliance or other), "
    "sub_intent (a short snake_case label), "
    "transaction_id (a reference such as TX-994821, or null), "
    "amount (a decimal string with two decimals, or null), "
    "currency (an ISO 4217 code, or null), "
    "urgency (high, medium or low), "
    "sentiment (negative, neutral or positive). "
    'Use the string "UNDEFINED" for a text field you cannot determine from the ticket, '
    "and null for an optional field that is absent. Never guess."
)


def build_user_message(ticket: str, instruction: str = INSTRUCTION) -> str:
    """Return the user turn of the chat: the instruction followed by the ticket."""
    return f"{instruction}\n\nTicket:\n{ticket}"
