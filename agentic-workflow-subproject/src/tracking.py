"""Shared MLflow tracking contract for local scoring and Vertex result imports.

This module never contacts Vertex AI. Cloud runs are synchronized from a local
manifest exported/retrieved separately after the appropriate cost approval.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "navy-qualifier")
TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
TRACKING_SCHEMA_VERSION = "2"

# Canonical names used in comparisons. Values retain the scorer's original units:
# rates are proportions in [0, 1], not percentages.
METRIC_MAP = {
    "n": "evaluation_n",
    "urgent_wrong_desk": "urgent_wrong_desk_rate",
    "silent_error_rate": "silent_error_rate",
    "needless_triage_rate": "needless_triage_rate",
    "auto_routed_rate": "auto_routed_rate",
    "desk_accuracy": "desk_accuracy",
    "valid_json_rate": "valid_json_rate",
    "recall_high_urgency": "recall_high_urgency",
    "severity_score": "severity_score",
    "severity_score_urgent_doubled": "severity_score_urgent_doubled",
    "exact_transaction_id": "exact_transaction_id",
    "exact_amount": "exact_amount",
    "exact_currency": "exact_currency",
    "accuracy_urgency": "accuracy_urgency",
    "accuracy_sentiment": "accuracy_sentiment",
    "macro_f1_intent": "macro_f1_intent",
    "macro_f1_sub_intent": "macro_f1_sub_intent",
    "latency_mean_seconds": "latency_mean_seconds",
    "latency_median_seconds": "latency_median_seconds",
    "latency_p95_seconds": "latency_p95_seconds",
    "training_duration_seconds": "training_duration_seconds",
    "inference_duration_seconds": "inference_duration_seconds",
    "training_cost_eur": "training_cost_eur",
    "inference_cost_per_1000_eur": "inference_cost_per_1000_eur",
    "estimated_monthly_inference_cost_eur": "estimated_monthly_inference_cost_eur",
}


def _mlflow():
    try:
        import mlflow
        from mlflow import MlflowClient
    except ImportError as exc:  # pragma: no cover - depends on optional runtime setup
        raise RuntimeError(
            "MLflow is not installed in this environment. Run `uv sync` in "
            "finetuned_llm_classifier/ after the lockfile is regenerated."
        ) from exc
    mlflow.set_tracking_uri(TRACKING_URI)
    return mlflow, MlflowClient(tracking_uri=TRACKING_URI)


def git_provenance(root: Path | None = None) -> dict[str, str]:
    """Return source commit/dirty state, or explicit unknown values outside Git."""
    cwd = root or Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=cwd,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
        return {"git_commit": commit, "git_dirty": str(dirty).lower()}
    except (OSError, subprocess.CalledProcessError):
        return {"git_commit": "unknown", "git_dirty": "unknown"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_prediction_artifact(source_path: Path) -> Path:
    """Create a prediction artifact without copying ticket text or references."""
    import pandas as pd

    source_path = source_path.resolve()
    frame = pd.read_csv(source_path, keep_default_na=False)
    if "row_id_sha256" in frame and "extracted_response" in frame:
        return source_path
    if "user_input" not in frame or "extracted_response" not in frame:
        raise ValueError(f"Prediction source must contain user_input and extracted_response: {source_path}")
    safe = pd.DataFrame({
        "row_id_sha256": [hashlib.sha256(str(value).encode("utf-8")).hexdigest() for value in frame["user_input"]],
        "extracted_response": frame["extracted_response"],
    })
    if "valid_json" in frame:
        safe["valid_json"] = frame["valid_json"]
    destination_dir = PROJECT_ROOT / "logs" / "mlflow" / "sanitized_predictions"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{source_path.stem}-{sha256_file(source_path)[:12]}.csv"
    safe.to_csv(destination, index=False)
    return destination


def build_dataset_manifest(dataset_dir: Path) -> dict[str, Any]:
    """Fingerprint committed split CSVs without copying or uploading their contents."""
    import csv

    splits: dict[str, Any] = {}
    for path in sorted(dataset_dir.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            columns = next(reader, [])
            row_count = sum(1 for _ in reader)
        splits[path.name] = {
            "sha256": sha256_file(path),
            "rows": row_count,
            "columns": columns,
        }
    return {"manifest_version": 1, "splits": splits}


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _file_records(artifacts: list[dict[str, str]] | None) -> list[dict[str, str]]:
    records = []
    for item in artifacts or []:
        path = Path(item["path"]).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"MLflow artifact does not exist: {path}")
        records.append(
            {
                "path": str(path),
                "artifact_path": item.get("artifact_path", "artifacts"),
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size),
            }
        )
    return records


def _canonical_metrics(metrics: dict[str, Any]) -> tuple[dict[str, float], dict[str, Any]]:
    normalized: dict[str, float] = {}
    provenance: dict[str, Any] = {}
    for source_name, raw_value in metrics.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            provenance[source_name] = {"status": "unknown", "reason": "not_numeric"}
            continue
        target_name = METRIC_MAP.get(source_name, source_name)
        if not math.isfinite(value):
            provenance[source_name] = {
                "metric": target_name,
                "status": "unknown",
                "reason": "non_finite_value",
            }
            continue
        normalized[target_name] = value
        provenance[source_name] = {
            "metric": target_name,
            "value": value,
            "status": "measured",
        }
    return normalized, provenance


def _get_experiment(client, name: str) -> str:
    experiment = client.get_experiment_by_name(name)
    if experiment is None:
        return client.create_experiment(name)
    return experiment.experiment_id


def _find_by_key(client, experiment_id: str, key: str):
    # tracking_key values are SHA-256 hex strings, so no filter escaping is needed.
    matches = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"tags.tracking_key = '{key}'",
        max_results=10,
    )
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate MLflow runs already exist for tracking key {key}")
    return matches[0] if matches else None


def log_record(
    *,
    run_name: str,
    run_type: str,
    tags: dict[str, Any],
    params: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    metric_history: dict[str, list[tuple[int, float]]] | None = None,
    artifacts: list[dict[str, str]] | None = None,
    metric_evidence: dict[str, Any] | None = None,
    experiment_name: str = EXPERIMENT_NAME,
    tracking_key: str,
    parent_run_id: str | None = None,
) -> tuple[str, bool]:
    """Log a deterministic record once; reject changed payloads under an existing key.

    Returns `(run_id, created)`. Reconciliation does not append duplicate metric
    history: an unchanged payload is a no-op and a changed payload requires a new
    explicit tracking key/revision.
    """
    mlflow, client = _mlflow()
    experiment_id = _get_experiment(client, experiment_name)
    normalized_metrics, metric_provenance = _canonical_metrics(metrics or {})
    history = {
        str(name): [(int(step), float(value)) for step, value in points]
        for name, points in (metric_history or {}).items()
    }
    if any(step < 0 or not math.isfinite(value) for points in history.values() for step, value in points):
        raise ValueError("Metric history requires nonnegative steps and finite values")
    file_records = _file_records(artifacts)
    safe_tags = {str(k): str(v)[:500] for k, v in (tags or {}).items() if v is not None}
    safe_params = {str(k): str(v)[:500] for k, v in (params or {}).items() if v is not None}
    provenance = {
        "tracking_schema_version": TRACKING_SCHEMA_VERSION,
        "run_type": run_type,
        "tracking_key": tracking_key,
        "metrics": {**metric_provenance, **(metric_evidence or {})},
        "metric_history": {name: {"points": len(points), "first_step": points[0][0],
                                  "last_step": points[-1][0]} for name, points in history.items() if points},
        "artifacts": file_records,
    }
    payload_hash = _json_hash(
        {
            "run_name": run_name,
            "run_type": run_type,
            "tags": safe_tags,
            "params": safe_params,
            "metrics": normalized_metrics,
            "metric_history": history,
            "provenance": provenance,
            "parent_run_id": parent_run_id,
        }
    )
    run_key = hashlib.sha256(tracking_key.encode("utf-8")).hexdigest()
    existing = _find_by_key(client, experiment_id, run_key)
    if existing is not None:
        old_hash = existing.data.tags.get("sync_payload_sha256")
        if old_hash != payload_hash:
            raise RuntimeError(
                "Tracking key already exists with different content. Use a new explicit "
                "revision key; refusing to append duplicate MLflow metric history."
            )
        return existing.info.run_id, False

    run_tags = {
        "mlflow.runName": run_name,
        "tracking_key": run_key,
        "tracking_schema_version": TRACKING_SCHEMA_VERSION,
        "run_type": run_type,
        "tracking_origin": safe_tags.pop("tracking_origin", "local"),
        "sync_payload_sha256": payload_hash,
        **safe_tags,
    }
    if parent_run_id:
        run_tags["mlflow.parentRunId"] = parent_run_id
    run = client.create_run(experiment_id, tags=run_tags)
    run_id = run.info.run_id
    try:
        for name, value in safe_params.items():
            client.log_param(run_id, name, value)
        for name, value in normalized_metrics.items():
            client.log_metric(run_id, name, value, step=0)
        for name, points in history.items():
            for step, value in points:
                client.log_metric(run_id, name, value, step=step)
        client.log_dict(run_id, provenance, "provenance/metrics_and_artifacts.json")
        for item in file_records:
            client.log_artifact(run_id, item["path"], item["artifact_path"])
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    return run_id, True


def metric_summary_for_traps(trap_rows: dict[str, tuple[int, float, float]]) -> dict[str, float]:
    """Flatten the scorer's per-trap `(n, desk_accuracy, severity)` table."""
    metrics: dict[str, float] = {}
    for trap, (count, accuracy, severity) in trap_rows.items():
        slug = "".join(c.lower() if c.isalnum() else "_" for c in trap).strip("_")
        metrics[f"trap.{slug}.n"] = float(count)
        metrics[f"trap.{slug}.desk_accuracy"] = float(accuracy)
        metrics[f"trap.{slug}.severity_score"] = float(severity)
    return metrics


