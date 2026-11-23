"""API tests: health, plan validation, idempotency replay."""
from fastapi.testclient import TestClient

from backend.app.main import app

c = TestClient(app)


def test_health_manifest():
    assert c.get("/healthz").json() == {"ok": True}
    m = c.get("/manifest").json()
    assert "720p" in m["presets"]


def test_plan_validation():
    r = c.post("/v1/plans:generate", json={"raw": '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":1}]}'})
    assert r.status_code == 200
    r2 = c.post("/v1/plans:generate", json={"raw": "not json"})
    assert r2.status_code == 422


def test_idempotency_replay():
    body = {"assetId": "a", "plan": {"ops": []}}
    h = {"Idempotency-Key": "k-123"}
    r1 = c.post("/v1/renders", json=body, headers=h)
    r2 = c.post("/v1/renders", json=body, headers=h)
    assert r1.json()["jobId"] == r2.json()["jobId"]
    assert r2.json().get("replayed") is True
