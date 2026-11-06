"""Prepares the local workspace: creates .local/ and fetches the Qualifier model with its checksum."""

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage

from flow.contracts import FlowConfig, load_config
from ml.qualifier.src.local_paths import LOCAL_FOLDERS, MODELS_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)

CHUNK_BYTES = 1 << 20


def create_local_dirs(folders: tuple[Path, ...] = LOCAL_FOLDERS) -> None:
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_model(path: Path, expected_md5: str) -> bool:
    return path.is_file() and file_md5(path) == expected_md5


def fetch_model(config: FlowConfig) -> Path:
    """Download the model unless a verified copy exists; refuse a corrupt download."""
    target = MODELS_DIR / config.qualifier_model_uri.rsplit("/", 1)[1]
    if has_model(target, config.qualifier_model_md5):
        logger.info("Model already present: %s", target)
        return target
    bucket, blob = config.qualifier_model_uri.removeprefix("gs://").split("/", 1)
    logger.info("Downloading the model, about 2 GB")
    client = storage.Client(project=os.environ.get("GCP_PROJECT_ID"))
    client.bucket(bucket).blob(blob).download_to_filename(str(target), timeout=1200)
    if not has_model(target, config.qualifier_model_md5):
        target.unlink()
        raise ValueError(f"checksum mismatch for {config.qualifier_model_uri}")
    logger.info("Model ready: %s", target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-model", action="store_true", help="only create the folders")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(PROJECT_ROOT / ".env")
    create_local_dirs()
    if args.skip_model:
        return 0
    try:
        fetch_model(load_config())
    except DefaultCredentialsError:
        logger.error("No Google credentials: run `gcloud auth application-default login`")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
