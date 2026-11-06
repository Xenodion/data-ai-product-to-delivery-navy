"""Upload the exported splits to gs://<bucket>/dataset/: python ml/qualifier/scripts/upload_dataset.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from google.cloud import storage

from ml.qualifier.src.constants import GCP_BUCKET_NAME, GCP_PROJECT_ID

SPLITS = ("train", "val", "test_natural", "test_traps")
DATASET_DIR = Path(__file__).resolve().parents[3] / "data" / "dataset"

bucket = storage.Client(project=GCP_PROJECT_ID).bucket(GCP_BUCKET_NAME)
for split in SPLITS:
    bucket.blob(f"dataset/{split}.csv").upload_from_filename(DATASET_DIR / f"{split}.csv")
    print(f"uploaded gs://{GCP_BUCKET_NAME}/dataset/{split}.csv")
