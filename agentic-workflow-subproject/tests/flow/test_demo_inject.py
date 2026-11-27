from fastapi.testclient import TestClient

from flow.api import app


def test_demo_inject_is_hidden_unless_demo_mode(monkeypatch) -> None:
    monkeypatch.delenv("NAVY_DEMO_MODE", raising=False)
    client = TestClient(app)
    assert client.get("/api/v1/demo").json()["enabled"] is False
    assert client.post("/api/v1/demo/inject", json={"count": 1}).status_code == 404


def test_demo_inject_rejects_oversized_count(monkeypatch) -> None:
    monkeypatch.setenv("NAVY_DEMO_MODE", "1")
    assert TestClient(app).post("/api/v1/demo/inject", json={"count": 999}).status_code == 422


def test_command_names_cover_every_renamed_action() -> None:
    from flow.api import _COMMAND_NAMES, _allowed_actions, _human_command, ActionRequest

    # a renamed action must still be accepted by the allowed-actions check in _mutate
    assert _human_command(ActionRequest(action="close_manual", actor="a", reason="r"))["action"] == "close"
    assert {_COMMAND_NAMES.get(n, n) for n in ("write_reply", "close_manual")} == {"write", "close"}
