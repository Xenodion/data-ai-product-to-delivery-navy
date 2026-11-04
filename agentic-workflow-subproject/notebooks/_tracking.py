"""Notebook-side MLflow result access with explicit legacy-file fallback."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import socket
import urllib.parse
from typing import Any

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "navy-qualifier")

_MLFLOW_ONLINE: bool | None = None
_EXPERIMENT_CACHE: Any = None
_PREDICTION_CACHE: dict[tuple[str, str], list[str] | None] = {}
_RUN_SEARCH_CACHE: dict[tuple[str, str, int | None], Any] = {}


def _warn_mlflow_offline(uri: str, timeout: float) -> None:
    """Print a prominent and actionable banner when MLflow server is offline."""
    banner = (
        "\n" + "=" * 74 + "\n"
        f"[!] MLFLOW TRACKING NOTICE: Server unreachable at: {uri}\n"
        f"    (Connectivity check timed out in {timeout}s to prevent notebook freeze)\n\n"
        "    -> Local fallback active: reading predictions and metrics directly\n"
        "       from local CSV files in `docs/results/`.\n\n"
        "    INFO: To start the local MLflow server and enable live tracking:\n"
        "       1. Open a separate terminal\n"
        "       2. Run: mlflow server --host 127.0.0.1 --port 5000\n"
        "          (or: uv run mlflow server --port 5000)\n"
        + "=" * 74 + "\n"
    )
    print(banner)


def _is_mlflow_available(uri: str, timeout: float = 0.1) -> bool:
    """Quickly test whether the MLflow tracking URI is reachable."""
    global _MLFLOW_ONLINE
    if _MLFLOW_ONLINE is not None:
        return _MLFLOW_ONLINE

    if not uri or uri.strip() == "":
        _MLFLOW_ONLINE = False
        return False

    try:
        parsed = urllib.parse.urlparse(uri)
        if parsed.scheme in ("http", "https"):
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
            _MLFLOW_ONLINE = True
        elif parsed.scheme in ("file", "") or Path(uri).is_dir():
            _MLFLOW_ONLINE = True
        else:
            _MLFLOW_ONLINE = False
    except Exception:
        _MLFLOW_ONLINE = False
        _warn_mlflow_offline(uri, timeout)

    return _MLFLOW_ONLINE


def _client():
    global _EXPERIMENT_CACHE
    if not _is_mlflow_available(TRACKING_URI):
        return None, None

    try:
        import mlflow
        from mlflow import MlflowClient

        mlflow.set_tracking_uri(TRACKING_URI)
        client = MlflowClient(tracking_uri=TRACKING_URI)
        if _EXPERIMENT_CACHE is None:
            _EXPERIMENT_CACHE = client.get_experiment_by_name(EXPERIMENT_NAME)
        return client, _EXPERIMENT_CACHE
    except Exception as exc:
        print(f"[Tracking] MLflow client error ({type(exc).__name__}); using local fallback")
        return None, None


def find_evaluation(system_id: str, split: str, expected_n: int | None = None):
    """Return the newest tracked result for one system/split, or None."""
    cache_key = (system_id, split, expected_n)
    if cache_key in _RUN_SEARCH_CACHE:
        return _RUN_SEARCH_CACHE[cache_key], None

    if not _is_mlflow_available(TRACKING_URI):
        return None, None

    client, experiment = _client()
    if experiment is None:
        _RUN_SEARCH_CACHE[cache_key] = None
        return None, client

    runs = client.search_runs([experiment.experiment_id], max_results=1000)
    candidates = [
        run for run in runs
        if run.data.tags.get("project") == "navy-qualifier"
        and run.data.tags.get("system_id") == system_id
        and run.data.tags.get("split") == split
        and run.data.tags.get("run_type") == "evaluation"
        and (expected_n is None or run.data.metrics.get("evaluation_n") == expected_n)
    ]
    candidates.sort(key=lambda run: run.info.end_time or run.info.start_time, reverse=True)
    res = candidates[0] if candidates else None
    _RUN_SEARCH_CACHE[cache_key] = res
    return res, client


def load_predictions(
    root: Path,
    system_id: str,
    split: str,
    fallback_path: Path | None,
    expected_tickets: list[str],
) -> list[str] | None:
    """Load predictions from MLflow when available; use a labelled local fallback.

    A found tracked artifact with mismatched tickets is a hard error. Local CSV
    fallback is used only when no tracked run is available or MLflow is offline.
    Results are memoized in memory so subsequent calls in the same notebook are instant.
    """
    cache_key = (system_id, split)
    if cache_key in _PREDICTION_CACHE:
        return _PREDICTION_CACHE[cache_key]

    import pandas as pd

    tracked, client = None, None
    if _is_mlflow_available(TRACKING_URI):
        try:
            tracked, client = find_evaluation(system_id, split, len(expected_tickets))
        except Exception as exc:
            print(f"MLflow unavailable ({type(exc).__name__}); using local prediction fallback")

    if tracked is not None and client is not None:
        artifact_path = tracked.data.tags.get("prediction_artifact_path")
        if not artifact_path:
            raise ValueError(f"Tracked run {tracked.info.run_id} has no prediction_artifact_path tag")
        local_path = Path(client.download_artifacts(tracked.info.run_id, artifact_path))
        frame = pd.read_csv(local_path, keep_default_na=False)
        expected_hashes = [hashlib.sha256(ticket.encode("utf-8")).hexdigest() for ticket in expected_tickets]
        if "row_id_sha256" not in frame or list(frame["row_id_sha256"]) != expected_hashes:
            raise ValueError(f"Tracked {system_id}/{split} artifact does not match the current dataset order")
        print(f"Loaded {system_id}/{split} predictions from MLflow run {tracked.info.run_id}")
        res = list(frame["extracted_response"])
        _PREDICTION_CACHE[cache_key] = res
        return res

    if fallback_path is None or not fallback_path.is_file():
        _PREDICTION_CACHE[cache_key] = None
        return None

    frame = pd.read_csv(fallback_path, keep_default_na=False)
    if len(frame) != len(expected_tickets) or list(frame["user_input"]) != list(expected_tickets):
        raise ValueError(f"Local fallback {fallback_path} does not match every {split} row in order")
    print(f"Using local historical prediction file: {fallback_path.relative_to(root)}")
    res = list(frame["extracted_response"])
    _PREDICTION_CACHE[cache_key] = res
    return res


def has_predictions(root: Path, system_id: str, split: str, fallback_path: Path | None, expected_n: int) -> bool:
    """Check if a full-split run or a local fallback exists for notebook selection."""
    if (system_id, split) in _PREDICTION_CACHE:
        return _PREDICTION_CACHE[(system_id, split)] is not None

    if _is_mlflow_available(TRACKING_URI):
        try:
            run, _ = find_evaluation(system_id, split, expected_n)
            if run is not None:
                return True
        except Exception:
            pass

    return fallback_path is not None and fallback_path.is_file()


def load_training_history(root: Path, fallback_path: Path):
    """Load D's training history artifact from MLflow, or the committed JSON file."""
    if _is_mlflow_available(TRACKING_URI):
        try:
            run, client = find_evaluation("D", "val")
            if run is not None and client is not None:
                local_path = Path(client.download_artifacts(run.info.run_id, "training/d_qwen2.5-3b_full_run_log_history.json"))
                print(f"Loaded training history from MLflow run {run.info.run_id}")
                return local_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"MLflow training artifact unavailable ({type(exc).__name__}); using local JSON fallback")
    return fallback_path.read_text(encoding="utf-8")
