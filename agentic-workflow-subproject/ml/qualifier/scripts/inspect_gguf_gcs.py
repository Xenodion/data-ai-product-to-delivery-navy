"""Compare GCS metadata for two GGUF files without downloading their model bytes."""

from __future__ import annotations

import argparse
import base64
import json
from urllib.parse import urlparse


def object_metadata(uri: str) -> dict[str, object]:
    from google.cloud import storage

    parsed = urlparse(uri)
    if parsed.scheme != "gs" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Expected a gs://bucket/object URI, got: {uri}")
    blob = storage.Client().bucket(parsed.netloc).blob(parsed.path.lstrip("/"))
    blob.reload()
    md5_hex = base64.b64decode(blob.md5_hash).hex() if blob.md5_hash else None
    return {
        "uri": uri,
        "generation": str(blob.generation) if blob.generation else None,
        "size_bytes": blob.size,
        "md5_hex": md5_hex,
        "md5_base64": blob.md5_hash,
        "crc32c_base64": blob.crc32c,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_natural_uri", help="GCS URI of test_natural run's model-q4.gguf")
    parser.add_argument("test_traps_uri", help="GCS URI of test_traps run's model-q4.gguf")
    args = parser.parse_args()

    natural = object_metadata(args.test_natural_uri)
    traps = object_metadata(args.test_traps_uri)
    same_md5 = bool(natural["md5_hex"]) and natural["md5_hex"] == traps["md5_hex"]
    print(
        json.dumps(
            {
                "test_natural": natural,
                "test_traps": traps,
                "same_md5": same_md5,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
