"""Reads the probability the Qualifier gave to the value of a field, from the token log probabilities.

The model writes one JSON object, so the useful signal is not a softmax over all classes but the
probability of the first token of a field value (the moment it picks among the classes). JSON syntax
tokens are ignored. Nothing here treats a token probability as a probability of being correct:
that is measured later, against the labels.
"""

import math
from dataclasses import dataclass
from typing import Final

FIELDS: Final = ("intent", "sub_intent", "urgency")


@dataclass(frozen=True)
class FieldSignal:
    """What the model did at the first token of one field value."""

    field: str
    value_token: str
    p_chosen: float  # probability of the token it wrote
    p_top1: float  # probability of the most likely token (equals p_chosen when decoding is greedy)
    p_top2: float  # probability of the runner-up, 0.0 when only one candidate is returned
    p_value: float  # product of the probabilities of all tokens of the value


def _probability(logprob: float) -> float:
    return math.exp(logprob)


def field_signal(
    text: str,
    offsets: list[int],
    tokens: list[str],
    token_logprobs: list[float],
    top_logprobs: list[dict[str, float]],
    field: str,
) -> FieldSignal | None:
    """Return the signal of `field` or None when its value is not found in the generated JSON."""
    marker = f'"{field}":"'
    start = text.find(marker)
    if start < 0:
        return None
    value_start = start + len(marker)
    value_end = text.find('"', value_start)
    if value_end < 0:
        return None
    covered = [i for i, off in enumerate(offsets) if value_start <= off < value_end]
    # A token may begin before the value (for example `":"` merged with the first letters).
    if not covered:
        return None
    first = covered[0]
    ranked = sorted((_probability(lp) for lp in top_logprobs[first].values()), reverse=True)
    p_value = math.prod(_probability(token_logprobs[i]) for i in covered)
    return FieldSignal(
        field=field,
        value_token=tokens[first],
        p_chosen=_probability(token_logprobs[first]),
        p_top1=ranked[0],
        p_top2=ranked[1] if len(ranked) > 1 else 0.0,
        p_value=p_value,
    )
