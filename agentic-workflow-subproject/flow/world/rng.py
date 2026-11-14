"""Independent, reproducible random streams, one per builder stage."""

import hashlib
import random


def stage_seed(seed: int, stage: str) -> int:
    """Derive a 64-bit stage seed from the world seed and the stage name.

    SHA-256 is used instead of the builtin ``hash()``, which is salted per process.
    Each stage owns its stream, so changing one stage never reshuffles another.
    """
    digest = hashlib.sha256(f"{seed}:{stage}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def stage_rng(seed: int, stage: str) -> random.Random:
    """Return a fresh generator for one stage."""
    return random.Random(stage_seed(seed, stage))
