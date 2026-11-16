from pathlib import Path

import pytest

from flow.api_store import ApiStore, IdempotencyConflict, VersionConflict


def make_store(tmp_path: Path) -> ApiStore:
    return ApiStore(tmp_path / "api.sqlite3")


def add_ticket(store: ApiStore) -> None:
    assert store.insert_ticket(
        ticket_id="case-1", turn=1, flow_id="flow-1", thread_id="thread-1",
        ticket={"ticket_id": "case-1", "turn": 1, "body": "synthetic"},
    )


def test_ticket_and_idempotency_are_persisted(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    add_ticket(store)

    store.save_idempotent("ingress:case-1:1", "request-key", "hash-1", {"flow_id": "flow-1"})

    assert store.get_idempotent("ingress:case-1:1", "request-key", "hash-1") == {"flow_id": "flow-1"}
    assert store.ticket("case-1", 1)["ticket"]["body"] == "synthetic"
    with pytest.raises(IdempotencyConflict):
        store.get_idempotent("ingress:case-1:1", "request-key", "different-hash")


def test_version_check_and_action_job_survive_restart(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    add_ticket(store)
    command = {"action": "approve", "actor": "reviewer"}

    assert store.update_ticket(
        "case-1", 1, 1, status="awaiting_validation", job_status="queued", job_command=command,
    ) == 2
    with pytest.raises(VersionConflict):
        store.update_ticket("case-1", 1, 1, status="awaiting_validation")

    jobs = store.claim_jobs()

    assert jobs == [{"flow_id": "flow-1", "ticket_id": "case-1", "turn": 1, "command": command}]
    assert store.claim_jobs() == []


def test_node_event_insert_is_idempotent(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    add_ticket(store)
    event = {"node_id": "qualifier", "status": "succeeded", "duration_ms": 12.5}

    store.record_node_events("case-1", 1, 2, 0, [event])
    store.record_node_events("case-1", 1, 3, 0, [event])

    events = store.events("case-1", 1)
    assert len(events) == 1
    assert events[0]["node_id"] == "qualifier"


def test_action_reservation_is_atomic_and_idempotent(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    add_ticket(store)
    command = {"action": "approve", "actor": "reviewer"}
    kwargs = {
        "scope": "action:case-1:1:key-1", "key": "key-1", "request_sha256": "payload-hash",
        "ticket_id": "case-1", "turn": 1, "expected_version": 1,
        "status": "awaiting_validation", "run": {"status": "awaiting_validation"},
        "command": command,
    }

    first, created = store.reserve_action(**kwargs)
    replay, replay_created = store.reserve_action(**kwargs)

    assert created and not replay_created
    assert replay == first
    assert store.ticket("case-1", 1)["version"] == 2
    assert store.claim_jobs()[0]["command"] == command
