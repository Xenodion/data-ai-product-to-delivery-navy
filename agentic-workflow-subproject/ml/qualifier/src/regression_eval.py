"""Regression gate of the Qualifier on the 100 hand-labelled cases of the eval-set (issue #19).

Each case is a test triple: the ticket (input), its seven labelled fields (expected output) and the
checks of ``scoring.score`` (valid contract, desk, urgent ticket in a wrong desk, silent error).
The gate replays stored predictions, so CI needs no model: it fails when the predictions are stale
(prompt, schema, model or eval-set changed since they were produced) or when a metric crosses a
threshold of ``regression_thresholds.toml``. Thresholds live in that file, never in this code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ml.qualifier.src.dataset_build.schema import TicketLabel
from ml.qualifier.src.prompt import INSTRUCTION
from ml.qualifier.src.scoring import score

SUBPROJECT = Path(__file__).resolve().parents[3]
THRESHOLDS_PATH = Path(__file__).with_name("regression_thresholds.toml")
LABEL_FIELDS = ("intent", "sub_intent", "transaction_id", "amount", "currency", "urgency", "sentiment")
TICKET_PLACEHOLDER = "<<TICKET>>"


@dataclass(frozen=True)
class Triple:
    case_id: str
    ticket: str
    expected: TicketLabel


@dataclass
class GateReport:
    metrics: dict[str, float]
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_thresholds(path: Path = THRESHOLDS_PATH) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def resolve(relative: str) -> Path:
    """Paths in the thresholds file are relative to the sub-project folder."""
    return (SUBPROJECT / relative).resolve()


def load_triples(path: Path) -> list[Triple]:
    """Read the eval-set: one triple per row, labels validated against the output contract."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    triples = [
        Triple(
            case_id=row["id"],
            ticket=row["input_the_agent_receives"],
            expected=TicketLabel(**{name: row[f"label_{name}"] for name in LABEL_FIELDS}),
        )
        for row in rows
    ]
    ids = [triple.case_id for triple in triples]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate case ids in {path}")
    return triples


def prompt_template_sha(template_with_placeholder: str) -> str:
    return sha256_text(template_with_placeholder)


def repository_prompt_sha() -> str:
    """Hash of the repository prompt as the flow compiles it (`flow/qualifier.py` fallback)."""
    return prompt_template_sha(f"{INSTRUCTION}\n\nTicket:\n{TICKET_PLACEHOLDER}")


def schema_sha() -> str:
    return sha256_text(json.dumps(TicketLabel.model_json_schema(), sort_keys=True))


def runtime_settings(config_path: Path) -> dict[str, object]:
    """Qualifier settings of `flow/config.toml` that change its answers (read as data, not imported)."""
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    return {
        "model_md5": config["qualifier_model_md5"],
        "model_version": config["qualifier_model_version"],
        "max_tokens": config["qualifier_max_tokens"],
        "temperature": config["qualifier_temperature"],
    }


def expected_fingerprint(eval_set: Path, config_path: Path) -> dict[str, object]:
    """What the stored predictions must have been produced with to still be valid."""
    return {
        "eval_set_sha256": sha256_file(eval_set),
        "prompt_sha256": repository_prompt_sha(),
        "schema_sha256": schema_sha(),
        **runtime_settings(config_path),
    }


def load_predictions(path: Path) -> dict[str, str | None]:
    """Raw Qualifier output per case id; an empty cell is a missing answer (unavailable)."""
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["id"]: (row["raw_output"] or None) for row in csv.DictReader(handle)}


def stale_reasons(manifest: dict, expected: dict) -> list[str]:
    return [
        f"{key}: predictions made with {manifest.get(key)!r}, repository now has {value!r}"
        for key, value in expected.items()
        if manifest.get(key) != value
    ]


def check_thresholds(metrics: dict[str, float], thresholds: dict) -> list[str]:
    failures = []
    for name, bound in thresholds.get("min", {}).items():
        if metrics[name] < bound:
            failures.append(f"{name} = {metrics[name]:.4f} is below the minimum {bound}")
    for name, bound in thresholds.get("max", {}).items():
        if metrics[name] > bound:
            failures.append(f"{name} = {metrics[name]:.4f} is above the maximum {bound}")
    return failures


def run_gate(
    triples: list[Triple],
    predictions: dict[str, str | None],
    manifest: dict,
    expected: dict,
    thresholds: dict,
) -> GateReport:
    """Score the stored predictions and list every reason the gate fails."""
    missing = [t.case_id for t in triples if t.case_id not in predictions]
    extra = sorted(set(predictions) - {t.case_id for t in triples})
    metrics = score([t.expected for t in triples], [predictions.get(t.case_id) for t in triples])
    failures = [f"stale predictions, rerun `python -m flow.regression_predict`: {reason}"
                for reason in stale_reasons(manifest, expected)]
    if missing:
        failures.append(f"{len(missing)} cases have no prediction, e.g. {missing[:3]}")
    if extra:
        failures.append(f"{len(extra)} predictions match no case, e.g. {extra[:3]}")
    failures += check_thresholds(metrics, thresholds)
    return GateReport(metrics=metrics, failures=failures)