def log_evaluation(
    *,
    system_id: str,
    split: str,
    metrics: dict[str, Any],
    dataset_path: Path,
    source_path: Path,
    params: dict[str, Any] | None = None,
    stage: str = "historical",
    tracking_origin: str = "historical_import",
    model_id: str = "unknown",
    selection_status: str | None = None,
    extra_metrics: dict[str, Any] | None = None,
    metric_history: dict[str, list[tuple[int, float]]] | None = None,
    extra_params: dict[str, Any] | None = None,
    extra_artifacts: list[dict[str, str]] | None = None,
    metric_evidence: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    """Log a scoring result with source/data/code provenance and prediction artifact."""
    dataset_hash = sha256_file(dataset_path)
    source_hash = sha256_file(source_path)
    safe_source_path = _safe_prediction_artifact(source_path)
    provenance_tags = git_provenance(dataset_path.parent)
    return log_record(
        run_name=f"qualifier-{system_id}-evaluation-{split}-{source_hash[:8]}",
        run_type="evaluation",
        tracking_key=f"evaluation:v2:{system_id}:{split}:{source_hash}",
        tags={
            **provenance_tags,
            "project": "navy-qualifier",
            "system_id": system_id,
            "stage": stage,
            "split": split,
            "dataset_name": dataset_path.name,
            "dataset_revision": dataset_hash,
            "scoring_protocol_version": "2026-11-02",
            "scorer_version": provenance_tags["git_commit"],
            "model_id": model_id,
            "source_sha256": source_hash,
            "prediction_artifact_path": f"predictions/{safe_source_path.name}",
            "tracking_origin": tracking_origin,
            "selection_status": selection_status
            or ("reference" if system_id.startswith("B") else "candidate"),
        },
        params={**(params or {}), **(extra_params or {})},
        metrics={**metrics, **(extra_metrics or {})},
        metric_history=metric_history,
        artifacts=[
            {"path": str(safe_source_path), "artifact_path": "predictions"},
            *(extra_artifacts or []),
        ],
        metric_evidence=metric_evidence,
    )


def sync_vertex_manifest(manifest_path: Path) -> dict[str, Any]:
    """Synchronize a local export manifest; this function performs no cloud access."""
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Expected Vertex export manifest schema_version=1")
    vertex = manifest.get("vertex", {})
    job_id = vertex.get("pipeline_job_resource")
    if not job_id:
        raise ValueError("vertex.pipeline_job_resource is required")
    root = manifest_path.parent
    job_tags = {
        **git_provenance(root),
        "project": "navy-qualifier",
        "vertex_pipeline_job_id": job_id,
        "vertex_project": vertex.get("project", "unknown"),
        "vertex_region": vertex.get("region", "unknown"),
        "pipeline_name": vertex.get("pipeline_name", "unknown"),
        "pipeline_template_version": vertex.get("pipeline_template_version", "unknown"),
        "tracking_origin": "vertex",
    }
    parent_id, parent_created = log_record(
        run_name=vertex.get("display_name", f"vertex-{job_id.rsplit('/', 1)[-1]}"),
        run_type="pipeline",
        tracking_key=f"vertex-parent:{job_id}",
        tags=job_tags,
        params=manifest.get("parameters", {}),
        metrics=manifest.get("pipeline_metrics", {}),
        artifacts=[
            {"path": str((root / a["path"]).resolve()), "artifact_path": a.get("artifact_path", "vertex")}
            for a in manifest.get("artifacts", [])
        ],
        experiment_name=manifest.get("experiment_name", EXPERIMENT_NAME),
    )
    children = []
    for result in manifest.get("results", []):
        for required in ("system_id", "run_type", "split"):
            if not result.get(required):
                raise ValueError(f"Each result requires {required}")
        artifacts = [
            {"path": str((root / a["path"]).resolve()), "artifact_path": a.get("artifact_path", "artifacts")}
            for a in result.get("artifacts", [])
        ]
        child_id, created = log_record(
            run_name=result.get("run_name", f"{result['system_id']}-{result['run_type']}-{result['split']}"),
            run_type=result["run_type"],
            tracking_key=(
                f"vertex-child:{job_id}:{result.get('task_name', 'unknown')}:"
                f"{result['system_id']}:{result['split']}:{result['run_type']}"
            ),
            tags={**job_tags, **result.get("tags", {}), "system_id": result["system_id"], "split": result["split"]},
            params=result.get("params", {}),
            metrics=result.get("metrics", {}),
            artifacts=artifacts,
            metric_evidence=result.get("metric_evidence"),
            experiment_name=manifest.get("experiment_name", EXPERIMENT_NAME),
            parent_run_id=parent_id,
        )
        children.append({"run_id": child_id, "created": created, "system_id": result["system_id"], "split": result["split"]})
    return {"parent_run_id": parent_id, "parent_created": parent_created, "children": children}
