"""Compile a pipeline and submit it to Vertex AI: python scripts/pipeline_runner.py [training|sweep|base|compact|inference]."""

import argparse
import sys
from pathlib import Path

# Ensure the sub-project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import aiplatform
from kfp import compiler

from src.constants import GCP_PROJECT_ID, GCP_REGION, DATASET_URI, PIPELINE_ROOT
from src.pipelines.base_model_pipeline import base_model_pipeline
from src.pipelines.compact_variants_pipeline import compact_variants_pipeline
from src.pipelines.hyperparameter_sweep_pipeline import hyperparameter_sweep_pipeline
from src.pipelines.inference_pipeline import inference_pipeline
from src.pipelines.model_training_pipeline import model_training_pipeline

PIPELINES = {
    "training": model_training_pipeline,
    "sweep": hyperparameter_sweep_pipeline,
    "base": base_model_pipeline,  # B3: the base model prompted, no fine-tuning
    "compact": compact_variants_pipeline,  # D-q8 and D-q4: merge, GGUF, quantise, predict on CPU
    "inference": inference_pipeline,  # D unquantized (with adapter) or B3 (without adapter) on GPU
}

parser = argparse.ArgumentParser()
parser.add_argument("pipeline", nargs="?", choices=PIPELINES, default="training")
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
    "--test-file", default="val.csv", help="split the pipeline predicts on"
)
parser.add_argument(
    "--adapter-uri", help="gs:// folder of the LoRA adapter (compact and inference pipelines)"
)
args = parser.parse_args()
if args.pipeline == "compact" and not args.adapter_uri:
    parser.error("--adapter-uri is required by the compact pipeline")

template_path = f"{args.pipeline}_pipeline.yaml"
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
display_name = (
    f"router-{args.pipeline}-pipeline"
    + split_tag
    + ("-smoke" if args.smoke else "")
    + ("-fp16" if args.fp16 else "")
    + (f"-{args.model_id.split('/')[-1]}" if args.model_id else "")
)

aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
aiplatform.PipelineJob(
    display_name=display_name,
    template_path=template_path,
    pipeline_root=PIPELINE_ROOT,
    parameter_values={"dataset_uri": DATASET_URI} | extra,
    # enable_caching=False
).submit()
