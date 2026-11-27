"""Compile and submit the KFP-native D-q4 registration/deployment pipelines."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from kfp import compiler
from google.cloud import aiplatform

from ml.qualifier.src.constants import GCP_PROJECT_ID, GCP_PROJECT_NUMBER, GCP_REGION, PIPELINE_ROOT
from ml.qualifier.src.local_paths import LOGS_DIR, PIPELINES_DIR
from ml.qualifier.src.pipelines.dq4_promotion_pipeline import (
    dq4_deployment_pipeline,
    dq4_promotion_pipeline,
    dq4_undeployment_pipeline,
)

# Google's prebuilt Hugging Face inference image, the one every Registry model of the course uses.
HF_SERVING_IMAGE = (
    "us-docker.pkg.dev/deeplearning-platform-release/gcr.io/"
    "huggingface-pytorch-inference-cu121.2-3.transformers.4-46.ubuntu2204.py311"
)
HANDLER_PATH = ROOT / "ml" / "qualifier" / "src" / "dq4_handler.py"


def _upload_handler(serving_dir_uri: str) -> None:
    """Upload handler.py to the serving directory; the pipeline builds the wheel and copies the GGUF."""
    from google.cloud import storage

    bucket_name, _, prefix = serving_dir_uri.removeprefix("gs://").rstrip("/").partition("/")
    bucket = storage.Client(project=GCP_PROJECT_ID).bucket(bucket_name)
    bucket.blob(f"{prefix}/handler.py").upload_from_filename(str(HANDLER_PATH))
    print(f"Uploaded handler.py to {serving_dir_uri}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("compile", help="compile all three KFP templates locally without contacting Vertex")

    register = commands.add_parser(
        "register", help="verify the GCS checksum and register a distinct D-q4 GGUF model"
    )
    register.add_argument("--gguf-artifact-uri", required=True, help="GCS directory of the KFP gguf_q4 artifact")
    register.add_argument("--gguf-file-uri", required=True, help="GCS URI of the contained model-q4.gguf object")
    register.add_argument("--expected-md5-hex", required=True, help="reviewed 32-character GCS object MD5")
    register.add_argument("--source-pipeline-run", required=True, help="full compact KFP run name")
    register.add_argument("--source-artifact-id", required=True, help="ML Metadata artifact ID from the compact run")
    register.add_argument("--source-adapter-uri", required=True, help="effective adapter_uri parameter from the compact run")
    register.add_argument(
        "--serving-dir-uri", required=True,
        help="new gs:// directory that will hold handler.py, the wheel and the GGUF (the Registry artifact)",
    )
    register.add_argument("--display-name", default="navy-team-keelpay-router-json")
    register.add_argument(
        "--parent-model", default="",
        help="projects/.../models/ID to add a new version to; empty creates a new model",
    )
    register.add_argument("--version-aliases", default="d-q4-gguf,champion", help="comma-separated aliases to move")
    register.add_argument("--confirm-billable-run", action="store_true")

    deploy = commands.add_parser("deploy", help="deploy an exact Registry model version to a fresh Vertex endpoint")
    deploy.add_argument("--model-versioned-resource-name", required=True, help="projects/.../models/MODEL_ID@VERSION_ID")
    deploy.add_argument("--endpoint-display-name", default="navy-team-keelpay-router")
    deploy.add_argument("--endpoint-resource-name", default="", help="reuse an empty endpoint returned by an earlier run")
    deploy.add_argument("--machine-type", required=True)
    deploy.add_argument("--confirm-billable-run", action="store_true")
    deploy.add_argument("--confirm-billable-deploy", action="store_true")

    undeploy = commands.add_parser("undeploy", help="release the expected D-q4 model replica from an endpoint")
    undeploy.add_argument("--endpoint-resource-name", required=True, help="full projects/.../endpoints/... resource name")
    undeploy.add_argument("--expected-model-versioned-resource-name", required=True, help="exact model version allowed to be removed")
    undeploy.add_argument("--confirm-billable-run", action="store_true")
    return parser


def _pipeline_for(args: argparse.Namespace):
    if args.command == "register":
        return dq4_promotion_pipeline, {
            "project": GCP_PROJECT_ID,
            "region": GCP_REGION,
            "gguf_artifact_uri": args.gguf_artifact_uri,
            "gguf_file_uri": args.gguf_file_uri,
            "expected_md5_hex": args.expected_md5_hex,
            "source_pipeline_run": args.source_pipeline_run,
            "source_artifact_id": args.source_artifact_id,
            "source_adapter_uri": args.source_adapter_uri,
            "serving_dir_uri": args.serving_dir_uri,
            "serving_image_uri": HF_SERVING_IMAGE,
            "display_name": args.display_name,
            "parent_model": args.parent_model,
            "version_aliases": args.version_aliases,
        }
    if args.command == "deploy":
        return dq4_deployment_pipeline, {
            "project": GCP_PROJECT_ID,
            "project_number": GCP_PROJECT_NUMBER,
            "region": GCP_REGION,
            "model_versioned_resource_name": args.model_versioned_resource_name,
            "endpoint_display_name": args.endpoint_display_name,
            "machine_type": args.machine_type,
            "endpoint_resource_name": args.endpoint_resource_name,
        }
    return dq4_undeployment_pipeline, {
        "project": GCP_PROJECT_ID,
        "project_number": GCP_PROJECT_NUMBER,
        "region": GCP_REGION,
        "endpoint_resource_name": args.endpoint_resource_name,
        "expected_model_versioned_resource_name": args.expected_model_versioned_resource_name,
    }


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    if args.command == "compile":
        PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
        for stage, pipeline_func in (
            ("register", dq4_promotion_pipeline),
            ("deploy", dq4_deployment_pipeline),
            ("undeploy", dq4_undeployment_pipeline),
        ):
            template_path = PIPELINES_DIR / f"dq4_{stage}_pipeline.yaml"
            compiler.Compiler().compile(pipeline_func=pipeline_func, package_path=str(template_path))
            print(f"Compiled local KFP template: {template_path}")
        return

    if not args.confirm_billable_run:
        parser.error("Submitting a Vertex pipeline can incur charges; pass --confirm-billable-run")
    if args.command == "deploy" and not args.confirm_billable_deploy:
        parser.error("Deploying inference replicas is billable; pass --confirm-billable-deploy")
    if args.command in {"deploy", "undeploy"} and not GCP_PROJECT_NUMBER:
        parser.error("Set GCP_PROJECT_NUMBER to the number that belongs to GCP_PROJECT_ID")
    if args.command == "register":
        try:
            if len(args.expected_md5_hex) != 32:
                raise ValueError
            bytes.fromhex(args.expected_md5_hex)
        except ValueError:
            parser.error("--expected-md5-hex must contain 32 hexadecimal characters")
        if not args.serving_dir_uri.startswith("gs://"):
            parser.error("--serving-dir-uri must be a gs:// directory")
        _upload_handler(args.serving_dir_uri)

    pipeline_func, parameters = _pipeline_for(args)
    stage = args.command
    tracking_id = uuid.uuid4().hex[:12]
    display_name = f"keelpay-dq4-{stage}-{tracking_id}"
    PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
    template_path = PIPELINES_DIR / f"dq4_{stage}_pipeline.yaml"
    compiler.Compiler().compile(pipeline_func=pipeline_func, package_path=str(template_path))

    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    pipeline_job = aiplatform.PipelineJob(
        display_name=display_name,
        template_path=str(template_path),
        pipeline_root=PIPELINE_ROOT,
        parameter_values=parameters,
        labels={"tracking_id": tracking_id, "project": "navy-qualifier", "stage": stage},
        enable_caching=False,
    )
    pipeline_job.submit()

    receipt = {
        "tracking_id": tracking_id,
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": stage,
        "pipeline_job_resource": getattr(pipeline_job, "resource_name", None),
        "project": GCP_PROJECT_ID,
        "region": GCP_REGION,
        "pipeline_root": PIPELINE_ROOT,
        "template_path": str(template_path.resolve()),
        "template_sha256": hashlib.sha256(template_path.read_bytes()).hexdigest(),
        "parameters": parameters,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
    }
    receipt_dir = LOGS_DIR / "vertex_submissions"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"dq4-{stage}-{tracking_id}.json"
    import json

    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Vertex pipeline submitted. Resource: {receipt['pipeline_job_resource']}")
    print(f"Local correlation receipt: {receipt_path}")


if __name__ == "__main__":
    main()
