from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def test_root_endpoint() -> None:
    client = TestClient(create_app(Settings(env="test")))
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_endpoint() -> None:
    client = TestClient(create_app(Settings(env="test")))
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

