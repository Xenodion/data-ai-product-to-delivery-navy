"""Smoke test for the GCP setup: Vertex AI init + GCS bucket access."""

import os

from dotenv import load_dotenv
from google.cloud import aiplatform, storage

load_dotenv()

project_id = os.getenv("GCP_PROJECT_ID")
region = os.getenv("GCP_REGION")
bucket_name = os.getenv("GCP_BUCKET_NAME")
assert project_id and region and bucket_name, "Missing GCP_* variables in .env"

aiplatform.init(project=project_id, location=region)
print(f"Vertex AI initialised: project={project_id}, location={region}")

client = storage.Client(project=project_id)
blobs = list(client.bucket(bucket_name).list_blobs(max_results=20))
print(f"Bucket gs://{bucket_name}: {len(blobs)} object(s)")
for blob in blobs:
    print(f"  - {blob.name}")
