"""Download the probabilities of a finished Vertex confidence job into `.local/runs/confidence/<split>.jsonl`.

Run from the subproject root, with the job id (the timestamp at the end of the pipeline job name):
    uv run python -m ml.confidence.scripts.fetch_signals test_natural 20261107094752
"""

import argparse

from google.cloud import storage

from ml.qualifier.src.constants import GCP_BUCKET_NAME, GCP_PROJECT_ID
from ml.qualifier.src.local_paths import RUNS_DIR

PIPELINE_NAME = "keelpay-router-confidence-signals-pipeline"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=["val", "test_natural", "test_traps"])
    parser.add_argument("job_id", help="timestamp at the end of the Vertex job name, e.g. 20261107094752")
    args = parser.parse_args()
    client = storage.Client(project=GCP_PROJECT_ID)
    prefix = f"pipeline_root/158407666882/{PIPELINE_NAME}-{args.job_id}/"
    blobs = [b for b in client.list_blobs(GCP_BUCKET_NAME, prefix=prefix) if b.name.endswith("/signals")]
    if len(blobs) != 1:
        raise SystemExit(f"Expected one signals file under {prefix}, found {len(blobs)}: is the job finished?")
    out = RUNS_DIR / "confidence" / f"{args.split}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    blobs[0].download_to_filename(str(out))
    print(f"{blobs[0].name} -> {out}")


if __name__ == "__main__":
    main()
