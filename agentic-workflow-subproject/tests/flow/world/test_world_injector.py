"""The injector can draw first-contact tickets from the world database."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from flow import inject_dataset
from flow.world.build import build_world
from flow.world.config import PROJECT_ROOT, SampleConfig, load_world_config
from flow.world.deck import load_deck

KNOWLEDGE = PROJECT_ROOT / "flow" / "fixtures" / "knowledge.json"


@pytest.fixture()
def database(write_deck: Callable[..., Path], tmp_path: Path) -> Path:
    config = load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=10, history=20, dev=6),
            "merchant_target": 9,
            "transactions_per_merchant": 8,
        }
    )
    path = tmp_path / "world.sqlite"
    build_world(load_deck(write_deck()), config, KNOWLEDGE, path)
    return path


def test_world_rows_are_dev_tickets_with_world_merchant_and_date(database: Path) -> None:
    rows = inject_dataset.select_rows("val", 3, 1, database)
    with sqlite3.connect(database) as conn:
        dev = {r[0]: r for r in conn.execute(
            "SELECT ticket_id, merchant_id, opened_at FROM tickets WHERE role = 'dev'"
        )}
    assert len(rows) == 3 and all(row["card_id"] in dev for row in rows)
    envelope = inject_dataset.build_envelope(rows[0], "val", "M-FALLBACK", 1, datetime.now(UTC))
    _, merchant_id, opened_at = dev[rows[0]["card_id"]]
    assert envelope["ticket_id"] == rows[0]["card_id"]
    assert envelope["merchant_id"] == merchant_id != "M-FALLBACK"
    assert envelope["created_at"] == opened_at
    assert "\r" not in envelope["body"]


def test_world_has_no_traps_split(database: Path) -> None:
    with pytest.raises(ValueError):
        inject_dataset.select_rows("test_traps", 1, 1, database)
