"""Compile and submit an explicitly selected Vertex pipeline (requires --confirm-billable-run)."""

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure the sub-project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from google.cloud import aiplatform
from kfp import compiler

from ml.qualifier.src.local_paths import LOGS_DIR, PIPELINES_DIR
from ml.qualifier.src.constants import GCP_PROJECT_ID, GCP_REGION, DATASET_URI, PIPELINE_ROOT
from ml.qualifier.src.pipelines.base_model_pipeline import base_model_pipeline
from ml.qualifier.src.pipelines.compact_variants_pipeline import compact_variants_pipeline
from ml.qualifier.src.pipelines.hyperparameter_sweep_pipeline import hyperparameter_sweep_pipeline
from ml.qualifier.src.pipelines.inference_pipeline import inference_pipeline
from ml.qualifier.src.pipelines.model_training_pipeline import model_training_pipeline

PIPELINES = {
    "training": model_training_pipeline,
    "sweep": hyperparameter_sweep_pipeline,
    "base": base_model_pipeline,  # B3: the base model prompted, no fine-tuning
    "compact": compact_variants_pipeline,  # D-q8 and D-q4: merge, GGUF, quantise, predict on CPU
    "inference": inference_pipeline,  # D unquantized (with adapter) or B3 (without adapter) on GPU
}

parser = argparse.ArgumentParser()
parser.add_argument("pipeline", choices=PIPELINES, help="pipeline to compile and submit (must be explicit)")
parser.add_argument(
    "--confirm-billable-run",
    action="store_true",
    help="required acknowledgement that submitting a Vertex pipeline can incur charges",
)
parser.add_argument(
    "--smoke",
    action="store_true",
    help="very short run: 200 tickets, 40 steps, 20 predictions",
)
parser.add_argument(
    "--fp16",
    action="store_true",
    help="compute in float16 (faster on a T4, to check on a smoke run first)",
)
parser.add_argument(
    "--model-id",
    help="base model for the training and base pipelines (default: Qwen/Qwen2.5-3B-Instruct)",
)
parser.add_argument(
    "--test-file",
    choices=("val.csv", "test_natural.csv", "test_traps.csv"),
    default="val.csv",
    help="evaluation split; train.csv is intentionally excluded",
)
parser.add_argument(
    "--adapter-uri", help="gs:// folder of the LoRA adapter (compact and inference pipelines)"
)
args = parser.parse_args()
if not args.confirm_billable_run:
    parser.error("Vertex submission is billable; pass --confirm-billable-run after the campaign gates pass")
if args.pipeline == "compact" and not args.adapter_uri:
    parser.error("--adapter-uri is required by the compact pipeline")

PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
template_path = str(PIPELINES_DIR / f"{args.pipeline}_pipeline.yaml")
compiler.Compiler().compile(PIPELINES[args.pipeline], template_path)

extra = {} if args.pipeline == "sweep" else {"test_file": args.test_file}
if args.smoke and args.pipeline == "sweep":
    parser.error("--smoke applies to the training and base pipelines, not the sweep")
if args.model_id and args.pipeline != "sweep":
    extra |= {"model_id": args.model_id}
if args.adapter_uri and args.pipeline in ("compact", "inference"):
    extra |= {"adapter_uri": args.adapter_uri}
if args.fp16 and args.pipeline == "training":
    extra |= {"compute_dtype": "float16"}
if args.smoke:
    # Calibration run: checks that everything loads, measures time and memory per step, and shows the first loss values
    extra |= {"max_rows": 20}
    if args.pipeline == "training":
        extra |= {"max_train_rows": 200, "max_steps": 40, "eval_steps": 20}

split_tag = f"-{Path(args.test_file).stem}" if args.test_file != "val.csv" else ""
tracking_id = uuid.uuid4().hex[:12]
display_name = (
    f"router-{args.pipeline}-pipeline"
    + split_tag
    + ("-smoke" if args.smoke else "")
    + ("-fp16" if args.fp16 else "")
    + (f"-{args.model_id.split('/')[-1]}" if args.model_id else "")
    + f"-{tracking_id}"
)

aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
pipeline_job = aiplatform.PipelineJob(
    display_name=display_name,
    template_path=template_path,
    pipeline_root=PIPELINE_ROOT,
    parameter_values={"dataset_uri": DATASET_URI} | extra,
    labels={"tracking_id": tracking_id, "project": "navy-qualifier"},
    # enable_caching=False
)
pipeline_job.submit()

# This local receipt is the correlation source for a later offline MLflow sync.
# No MLflow or GCS request is made here; the pipeline submission above remains
# an explicitly billed Vertex operation when an operator chooses to run it.
submission = {
    "tracking_id": tracking_id,
    "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
    "display_name": display_name,
    "pipeline_name": args.pipeline,
    "pipeline_job_resource": getattr(pipeline_job, "resource_name", None),
    "project": GCP_PROJECT_ID,
    "region": GCP_REGION,
    "pipeline_root": PIPELINE_ROOT,
    "template_path": str(Path(template_path).resolve()),
    "template_sha256": hashlib.sha256(Path(template_path).read_bytes()).hexdigest(),
    "parameters": {"dataset_uri": DATASET_URI} | extra,
    "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "git_dirty": bool(subprocess.check_output(
        ["git", "status", "--porcelain"], text=True
    ).strip()),
}
receipt_dir = LOGS_DIR / "vertex_submissions"
receipt_dir.mkdir(parents=True, exist_ok=True)
receipt_path = receipt_dir / f"{tracking_id}.json"
receipt_path.write_text(json.dumps(submission, indent=2, default=str) + "\n", encoding="utf-8")
print(f"Vertex job submitted. Local correlation receipt: {receipt_path}")
