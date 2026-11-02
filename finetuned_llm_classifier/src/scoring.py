"""Scoring of a system's outputs against dataset labels, as frozen in ``docs/scoring_protocol.md``.

Every system (baselines B0-B2, base LLM, LoRA model) is scored through ``score`` on the same tickets, with
one raw output string per ticket (``None`` when the system produced nothing). An output that does not parse
or does not pass ``TicketLabel`` is *invalid*: it counts as wrong on every field and is routed to human triage.
"""

import csv
import json
import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from src.dataset_build.schema import SENTINELS, TicketLabel

TRIAGE = "triage"
REFERENCE_FIELDS = ("transaction_id", "amount", "currency")
# Desk that handles each real intent; OTHER and UNDEFINED go to human triage.
DESK_OF_INTENT = {
    "payment_status": "payments",
    "dispute": "disputes",
    "technical_api": "technical",
    "compliance": "compliance",
}


@dataclass(frozen=True)
class CostWeights:
    """Relative weights of the protocol's cost matrix (ASSUMPTION until the euro values of the sizing land)."""

    triage: float = 1.0
    wrong_desk: float = 3.0
    wrong_reference: float = 5.0
    wrong_desk_urgent: float = 10.0


DEFAULT_WEIGHTS = CostWeights()


def desk_of(label: TicketLabel | None) -> str:
    """Desk of a label; an invalid output (``None``) goes to triage."""
    return DESK_OF_INTENT.get(label.intent, TRIAGE) if label else TRIAGE


def parse_output(raw: str | None) -> TicketLabel | None:
    """Parse a raw model output into a label; ``None`` when it is not valid JSON of the contract."""
    if raw is None:
        return None
    try:
        return TicketLabel(**json.loads(raw))
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def ticket_cost(
    truth: TicketLabel, pred: TicketLabel | None, weights: CostWeights = DEFAULT_WEIGHTS
) -> float:
    """Largest weight among the errors of one ticket (0 when correct)."""
    true_desk, pred_desk = desk_of(truth), desk_of(pred)
    if pred_desk != TRIAGE and pred_desk != true_desk:
        return (
            weights.wrong_desk_urgent if truth.urgency == "high" else weights.wrong_desk
        )
    if pred_desk == TRIAGE and true_desk != TRIAGE:
        return weights.triage
    if (
        pred_desk != TRIAGE
        and pred
        and any(getattr(pred, f) != getattr(truth, f) for f in REFERENCE_FIELDS)
    ):
        return weights.wrong_reference
    return 0.0


def macro_f1(truth: Sequence[str], pred: Sequence[str]) -> float:
    """Macro-averaged F1 over the classes present in ``truth``; an invalid prediction is the class ``""``."""
    scores = []
    for cls in set(truth):
        tp = sum(t == cls and p == cls for t, p in zip(truth, pred))
        fp = sum(t != cls and p == cls for t, p in zip(truth, pred))
        fn = sum(t == cls and p != cls for t, p in zip(truth, pred))
        scores.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return sum(scores) / len(scores)


def _share(hits: int, total: int) -> float:
    return hits / total if total else float("nan")


