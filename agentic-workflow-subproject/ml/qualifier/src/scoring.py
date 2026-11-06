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

from ml.qualifier.src.dataset_build.schema import TicketLabel

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
class SeverityWeights:
    """Relative weights of the protocol's severity matrix (ASSUMPTION: points, not euros)."""

    triage: float = 1.0
    wrong_desk: float = 3.0
    wrong_reference: float = 5.0
    wrong_desk_urgent: float = 10.0


DEFAULT_WEIGHTS = SeverityWeights()


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


def ticket_severity(
    truth: TicketLabel,
    pred: TicketLabel | None,
    weights: SeverityWeights = DEFAULT_WEIGHTS,
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


def is_routed(pred: TicketLabel | None) -> bool:
    """True when the system sends the ticket to a real desk by itself (valid output, not triage)."""
    return pred is not None and desk_of(pred) != TRIAGE


def is_silent_error(truth: TicketLabel, pred: TicketLabel | None) -> bool:
    """A definite answer that is wrong: routed to a desk, with a wrong desk or a wrong reference field.

    Nothing flags it for a human, so it is the error that can reach the merchant unnoticed.
    """
    return is_routed(pred) and (
        desk_of(pred) != desk_of(truth)
        or any(getattr(pred, f) != getattr(truth, f) for f in REFERENCE_FIELDS)
    )


def is_needless_triage(truth: TicketLabel, pred: TicketLabel | None) -> bool:
    """Sent to a human (invalid output, ``OTHER`` or ``UNDEFINED``) although the label has a desk."""
    return not is_routed(pred) and desk_of(truth) != TRIAGE


def silent_errors(
    truths: Sequence[TicketLabel], raws: Sequence[str | None]
) -> list[float]:
    """Per-ticket silent-error flags (1.0 or 0.0), to feed ``paired_bootstrap`` or a per-trap rate."""
    return [float(is_silent_error(t, parse_output(r))) for t, r in zip(truths, raws)]


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
    weights: SeverityWeights = DEFAULT_WEIGHTS,
) -> dict[str, float]:
    """Metrics 1-10 of the protocol for one system on one set of tickets."""
    preds = [parse_output(r) for r in raws]
    pairs = list(zip(truths, preds))
    valid = [(t, p) for t, p in pairs if p]
    high = [(t, p) for t, p in pairs if t.urgency == "high"]
    doubled = SeverityWeights(
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
        "auto_routed_rate": _share(sum(is_routed(p) for _, p in pairs), len(pairs)),
        "silent_error_rate": _share(
            sum(is_silent_error(t, p) for t, p in pairs), len(pairs)
        ),
        "needless_triage_rate": _share(
            sum(is_needless_triage(t, p) for t, p in pairs), len(pairs)
        ),
        "recall_high_urgency": _share(
            sum(bool(p) and p.urgency == "high" for _, p in high), len(high)
        ),
        "severity_score": sum(ticket_severity(t, p, weights) for t, p in pairs)
        / len(pairs),
        "severity_score_urgent_doubled": sum(
            ticket_severity(t, p, doubled) for t, p in pairs
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


def severities(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    weights: SeverityWeights = DEFAULT_WEIGHTS,
) -> list[float]:
    """Per-ticket severity of one system, to feed ``paired_bootstrap``."""
    return [ticket_severity(t, parse_output(r), weights) for t, r in zip(truths, raws)]


def paired_bootstrap(
    values_a: Sequence[float],
    values_b: Sequence[float],
    resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Mean of ``a - b`` per ticket with its 95 % bootstrap interval, resampling the same tickets in both."""
    diffs = [a - b for a, b in zip(values_a, values_b)]
    rng = random.Random(seed)
    means = sorted(
        sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(resamples)
    )
    return (
        sum(diffs) / len(diffs),
        means[int(0.025 * resamples)],
        means[int(0.975 * resamples) - 1],
    )


def mean_interval(
    values: Sequence[float], resamples: int = 2000, seed: int = 0
) -> tuple[float, float, float]:
    """Mean of ``values`` with its 95 % bootstrap interval (same tickets resampled)."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(resamples))
    return (
        sum(values) / n,
        means[int(0.025 * resamples)],
        means[int(0.975 * resamples) - 1],
    )


def silent_by_trap(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    traps: Sequence[str],
) -> dict[str, tuple[int, float]]:
    """Per trap type: (tickets, silent error rate). Counts only: no interval below 20 tickets."""
    flags = silent_errors(truths, raws)
    groups: dict[str, list[float]] = {}
    for flag, tag in zip(flags, traps):
        for trap in tag.split("|"):
            groups.setdefault(trap, []).append(flag)
    return {k: (len(v), sum(v) / len(v)) for k, v in sorted(groups.items())}


def by_trap(
    truths: Sequence[TicketLabel],
    raws: Sequence[str | None],
    traps: Sequence[str],
    weights: SeverityWeights = DEFAULT_WEIGHTS,
) -> dict[str, tuple[int, float, float]]:
    """Per trap type: (tickets, desk accuracy, severity score). Counts only: no interval below 20 tickets."""
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
            sum(severities(sub_t, sub_r, weights)) / len(idx),
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
