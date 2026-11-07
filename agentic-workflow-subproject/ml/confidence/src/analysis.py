"""Joins the token probabilities of the replay to the labels and simulates a rejection threshold.

A ticket is "deferred" when its lowest probability among the chosen fields is under the threshold:
it would go to the Re-router with the flag UNCONFIDENT instead of to a desk. The simulation reports what
remains among the tickets still handled automatically. It does not assume a person fixes a deferred ticket.
"""

import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from ml.confidence.src.signals import FieldSignal, field_signal
from ml.qualifier.src.dataset_build.schema import TicketLabel
from ml.qualifier.src.scoring import desk_of, is_routed, is_silent_error, parse_output

SIGNAL_FIELDS = ("intent", "sub_intent", "urgency", "transaction_id", "amount", "currency")


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def build_frame(replay: Path, truths: Sequence[TicketLabel], fields: Sequence[str] = SIGNAL_FIELDS) -> pd.DataFrame:
    """One row per replayed ticket: probabilities per field and the outcome against the label."""
    rows = []
    for record in _read(replay):
        truth = truths[record["row"]]
        pred = parse_output(record["text"])
        signals: dict[str, FieldSignal | None] = {
            f: field_signal(
                record["text"], record["text_offset"], record["tokens"],
                record["token_logprobs"], record["top_logprobs"], f,
            )
            for f in fields
        }
        row = {
            "row": record["row"],
            "text": record["text"],
            "valid": pred is not None,
            "routed": is_routed(pred),
            "silent": is_silent_error(truth, pred),
            "urgent": truth.urgency == "high",
            "urgent_wrong_desk": truth.urgency == "high" and is_routed(pred) and desk_of(pred) != desk_of(truth),
            "needless_triage": not is_routed(pred) and desk_of(truth) != "triage",
        }
        for f, signal in signals.items():
            row[f"p_{f}"] = signal.p_value if signal else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def with_score(frame: pd.DataFrame, fields: Sequence[str]) -> pd.Series:
    """Lowest probability among `fields`; a missing field (absent value) does not count."""
    return frame[[f"p_{f}" for f in fields]].min(axis=1, skipna=True).fillna(1.0)


def deferral_curve(frame: pd.DataFrame, score: pd.Series, thresholds: Sequence[float]) -> pd.DataFrame:
    """For each threshold: deferred tickets and what is left among the automatically routed ones."""
    out = []
    n = len(frame)
    for t in thresholds:
        deferred = (score < t) & frame["routed"]
        auto = frame["routed"] & ~deferred
        out.append({
            "threshold": t,
            "deferred": int(deferred.sum()),
            "deferred_pct": 100 * deferred.sum() / n,
            "deferred_that_were_right": int((deferred & ~frame["silent"]).sum()),
            "silent_left": int((frame["silent"] & ~deferred).sum()),
            "silent_per_100": 100 * (frame["silent"] & ~deferred).sum() / n,
            "urgent_wrong_desk_left": int((frame["urgent_wrong_desk"] & ~deferred).sum()),
            "auto_routed_pct": 100 * auto.sum() / n,
        })
    return pd.DataFrame(out)