def score(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    weights: CostWeights = DEFAULT_WEIGHTS,
) -> dict[str, float]:
    """Metrics 1-10 of the protocol for one system on one set of tickets."""
    preds = [parse_output(r) for r in raws]
    pairs = list(zip(truths, preds))
    valid = [(t, p) for t, p in pairs if p]
    high = [(t, p) for t, p in pairs if t.urgency == "high"]
    answered = [(t, p) for t, p in valid if p.intent not in SENTINELS]
    doubled = CostWeights(
        weights.triage,
        weights.wrong_desk,
        weights.wrong_reference,
        2 * weights.wrong_desk_urgent,
    )
    out = {
        "n": float(len(pairs)),
        "valid_json_rate": _share(len(valid), len(pairs)),
        "desk_accuracy": _share(
            sum(desk_of(t) == desk_of(p) for t, p in pairs), len(pairs)
        ),
        "urgent_wrong_desk": _share(
            sum(desk_of(p) not in (TRIAGE, desk_of(t)) for t, p in high), len(high)
        ),
        "confident_and_wrong": _share(
            sum(p.intent != t.intent for t, p in answered), len(answered)
        ),
        "abstention_rate": _share(
            sum(p.intent in SENTINELS for _, p in valid), len(pairs)
        ),
        "answer_precision": _share(
            sum(p.intent == t.intent for t, p in answered), len(answered)
        ),
        "recall_high_urgency": _share(
            sum(bool(p) and p.urgency == "high" for _, p in high), len(high)
        ),
        "cost_per_ticket": sum(ticket_cost(t, p, weights) for t, p in pairs)
        / len(pairs),
        "cost_per_ticket_urgent_doubled": sum(
            ticket_cost(t, p, doubled) for t, p in pairs
        )
        / len(pairs),
    }
    for field in REFERENCE_FIELDS:
        out[f"exact_{field}"] = _share(
            sum(getattr(t, field) == getattr(p, field) for t, p in valid), len(pairs)
        )
    for field in ("urgency", "sentiment"):
        out[f"accuracy_{field}"] = _share(
            sum(getattr(t, field) == getattr(p, field) for t, p in valid), len(pairs)
        )
    for field in ("intent", "sub_intent"):
        out[f"macro_f1_{field}"] = macro_f1(
            [getattr(t, field) for t in truths],
            [getattr(p, field) if p else "" for p in preds],
        )
    return out


def costs(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    weights: CostWeights = DEFAULT_WEIGHTS,
) -> list[float]:
    """Per-ticket costs of one system, to feed ``paired_bootstrap``."""
    return [ticket_cost(t, parse_output(r), weights) for t, r in zip(truths, raws)]


def paired_bootstrap(
    costs_a: Sequence[float],
    costs_b: Sequence[float],
    resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Mean of ``a - b`` per ticket with its 95 % bootstrap interval, resampling the same tickets in both."""
    diffs = [a - b for a, b in zip(costs_a, costs_b)]
    rng = random.Random(seed)
    means = sorted(
        sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(resamples)
    )
    return (
        sum(diffs) / len(diffs),
        means[int(0.025 * resamples)],
        means[int(0.975 * resamples) - 1],
    )


def by_trap(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    traps: Sequence[str],
    weights: CostWeights = DEFAULT_WEIGHTS,
) -> dict[str, tuple[int, float, float]]:
    """Per trap type: (tickets, desk accuracy, cost per ticket). Counts only: no interval below 20 tickets."""
    groups: dict[str, list[int]] = {}
    for i, tag in enumerate(traps):
        for trap in tag.split("|"):
            groups.setdefault(trap, []).append(i)
    result = {}
    for trap, idx in sorted(groups.items()):
        sub_t, sub_r = [truths[i] for i in idx], [raws[i] for i in idx]
        preds = [parse_output(r) for r in sub_r]
        result[trap] = (
            len(idx),
            sum(desk_of(t) == desk_of(p) for t, p in zip(sub_t, preds)) / len(idx),
            sum(costs(sub_t, sub_r, weights)) / len(idx),
        )
    return result


def load_split(path: Path) -> tuple[list[str], list[TicketLabel], list[str]]:
    """Read an exported split CSV: ticket texts, labels (from ``target``) and trap tags."""
    csv.field_size_limit(10**7)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return (
        [r["ticket"] for r in rows],
        [TicketLabel(**json.loads(r["target"])) for r in rows],
        [r["traps"] for r in rows],
    )


def majority_counts(labels: Sequence[TicketLabel], field: str) -> Counter[str]:
    """Value counts of one field; B0 predicts the most common one."""
    return Counter(getattr(label, field) for label in labels)
