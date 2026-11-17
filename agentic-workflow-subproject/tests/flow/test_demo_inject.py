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
