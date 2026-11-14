"""Policies, oracle, validation and the full build on a micro deck."""

import json
import re
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from flow.world.build import build_world
from flow.world.config import PROJECT_ROOT, SampleConfig, WorldConfig, load_world_config
from flow.world.deck import load_deck
from flow.world.errors import DeckContractError
from flow.world.oracle import ORACLE_FILE
from flow.world.policies import load_policies
from flow.world.sampling import sample_roles
from flow.world.validate import validate_world

KNOWLEDGE = PROJECT_ROOT / "flow" / "fixtures" / "knowledge.json"


@pytest.fixture()
def config() -> WorldConfig:
    return load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=10, history=20, dev=6),
            "merchant_target": 9,
            "transactions_per_merchant": 8,
        }
    )


@pytest.fixture()
def deck_dir(write_deck: Callable[..., Path]) -> Path:
    return write_deck()


def _build(deck_dir: Path, config: WorldConfig, tmp_path: Path, name: str):
    database = tmp_path / name / "world.sqlite"
    oracle = tmp_path / name / "oracle"
    manifest = build_world(load_deck(deck_dir), config, KNOWLEDGE, database, oracle)
    return manifest, database, oracle


def test_policies_load_all_documents_with_their_sub_intents(config: WorldConfig) -> None:
    policies, links = load_policies(KNOWLEDGE, config)
    assert len(policies) == 22
    assert {p.status for p in policies} == {"approved", "draft"}
    assert {p.language for p in policies} == {"en"}
    assert {(link.source_id, link.version) for link in links} <= {
        (p.source_id, p.version) for p in policies
    }


def test_policies_reject_a_malformed_knowledge_file(tmp_path: Path, config: WorldConfig) -> None:
    broken = tmp_path / "knowledge.json"
    broken.write_text(json.dumps({"documents": [{"source_id": "x"}]}), encoding="utf-8")
    with pytest.raises(DeckContractError):
        load_policies(broken, config)


def test_build_writes_a_valid_database_with_every_table_filled(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    manifest, database, _ = _build(deck_dir, config, tmp_path, "a")
    assert manifest.row_counts["tickets"] == 36
    assert manifest.row_counts["messages"] == 36
    assert manifest.row_counts["ticket_outcomes"] == 0
    assert all(manifest.row_counts[t] > 0 for t in ("merchants", "transactions", "policies"))
    with sqlite3.connect(database) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_two_builds_with_the_same_inputs_give_the_same_content_hash(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    first, _, _ = _build(deck_dir, config, tmp_path, "a")
    second, _, _ = _build(deck_dir, config, tmp_path, "b")
    assert first.content_hash == second.content_hash


def test_the_seed_changes_the_content_hash(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    first, _, _ = _build(deck_dir, config, tmp_path, "a")
    other, _, _ = _build(
        deck_dir, config.model_copy(update={"seed": config.seed + 1}), tmp_path, "b"
    )
    assert first.content_hash != other.content_hash


def test_roles_come_from_the_expected_splits(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    _, database, _ = _build(deck_dir, config, tmp_path, "a")
    with sqlite3.connect(database) as conn:
        roles = dict(conn.execute("SELECT ticket_id, role FROM tickets"))
    deck = {t.card_id: t.split for t in load_deck(deck_dir)}
    assert {deck[i] for i, role in roles.items() if role == "current"} == {"test_natural"}
    assert {deck[i] for i, role in roles.items() if role == "dev"} == {"val"}
    assert "test_traps" not in {deck[i] for i in roles}


def test_oracle_holds_exactly_the_current_tickets(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    _, database, oracle = _build(deck_dir, config, tmp_path, "a")
    entries = json.loads((oracle / ORACLE_FILE).read_text(encoding="utf-8"))
    with sqlite3.connect(database) as conn:
        current = {r[0] for r in conn.execute("SELECT ticket_id FROM tickets WHERE role='current'")}
    assert {entry["ticket_id"] for entry in entries} == current
    assert all(set(entry) == {"ticket_id", "desk", "label"} for entry in entries)


def test_no_serving_module_imports_the_oracle() -> None:
    flow_dir = PROJECT_ROOT / "flow"
    allowed = {flow_dir / "world" / "build.py", flow_dir / "world" / "oracle.py"}
    pattern = re.compile(r"world\.oracle|from flow\.world import .*oracle|from \. import oracle")
    offenders = [
        path
        for path in flow_dir.rglob("*.py")
        if path not in allowed and pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_validate_world_detects_a_tampered_database(
    deck_dir: Path, config: WorldConfig, tmp_path: Path
) -> None:
    built, database, _ = _build(deck_dir, config, tmp_path, "a")
    shared = built.shared_references
    deck_tickets = load_deck(deck_dir)
    manifest = sample_roles(deck_tickets, config)
    deck = {t.card_id: t for t in deck_tickets}
    with sqlite3.connect(database) as conn:
        assert validate_world(conn, manifest.tickets, deck, shared, config) == []
        conn.execute("UPDATE messages SET body = 'edited' WHERE turn_index = 1 AND rowid = 1")
        conn.execute("UPDATE tickets SET opened_at = '2026-11-09T10:00:00Z' WHERE role = 'history'")
        problems = validate_world(conn, manifest.tickets, deck, shared, config)
    assert any("turn 1" in problem for problem in problems)
    assert any("inside the current window" in problem for problem in problems)
