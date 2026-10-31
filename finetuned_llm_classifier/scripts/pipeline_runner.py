"""Compile a pipeline and submit it to Vertex AI: python scripts/pipeline_runner.py [training|sweep]."""

import argparse
import sys
from pathlib import Path

# Ensure the sub-project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import aiplatform
from kfp import compiler

from src.constants import GCP_PROJECT_ID, GCP_REGION, PIPELINE_ROOT, RAW_DATASET_URI
from src.pipelines.hyperparameter_sweep_pipeline import hyperparameter_sweep_pipeline
from src.pipelines.model_training_pipeline import model_training_pipeline

PIPELINES = {
    "training": model_training_pipeline,
    "sweep": hyperparameter_sweep_pipeline,
}

parser = argparse.ArgumentParser()
parser.add_argument("pipeline", nargs="?", choices=PIPELINES, default="training")
args = parser.parse_args()

template_path = f"{args.pipeline}_pipeline.yaml"
compiler.Compiler().compile(PIPELINES[args.pipeline], template_path)

aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
aiplatform.PipelineJob(
    display_name=f"router-{args.pipeline}-pipeline",
    template_path=template_path,
    pipeline_root=PIPELINE_ROOT,
    parameter_values={"input_path": RAW_DATASET_URI},
    # enable_caching=False
).submit()
