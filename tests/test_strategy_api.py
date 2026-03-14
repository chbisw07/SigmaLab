from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def test_list_strategies_endpoint() -> None:
    client = TestClient(create_app(Settings(env="test")))
    resp = client.get("/strategies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    slugs = sorted([s["slug"] for s in data["strategies"]])
    assert slugs == ["intraday_vwap_pullback", "swing_trend_pullback"]


def test_get_strategy_detail_and_validate_params() -> None:
    client = TestClient(create_app(Settings(env="test")))
    resp = client.get("/strategies/swing_trend_pullback")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["slug"] == "swing_trend_pullback"
    keys = [p["key"] for p in data["parameters"]]
    assert "ema_fast" in keys

    v = client.post("/strategies/swing_trend_pullback/validate", json={"ema_fast": 10})
    assert v.status_code == 200
    assert v.json()["validated"]["ema_fast"] == 10

    bad = client.post("/strategies/swing_trend_pullback/validate", json={"nope": 1})
    assert bad.status_code == 400

