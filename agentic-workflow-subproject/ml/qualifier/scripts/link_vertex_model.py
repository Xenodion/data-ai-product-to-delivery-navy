"""Record a Vertex Model Registry version/alias against its source MLflow run.

This command writes only to MLflow and a local receipt file. It does not call
Vertex or change model aliases. Read the immutable resource/version and alias
target from the Vertex console or an approved export before invoking it.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.qualifier.src.tracking import _mlflow, git_provenance, log_record

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="source MLflow evaluation/training run ID")
    parser.add_argument("--system-id", required=True, help="system ID such as D-q4")
    parser.add_argument("--model-resource", required=True, help="immutable Vertex model resource name/version")
    parser.add_argument("--alias", required=True, help="alias and immutable target snapshot read from Vertex")
    parser.add_argument("--artifact-uri", default="unknown", help="immutable artifact URI or storage reference")
    parser.add_argument("--artifact-sha256", default="unknown", help="artifact checksum, if available")
    args = parser.parse_args()
    if "@" not in args.model_resource and "/versions/" not in args.model_resource:
        parser.error("--model-resource must identify an immutable Vertex model version")

    mlflow, client = _mlflow()
    source = client.get_run(args.run_id)
    if source.data.tags.get("system_id") != args.system_id:
        parser.error("--system-id must match the source run's system_id tag")

    receipt = {
        "source_mlflow_run_id": args.run_id,
        "system_id": args.system_id,
        "vertex_model_resource": args.model_resource,
        "alias_snapshot": args.alias,
        "artifact_uri": args.artifact_uri,
        "artifact_sha256": args.artifact_sha256,
        "source_prediction_sha256": source.data.tags.get("source_sha256", "unknown"),
        "dataset_revision": source.data.tags.get("dataset_revision", "unknown"),
        "scorer_version": source.data.tags.get("scorer_version", "unknown"),
        "vertex_pipeline_job_id": source.data.tags.get("vertex_pipeline_job_id", "unknown"),
    }
    receipt_dir = ROOT / "logs" / "vertex_registry_links"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_key = hashlib.sha256(f"{args.run_id}:{args.model_resource}:{args.alias}".encode()).hexdigest()[:16]
    receipt_path = receipt_dir / f"{args.system_id}-{receipt_key}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    tracking_key = f"vertex-registration:{args.model_resource}:{args.run_id}:{args.alias}"
    run_id, created = log_record(
        run_name=f"qualifier-registration-{args.system_id}-{args.model_resource.rsplit('/', 1)[-1]}",
        run_type="registration_link",
        tracking_key=tracking_key,
        parent_run_id=args.run_id,
        tags={
            **git_provenance(ROOT),
            "project": "navy-qualifier",
            "system_id": args.system_id,
            "split": "registry",
            "stage": "registration",
            "tracking_origin": "local",
            "selection_status": source.data.tags.get("selection_status", "unknown"),
            "vertex_model_resource": args.model_resource,
            "vertex_alias_snapshot": args.alias,
        },
        params={
            "source_mlflow_run_id": args.run_id,
            "artifact_uri": args.artifact_uri,
            "artifact_sha256": args.artifact_sha256,
        },
        artifacts=[{"path": str(receipt_path), "artifact_path": "registry"}],
    )
    print(json.dumps({"registration_link_run_id": run_id, "created": created, "receipt": str(receipt_path)}, indent=2))


if __name__ == "__main__":
    main()
