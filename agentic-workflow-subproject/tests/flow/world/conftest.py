"""Fixtures of the world tests."""

from collections.abc import Callable
from pathlib import Path

import pytest
from world_test_factories import micro_rows, write_split_file

from flow.world.deck import SPLIT_NAMES


@pytest.fixture()
def write_deck(tmp_path: Path) -> Callable[[dict[str, int] | None], Path]:
    """Return a function writing a micro deck (four splits and a quarantine file)."""

    def _write(sizes: dict[str, int] | None = None) -> Path:
        counts = sizes or {"train": 40, "val": 20, "test_natural": 20, "test_traps": 20}
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        for split in SPLIT_NAMES:
            write_split_file(deck_dir / f"{split}.csv", micro_rows(split, counts[split]))
        (deck_dir / "train_quarantine.csv").write_bytes(b"\xff\xfe not a csv")
        return deck_dir

    return _write
