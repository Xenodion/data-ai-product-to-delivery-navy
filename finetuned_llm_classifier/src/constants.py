import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GCP_REGION = os.environ["GCP_REGION"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]

RAW_DATASET_URI = f"gs://{GCP_BUCKET_NAME}/tickets_synthetic.csv"
PIPELINE_ROOT = f"gs://{GCP_BUCKET_NAME}/pipeline_root"
