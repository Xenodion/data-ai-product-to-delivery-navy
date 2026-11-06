"""Create an offline, immutable-input manifest before a B3 Vertex campaign.

This command is local-only: it does not contact Google Cloud or submit jobs.
Run from the subproject root with `uv run python ml/qualifier/scripts/prepare_b3_campaign.py <id>`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_ROWS = {"val": 293, "test_natural": 610, "test_traps": 380}
SPLIT_FILES = {name: ROOT / "data" / "dataset" / f"{name}.csv" for name in EXPECTED_ROWS}
TRAIN_FILE = ROOT / "data" / "dataset" / "train.csv"
SOURCE_FILES = {
    "prompt": ROOT / "ml" / "qualifier" / "src" / "prompt.py",
    "inference_component": ROOT / "ml" / "qualifier" / "src" / "pipeline_components" / "inference_component.py",
    "base_pipeline": ROOT / "ml" / "qualifier" / "src" / "pipelines" / "base_model_pipeline.py",
    "data_transformation": ROOT / "ml" / "qualifier" / "src" / "pipeline_components" / "data_transformation_component.py",
    "compiled_template": ROOT / ".local" / "pipelines" / "base_pipeline.yaml",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_records(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        next(reader, None)
        return sum(1 for _ in reader)


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_id", help="short immutable campaign label, e.g. b3-2026-11-04-a")
    args = parser.parse_args()
    campaign_id = args.campaign_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", campaign_id):
        parser.error("campaign_id must be 1-64 letters, digits, dots, underscores, or hyphens")

    missing = [str(path.relative_to(ROOT)) for path in [*SPLIT_FILES.values(), TRAIN_FILE, *SOURCE_FILES.values()] if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required campaign inputs are missing: " + ", ".join(missing))

    splits = {}
    mismatches = []
    for name, path in SPLIT_FILES.items():
        rows = csv_records(path)
        splits[name] = {"path": str(path.relative_to(ROOT)), "rows": rows, "sha256": sha256(path)}
        if rows != EXPECTED_ROWS[name]:
            mismatches.append(f"{name}: expected {EXPECTED_ROWS[name]}, found {rows}")
    if mismatches:
        raise ValueError("Frozen split row-count check failed: " + "; ".join(mismatches))

    git_status = git_value("status", "--porcelain")
    manifest = {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "prepared_local_only",
        "model": {
            "system_id": "B3",
            "model_id": "Qwen/Qwen2.5-3B-Instruct",
            "model_revision": "unknown",
            "adapter": None,
            "max_rows": 0,
            "max_new_tokens": 160,
            "do_sample": False,
            "quantization": "4-bit NF4",
            "compute_dtype": "float32",
        },
        "splits": splits,
        "pipeline_contract_train_input": {
            "path": str(TRAIN_FILE.relative_to(ROOT)),
            "rows": csv_records(TRAIN_FILE),
            "sha256": sha256(TRAIN_FILE),
            "used_for_inference": False,
        },
        "source_sha256": {name: sha256(path) for name, path in SOURCE_FILES.items()},
        "provenance": {
            "git_commit": git_value("rev-parse", "HEAD"),
            "git_dirty": bool(git_status),
            "git_status_sha256": hashlib.sha256(git_status.encode("utf-8")).hexdigest(),
        },
        "vertex": {
            "project": "not_configured",
            "region": "europe-west2",
            "pipeline_root_prefix": "gs://navy-team-llmops-bucket/pipeline_root/158407666882/",
            "remote_dataset_sha256_verified": False,
            "approved_budget_eur": None,
            "jobs": {},
        },
        "gate": "BLOCKED_UNTIL_REMOTE_DATA_AND_BUDGET_ARE_VERIFIED",
    }
    output = ROOT / "data" / "runs" / f"{campaign_id}_manifest.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing campaign manifest: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared local manifest: {output.relative_to(ROOT)}")
    print("No Vertex/GCS calls were made. Remote dataset identity and cost cap remain required gates.")


if __name__ == "__main__":
    main()
