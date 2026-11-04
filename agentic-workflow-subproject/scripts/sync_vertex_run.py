"""Synchronize a local manifest exported from a finished Vertex pipeline job.

This command reads only local JSON/files and talks to the configured MLflow
tracking URI. It does not call Vertex AI, list GCS objects, or download artifacts.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tracking import sync_vertex_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="local Vertex export manifest (schema version 1)")
    args = parser.parse_args()
    result = sync_vertex_manifest(args.manifest)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
