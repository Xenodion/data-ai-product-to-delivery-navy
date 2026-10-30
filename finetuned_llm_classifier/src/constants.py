import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GCP_REGION = os.environ["GCP_REGION"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]
