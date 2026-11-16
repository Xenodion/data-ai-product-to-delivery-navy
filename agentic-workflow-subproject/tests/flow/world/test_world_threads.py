"""History threads: plan, checks, stub generation and ingest into the database build."""

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from flow.world.build import build_world
from flow.world.config import PROJECT_ROOT, SampleConfig, WorldConfig, load_world_config
from flow.world.deck import load_deck
from flow.world.errors import ValidationFailure
from flow.world.threads import generate
from flow.world.threads.checks import check_thread
from flow.world.threads.plan import ThreadPlan, last_allowed, plan_threads
from ml.qualifier.src.dataset_build.openrouter import Budget, BudgetExhaustedError, Completion

KNOWLEDGE = PROJECT_ROOT / "flow" / "fixtures" / "knowledge.json"
SYSTEM = generate.PROMPT_PATH.read_text(encoding="utf-8")


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
def v0(write_deck: Callable[..., Path], config: WorldConfig, tmp_path: Path):
    deck_dir = write_deck()
    database = tmp_path / "v0.sqlite"
    build_world(load_deck(deck_dir), config, KNOWLEDGE, database)
    deck = {t.card_id: t for t in load_deck(deck_dir)}
    return deck_dir, database, deck


def _plans(v0, config: WorldConfig) -> list[ThreadPlan]:
    _, database, deck = v0
    with sqlite3.connect(database) as conn:
        return list(plan_threads(conn, deck, config))


def _run(plans, config, tmp_path, call=generate.stub_complete, budget=None):
    return generate.write_threads(
        plans, config, SYSTEM, call, budget or Budget(1.0), lambda s, u: 0.0,
        tmp_path / "calls", tmp_path / "threads",
    )


def test_plan_covers_every_history_ticket_and_ends_before_the_current_window(v0, config) -> None:
    plans = _plans(v0, config)
    assert len(plans) == config.sample.history
    for plan in plans:
        assert plan.messages[0].author_kind == "agent"
        assert plan.messages[-1].author_kind == "agent"
        assert all(a.sent_at < b.sent_at for a, b in zip(plan.messages, plan.messages[1:]))
        assert plan.messages[-1].sent_at < last_allowed(config)


def test_plan_is_deterministic(v0, config) -> None:
    assert _plans(v0, config) == _plans(v0, config)


def test_checks_flag_unknown_figures_wrong_turns_and_wrong_endings(v0, config) -> None:
    plan = next(p for p in _plans(v0, config) if p.state == "closed")
    turns = [m.turn_index for m in plan.messages]
    good = {t: "All good." for t in turns}
    assert check_thread(plan, good, 1500) == []
    assert check_thread(plan, {turns[0]: "x"}, 1500) or len(turns) == 1
    assert check_thread(plan, {**good, turns[-1]: "Refund of 98765.43 sent."}, 1500)
    assert check_thread(plan, {**good, turns[-1]: "Anything else?"}, 1500)
    waiting = plan.model_copy(update={"state": "open_awaiting_merchant"})
    assert check_thread(waiting, good, 1500)


def test_stub_run_writes_one_record_per_thread_and_resumes(v0, config, tmp_path) -> None:
    plans = _plans(v0, config)
    first = _run(plans, config, tmp_path)
    assert first["llm"] == len(plans) and first["fallback"] == 0
    second = _run(plans, config, tmp_path)
    assert second["skipped"] == len(plans)
    lines = (tmp_path / "threads" / generate.ACCEPTED_FILE).read_text("utf-8").splitlines()
    assert len(lines) == len(plans)


def test_a_bad_answer_is_retried_then_replaced_by_the_fallback(v0, config, tmp_path) -> None:
    plans = _plans(v0, config)[:2]
    calls = []

    def bad(system: str, user: str) -> Completion:
        calls.append(user)
        return Completion(content="not json", prompt_tokens=1, completion_tokens=1, cost_usd=0.01)

    counts = _run(plans, config, tmp_path, bad)
    assert counts["fallback"] == 2 and len(calls) == 4
    assert counts["spent_usd"] == pytest.approx(0.04)


def test_the_budget_stops_the_run_before_the_next_call(v0, config, tmp_path) -> None:
    plans = _plans(v0, config)
    with pytest.raises(BudgetExhaustedError):
        generate.write_threads(
            plans, config, SYSTEM, generate.stub_complete, Budget(0.001), lambda s, u: 0.01,
            tmp_path / "calls", tmp_path / "threads",
        )


def test_the_prompt_never_receives_labels_or_the_oracle(v0, config) -> None:
    user = generate.render_user(_plans(v0, config)[0])
    for forbidden in ("traps", "noise", "sentinel", "label", "urgency", "sentiment"):
        assert forbidden not in user.lower()


def test_build_ingests_the_log_into_a_valid_world_v1(v0, config, tmp_path) -> None:
    deck_dir, _, _ = v0
    _run(_plans(v0, config), config, tmp_path)
    log = tmp_path / "threads" / generate.ACCEPTED_FILE
    database = tmp_path / "v1.sqlite"
    manifest = build_world(load_deck(deck_dir), config, KNOWLEDGE, database, threads_log=log)
    assert manifest.row_counts["messages"] > config.sample.history + config.sample.current
    assert manifest.row_counts["ticket_outcomes"] > 0
    again = build_world(
        load_deck(deck_dir), config, KNOWLEDGE, tmp_path / "v1b.sqlite", threads_log=log
    )
    assert again.content_hash == manifest.content_hash
    with sqlite3.connect(database) as conn:
        turn_one = conn.execute(
            "SELECT count(*) FROM messages WHERE turn_index = 1"
        ).fetchone()[0]
    assert turn_one == config.sample.history + config.sample.current + config.sample.dev


def test_build_rejects_a_log_that_misses_a_history_ticket(v0, config, tmp_path) -> None:
    deck_dir, _, _ = v0
    _run(_plans(v0, config), config, tmp_path)
    log = tmp_path / "threads" / generate.ACCEPTED_FILE
    lines = log.read_text("utf-8").splitlines()
    log.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(ValidationFailure):
        build_world(load_deck(deck_dir), config, KNOWLEDGE, tmp_path / "x.sqlite", threads_log=log)
    assert json.loads(lines[0])["ticket_id"]
