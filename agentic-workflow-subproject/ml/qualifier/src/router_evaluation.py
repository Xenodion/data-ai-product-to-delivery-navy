"""Offline view of the initial Router decision; historical Qualifier scores stay unchanged.

This models only the validated label -> desk/Re-router and priority mapping. It
does not claim to evaluate lookup, drafting, human correction, or production risk.
"""

from collections.abc import Sequence

from ml.qualifier.src.dataset_build.schema import TicketLabel
from ml.qualifier.src.scoring import desk_of, parse_output, TRIAGE

DESKS = ("payments", "disputes", "technical", "compliance", TRIAGE)


def evaluate_router(truths: Sequence[TicketLabel], raws: Sequence[str | None]) -> dict:
    if len(truths) != len(raws):
        raise ValueError("Truth and prediction row counts differ")
    preds = [parse_output(raw) for raw in raws]
    pairs = list(zip(truths, preds))
    n = len(pairs)
    high = [(truth, pred) for truth, pred in pairs if truth.urgency == "high"]
    matrix = {
        expected: {actual: 0 for actual in DESKS} for expected in DESKS
    }
    for truth, pred in pairs:
        matrix[desk_of(truth)][desk_of(pred)] += 1
    counts = {
        "n": n,
        "high_n": len(high),
        "action_correct_n": sum(desk_of(t) == desk_of(p) for t, p in pairs),
        "auto_routed_n": sum(desk_of(p) != TRIAGE for _, p in pairs),
        "needless_rerouter_n": sum(desk_of(t) != TRIAGE and desk_of(p) == TRIAGE for t, p in pairs),
        "high_wrong_desk_n": sum(desk_of(p) not in (TRIAGE, desk_of(t)) for t, p in high),
        "high_missed_n": sum(p is None or p.urgency != "high" for _, p in high),
        "high_unknown_n": sum(p is None or p.urgency == "UNDEFINED" for _, p in high),
        "high_rerouter_n": sum(desk_of(p) == TRIAGE for _, p in high),
        "false_high_n": sum(t.urgency != "high" and p is not None and p.urgency == "high" for t, p in pairs),
    }
    rates = {
        "action_accuracy": counts["action_correct_n"] / n if n else None,
        "auto_routed_rate": counts["auto_routed_n"] / n if n else None,
        "needless_rerouter_rate": counts["needless_rerouter_n"] / n if n else None,
        "high_wrong_desk_rate": counts["high_wrong_desk_n"] / len(high) if high else None,
        "high_missed_rate": counts["high_missed_n"] / len(high) if high else None,
    }
    return {"counts": counts, "rates": rates, "action_matrix": matrix}
