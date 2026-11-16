"""Hashes of the inputs of a build, so that a manifest explains why its content hash changed."""

import hashlib
import logging
import subprocess
from pathlib import Path

from flow.world.deck import SPLIT_NAMES

LOGGER = logging.getLogger(__name__)
UNKNOWN_VERSION = "unknown"
CONFIG_KEY = "config:world.toml"


def file_sha256(path: Path) -> str:
    """SHA-256 of a file with CRLF read as LF, so that the hash does not depend on the checkout."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def input_hashes(deck_dir: Path, config_path: Path) -> dict[str, str]:
    """Hash the four deck split files and the configuration file."""
    hashes = {f"deck:{split}.csv": file_sha256(deck_dir / f"{split}.csv") for split in SPLIT_NAMES}
    hashes[CONFIG_KEY] = file_sha256(config_path)
    return hashes


def code_version(root: Path) -> str:
    """Current git commit, recorded next to the manifest but outside its content hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        LOGGER.warning("code version unavailable: %s", error)
        return UNKNOWN_VERSION
    return result.stdout.strip()
