"""Compile a pipeline and submit it to Vertex AI: python scripts/pipeline_runner.py [training|sweep]."""

import argparse
import sys
from pathlib import Path

# Ensure the sub-project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import aiplatform
from kfp import compiler

from src.constants import GCP_PROJECT_ID, GCP_REGION, DATASET_URI, PIPELINE_ROOT
from src.pipelines.base_model_pipeline import base_model_pipeline
from src.pipelines.hyperparameter_sweep_pipeline import hyperparameter_sweep_pipeline
from src.pipelines.model_training_pipeline import model_training_pipeline

PIPELINES = {
    "training": model_training_pipeline,
    "sweep": hyperparameter_sweep_pipeline,
    "base": base_model_pipeline,  # B3: the base model prompted, no fine-tuning
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
    "--test-file", default="val.csv", help="split the training pipeline predicts on"
)
args = parser.parse_args()

template_path = f"{args.pipeline}_pipeline.yaml"
compiler.Compiler().compile(PIPELINES[args.pipeline], template_path)

extra = {} if args.pipeline == "sweep" else {"test_file": args.test_file}
if args.smoke and args.pipeline == "sweep":
    parser.error("--smoke applies to the training and base pipelines, not the sweep")
if args.fp16 and args.pipeline == "training":
    extra |= {"compute_dtype": "float16"}
if args.smoke:
    # Calibration run: checks that everything loads, measures time and memory per step, and shows the first loss values
    extra |= {"max_rows": 20}
    if args.pipeline == "training":
        extra |= {"max_train_rows": 200, "max_steps": 40, "eval_steps": 20}
aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
aiplatform.PipelineJob(
    display_name=f"router-{args.pipeline}-pipeline"
    + ("-smoke" if args.smoke else "")
    + ("-fp16" if args.fp16 else ""),
    template_path=template_path,
    pipeline_root=PIPELINE_ROOT,
    parameter_values={"dataset_uri": DATASET_URI} | extra,
    # enable_caching=False
).submit()
