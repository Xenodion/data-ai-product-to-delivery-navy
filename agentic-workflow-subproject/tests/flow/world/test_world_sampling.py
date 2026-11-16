import json
import tomllib
from pathlib import Path

import pytest
from world_test_factories import make_row, write_split_file

from flow.world.config import DEFAULT_CONFIG_PATH, WorldConfig
from flow.world.deck import SPLIT_NAMES, load_deck
from flow.world.errors import SamplingError
from flow.world.sampling import (
    REASON_AFTER_REFERENCE,
    REASON_CITED_DATE_TOO_OLD,
    sample_roles,
    write_manifest,
)

ROLES = ("current", "history", "dev")


def _config(**sample: int) -> WorldConfig:
    raw = tomllib.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["sample"] = {"current": 10, "history": 15, "dev": 5} | sample
    return WorldConfig.model_validate(raw)


def _ids(manifest, role: str) -> set[str]:
    return {t.card_id for t in manifest.tickets if t.role == role}


def test_sample_roles_fills_each_role_to_its_configured_size(write_deck) -> None:
    manifest = sample_roles(load_deck(write_deck()), _config())
    assert {role: len(_ids(manifest, role)) for role in ROLES} == {
        "current": 10,
        "history": 15,
        "dev": 5,
    }


def test_sample_roles_takes_current_from_test_natural_only(write_deck) -> None:
    manifest = sample_roles(load_deck(write_deck()), _config())
    assert {t.split for t in manifest.tickets if t.role == "current"} == {"test_natural"}


def test_sample_roles_never_puts_a_test_ticket_in_history_or_dev(write_deck) -> None:
    manifest = sample_roles(load_deck(write_deck()), _config())
    for ticket in manifest.tickets:
        if ticket.split in ("test_natural", "test_traps"):
            assert ticket.role == "current"


def test_sample_roles_keeps_dev_and_history_disjoint_and_dev_inside_val(write_deck) -> None:
    manifest = sample_roles(load_deck(write_deck()), _config())
    assert _ids(manifest, "dev").isdisjoint(_ids(manifest, "history"))
    assert all(t.split == "val" for t in manifest.tickets if t.role == "dev")


def test_sample_roles_is_deterministic_for_a_seed_and_changes_with_it(write_deck) -> None:
    deck = load_deck(write_deck())
    config = _config()
    other = WorldConfig.model_validate(config.model_dump(mode="json") | {"seed": config.seed + 1})
    first = sample_roles(deck, config)
    assert first.content_hash == sample_roles(deck, config).content_hash
    assert first.content_hash != sample_roles(deck, other).content_hash


def test_sample_roles_raises_when_a_role_exceeds_its_pool(write_deck) -> None:
    with pytest.raises(SamplingError, match="current"):
        sample_roles(load_deck(write_deck()), _config(current=500))


def _write_deck_with_dated_tickets(tmp_path: Path) -> Path:
    plain = [make_row(f"{{split}}-{i}", f"question {i}") for i in range(6)]
    for split in SPLIT_NAMES:
        rows = [row | {"card_id": row["card_id"].format(split=split)} for row in plain]
        rows.append(make_row(f"{split}-future", "deadline 2027-01-15"))
        rows.append(make_row(f"{split}-stale", "the payment of 3 Feb 2025 never arrived"))
        rows.append(make_row(f"{split}-recent", "the payment of 3 Oct 2026 never arrived"))
        write_split_file(tmp_path / f"{split}.csv", rows)
    return tmp_path


def test_sample_roles_excludes_tickets_dated_after_the_reference_date_from_every_role(
    tmp_path: Path,
) -> None:
    deck = load_deck(_write_deck_with_dated_tickets(tmp_path))
    manifest = sample_roles(deck, _config(current=6, history=6, dev=3))
    assert not [t for t in manifest.tickets if t.card_id.endswith("-future")]
    reasons = {e.reason for e in manifest.excluded if e.card_id.endswith("-future")}
    assert reasons == {REASON_AFTER_REFERENCE}


def test_sample_roles_keeps_stale_cited_dates_out_of_current_and_dev_but_not_history(
    tmp_path: Path,
) -> None:
    deck = load_deck(_write_deck_with_dated_tickets(tmp_path))
    manifest = sample_roles(deck, _config(current=6, history=10, dev=3))
    for role in ("current", "dev"):
        assert not [i for i in _ids(manifest, role) if i.endswith("-stale")]
    stale_excluded = {e.role for e in manifest.excluded if e.reason == REASON_CITED_DATE_TOO_OLD}
    assert stale_excluded == {"current", "dev"}
    assert not [
        e
        for e in manifest.excluded
        if e.role == "history" and e.reason == REASON_CITED_DATE_TOO_OLD
    ]


def test_sample_roles_manifest_records_inputs_and_hashes_them(write_deck) -> None:
    deck = load_deck(write_deck())
    config = _config()
    first = sample_roles(deck, config, inputs={"config": "aaa"}, version="commit-1")
    same = sample_roles(deck, config, inputs={"config": "aaa"}, version="commit-2")
    other = sample_roles(deck, config, inputs={"config": "bbb"}, version="commit-1")
    assert first.inputs == {"config": "aaa"}
    assert first.content_hash == same.content_hash, "the code version is outside the hash"
    assert first.content_hash != other.content_hash


def test_manifest_file_is_complete_and_holds_no_ticket_body(write_deck, tmp_path: Path) -> None:
    deck = load_deck(write_deck())
    manifest = sample_roles(deck, _config())
    target = tmp_path / "out" / "sample_manifest.json"
    write_manifest(manifest, target)
    payload = target.read_text(encoding="utf-8")
    assert json.loads(payload)["content_hash"] == manifest.content_hash
    assert all(ticket.text not in payload for ticket in deck)
    assert not target.with_suffix(".json.tmp").exists()
