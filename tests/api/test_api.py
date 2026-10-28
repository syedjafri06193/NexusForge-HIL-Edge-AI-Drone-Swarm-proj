"""HTTP API tests: request validation, session lifecycle and limits."""
import pytest
from fastapi.testclient import TestClient

import backend.api.main as api


@pytest.fixture
def client(monkeypatch):
    # No Redis in tests; the lifespan falls back to running without it.
    monkeypatch.setattr(api, "REDIS_URL", "redis://127.0.0.1:1")
    with TestClient(api.app) as c:
        yield c
    api.sessions.clear()


def _create(client, **body):
    r = client.post("/sessions", json={"num_teams": 2, "drones_per_team": 2, **body})
    assert r.status_code == 201, r.text
    return r.json()["session_id"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_session_lifecycle(client):
    sid = _create(client)
    assert any(s["session_id"] == sid for s in client.get("/sessions").json())
    assert client.get(f"/sessions/{sid}").status_code == 200
    assert client.post(f"/sessions/{sid}/pause").json() == {"paused": True}
    assert client.delete(f"/sessions/{sid}").json() == {"deleted": sid}
    assert client.get(f"/sessions/{sid}").status_code == 404


def test_session_limit(client, monkeypatch):
    monkeypatch.setattr(api, "MAX_SESSIONS", 1)
    _create(client)
    r = client.post("/sessions", json={"num_teams": 2, "drones_per_team": 1})
    assert r.status_code == 429


def test_command_validation(client):
    sid = _create(client)
    ok = client.post(f"/sessions/{sid}/command", json={"team": "red", "mission": "attack", "formation": "wedge"})
    assert ok.status_code == 200, ok.text
    bad = client.post(f"/sessions/{sid}/command", json={"team": "purple", "mission": "attack"})
    assert bad.status_code == 400


def test_spawn_drone_validates_inputs(client):
    sid = _create(client)
    ok = client.post(f"/sessions/{sid}/drones", json={"team": "BLUE", "quantization_bits": 4})
    assert ok.status_code == 200, ok.text
    for body in ({"team": "BLUE", "quantization_bits": 3},
                 {"team": "BLUE", "aggression": 7},
                 {"team": "NOPE"}):
        r = client.post(f"/sessions/{sid}/drones", json=body)
        assert r.status_code in (400, 422), (body, r.status_code)


def test_benchmark_rejects_unknown_targets_and_huge_runs(client):
    ok = client.post("/benchmark", json={"n_runs": 5})
    assert ok.status_code == 200, ok.text
    assert client.post("/benchmark", json={"model_name": "nope"}).status_code == 400
    assert client.post("/benchmark", json={"mcu_type": "nope"}).status_code == 400
    assert client.post("/benchmark", json={"n_runs": 10_000_000}).status_code == 422


def test_websocket_survives_malformed_messages(client):
    sid = _create(client)
    with client.websocket_connect(f"/sessions/{sid}/ws") as ws:
        assert ws.receive_json()["type"] == "init"
        ws.send_text("not json")
        assert ws.receive_json()["type"] in ("error", "state")
        ws.send_json({"type": "command", "team": "purple", "text": "attack"})
        ws.send_json({"type": "ping"})
        # Drain broadcasts until our pong arrives; the socket must still be open.
        for _ in range(500):
            if ws.receive_json().get("type") == "pong":
                break
        else:
            pytest.fail("no pong after malformed messages")


def test_hil_inject(client):
    sid = _create(client)
    drone_id = client.get(f"/sessions/{sid}").json()["drones"][0]["id"]
    r = client.post(f"/sessions/{sid}/hil/inject",
                    json={"drone_id": drone_id, "battery_pct": 42, "pos": {"x": 10, "y": 20}})
    assert r.status_code == 200, r.text
    # Unknown drones are reported, not silently "injected".
    assert client.post(f"/sessions/{sid}/hil/inject", json={"drone_id": "ghost"}).status_code == 404
    # A partial position used to raise KeyError (HTTP 500).
    assert client.post(f"/sessions/{sid}/hil/inject",
                       json={"drone_id": drone_id, "pos": {"x": 1}}).status_code == 422
