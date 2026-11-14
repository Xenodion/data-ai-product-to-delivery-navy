"""Merchant profile and history for the front end."""

import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi import HTTPException

from flow import api, world_profile
from flow.contracts import FlowConfig, load_config
from flow.world.build import build_world
from flow.world.config import PROJECT_ROOT, SampleConfig, load_world_config
from flow.world.deck import load_deck

KNOWLEDGE = PROJECT_ROOT / "flow" / "fixtures" / "knowledge.json"


@pytest.fixture()
def world(write_deck: Callable[..., Path], tmp_path: Path) -> tuple[FlowConfig, Path]:
    config = load_world_config().model_copy(
        update={
            "sample": SampleConfig(current=10, history=20, dev=6),
            "merchant_target": 9,
            "transactions_per_merchant": 8,
        }
    )
    database = tmp_path / "world.sqlite"
    build_world(load_deck(write_deck()), config, KNOWLEDGE, database)
    return load_config().model_copy(update={"world_database_path": str(database)}), database


def _roles_by_merchant(database: Path) -> dict[str, set[str]]:
    with sqlite3.connect(database) as conn:
        rows = conn.execute("SELECT merchant_id, ticket_id, role FROM tickets").fetchall()
    out: dict[str, set[str]] = {}
    for merchant, ticket, role in rows:
        out.setdefault(merchant, set()).add(f"{role}:{ticket}")
    return out


def test_current_tickets_are_hidden_until_the_final_run_flag(world) -> None:
    config, database = world
    with sqlite3.connect(database) as conn:
        merchant = conn.execute(
            "SELECT merchant_id FROM tickets WHERE role = 'current' LIMIT 1"
        ).fetchone()[0]
        current = {r[0] for r in conn.execute("SELECT ticket_id FROM tickets WHERE role='current'")}
    hidden = world_profile.merchant_context(config, merchant)
    assert hidden is not None
    assert not current & {t["ticket_id"] for t in hidden["tickets"]}
    assert all(t["role"] != "current" for t in hidden["tickets"])
    shown = world_profile.merchant_context(
        config.model_copy(update={"world_show_current": True}), merchant
    )
    assert any(t["role"] == "current" for t in shown["tickets"])


def test_context_only_holds_the_requested_merchant(world) -> None:
    config, database = world
    merchant = next(iter(_roles_by_merchant(database)))
    context = world_profile.merchant_context(config, merchant)
    assert context["profile"]["merchant_id"] == merchant
    assert context["profile"]["currencies"]
    with sqlite3.connect(database) as conn:
        own = {r[0] for r in conn.execute(
            "SELECT transaction_id FROM transactions WHERE merchant_id = ?", (merchant,))}
    assert {t["transaction_id"] for t in context["recent_transactions"]} <= own


def test_unknown_merchant_is_none_and_route_answers_404(world, monkeypatch) -> None:
    config, _ = world
    assert world_profile.merchant_context(config, "M-NOPE") is None
    monkeypatch.setattr(api, "load_config", lambda: config)
    with pytest.raises(HTTPException) as caught:
        api.get_merchant_context("M-NOPE")
    assert caught.value.status_code == 404


def test_route_is_unavailable_without_a_world(monkeypatch) -> None:
    monkeypatch.setattr(api, "load_config", lambda: load_config())
    with pytest.raises(HTTPException) as caught:
        api.get_merchant_context("M-0001")
    assert caught.value.status_code == 503
