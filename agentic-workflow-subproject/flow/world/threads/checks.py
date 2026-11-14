"""Automatic checks of a generated thread; no model judge."""

import re
from collections.abc import Mapping

from flow.world.threads.plan import ThreadPlan, digits

_FIGURE = re.compile(r"\d[\d.,/ -]*\d|\d")
_REFERENCE = re.compile(r"\bTX-\d{6}\b")
MIN_FIGURE_DIGITS = 3  # shorter numbers ("2 days", "3 steps") are not facts
QUESTION_TAIL = 120  # characters of the last message searched for a question mark


def allowed_digits(plan: ThreadPlan) -> set[str]:
    """Digit strings a reply may quote: facts, guidance, the opening and the planned dates."""
    sources = [*plan.facts, plan.policy, plan.opening, *plan.stamps()]
    allowed = {digits(token) for text in sources for token in _FIGURE.findall(text)}
    allowed |= {digits(stamp[:10]) for stamp in plan.stamps()}
    return allowed


def check_thread(plan: ThreadPlan, bodies: Mapping[int, str], max_chars: int) -> list[str]:
    """Problems of the written messages against the plan; empty when the thread is acceptable."""
    expected = [m.turn_index for m in plan.messages]
    if sorted(bodies) != expected:
        return [f"turns {sorted(bodies)} instead of {expected}"]
    problems = []
    allowed = allowed_digits(plan)
    for turn, body in bodies.items():
        text = body.strip()
        if not text or len(text) > max_chars:
            problems.append(f"turn {turn}: empty or longer than {max_chars} characters")
        for token in _FIGURE.findall(text):
            number = digits(token)
            if len(number) >= MIN_FIGURE_DIGITS and number not in allowed:
                problems.append(f"turn {turn}: figure {token.strip()} is not in the allowed set")
        for reference in _REFERENCE.findall(text):
            if digits(reference) not in allowed:
                problems.append(f"turn {turn}: identifier {reference} is not in the allowed set")
    last = bodies[expected[-1]].strip()
    asks = "?" in last[-QUESTION_TAIL:]
    if plan.state == "open_awaiting_merchant" and not asks:
        problems.append("a thread waiting for the merchant must end with a question or request")
    if plan.state == "closed" and "?" in last:
        problems.append("a closed thread must not end with a question")
    return problems
