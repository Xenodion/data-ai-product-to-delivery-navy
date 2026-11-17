import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
# Set alongside GCP_PROJECT_ID for Vertex resource-name validation.
GCP_PROJECT_NUMBER = os.environ.get("GCP_PROJECT_NUMBER", "")
GCP_REGION = os.environ["GCP_REGION"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]

DATASET_URI = f"gs://{GCP_BUCKET_NAME}/dataset"
PIPELINE_ROOT = f"gs://{GCP_BUCKET_NAME}/pipeline_root"
