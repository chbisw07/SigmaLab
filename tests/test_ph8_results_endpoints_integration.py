from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.backtesting.models import ExecutionAssumptions
from app.backtesting.replay_engine import ReplayEngine
from app.core.settings import Settings
from app.main import create_app
from app.models.orm import Candle, Instrument, Watchlist, WatchlistItem
from app.services.backtests import BacktestRunService
from strategies.service import StrategyService


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reset_public_schema(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _candles_utc(n: int = 24) -> pd.DataFrame:
    # Start at 09:15 IST (03:45 UTC) to match our market-data normalization assumptions.
    t0 = datetime(2024, 1, 1, 3, 45, 0, tzinfo=ZoneInfo("UTC"))
    ts = [t0 + timedelta(hours=i) for i in range(n)]
    opens = [100.0 + (i * 0.5) for i in range(n)]
    highs = [o + 1.0 for o in opens]
    lows = [o - 1.0 for o in opens]
    closes = [o + (0.25 if i % 2 == 0 else -0.25) for i, o in enumerate(opens)]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [1000] * n,
        }
    )


class _FakeMarketDataService:
    def __init__(self, candles: pd.DataFrame) -> None:
        self._candles = candles

    def get_candles(self, instrument_id, timeframe, start, end):  # type: ignore[no-untyped-def]
        return self._candles.copy()


@pytest.mark.integration
def test_ph8_exports_and_chart_endpoint_postgres() -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    env = os.environ.copy()
    env["SIGMALAB_DATABASE_URL"] = url
    env["SIGMALAB_ENV"] = "test"

    engine = create_engine(url, future=True)
    _reset_public_schema(engine)

    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        cwd=str(_repo_root()),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    SessionLocal = sessionmaker(bind=engine, future=True)
    with SessionLocal() as session:
        inst = Instrument(
            broker_instrument_token="123",
            exchange="NSE",
            symbol="TEST",
            name="Test",
            segment="EQ",
            instrument_metadata={},
        )
        session.add(inst)
        session.commit()
        session.refresh(inst)

        wl = Watchlist(name=f"wl-{uuid.uuid4()}", description=None)
        session.add(wl)
        session.commit()
        session.refresh(wl)
        session.add(WatchlistItem(watchlist_id=wl.id, instrument_id=inst.id))
        session.commit()

        # Persist base candles so /backtests/{run}/chart can read from DB without Kite creds.
        candles = _candles_utc(24)
        for r in candles.itertuples(index=False):
            session.add(
                Candle(
                    instrument_id=inst.id,
                    base_interval="60minute",
                    ts=r.timestamp.to_pydatetime(),
                    open=float(r.open),
                    high=float(r.high),
                    low=float(r.low),
                    close=float(r.close),
                    volume=int(r.volume),
                )
            )
        session.commit()

        # Create a backtest run (uses fake MDS; persistence is what we care about for PH8 endpoints).
        svc = BacktestRunService(
            session=session,
            market_data_service=_FakeMarketDataService(candles),  # type: ignore[arg-type]
            strategy_service=StrategyService.default(),
            replay_engine=ReplayEngine(),
            assumptions=ExecutionAssumptions(),
        )

        start = candles["timestamp"].iloc[0].to_pydatetime()
        end = candles["timestamp"].iloc[-1].to_pydatetime()
        res = svc.run(
            strategy_slug="swing_trend_pullback",
            watchlist_id=wl.id,
            timeframe="1h",
            start=start,
            end=end,
            params={"ema_fast": 5, "ema_slow": 10, "rsi_period": 14},
        )

    client = TestClient(create_app(Settings(env="test", database_url=url)))

    # CSV export: should always return a CSV, even if there are 0 trades.
    t_csv = client.get(f"/backtests/{res.run_id}/export/trades.csv")
    assert t_csv.status_code == 200
    assert "text/csv" in (t_csv.headers.get("content-type") or "")
    assert "symbol,entry_ts,entry_price" in t_csv.text.splitlines()[0]

    m_csv = client.get(f"/backtests/{res.run_id}/export/metrics.csv")
    assert m_csv.status_code == 200
    assert "text/csv" in (m_csv.headers.get("content-type") or "")
    assert m_csv.text.splitlines()[0].startswith("symbol,")

    chart = client.get(f"/backtests/{res.run_id}/chart", params={"instrument_id": str(inst.id)})
    assert chart.status_code == 200
    body = chart.json()
    assert body["status"] == "ok"
    assert body["run_id"] == str(res.run_id)
    assert body["instrument_id"] == str(inst.id)
    assert body["timeframe"] == "1h"
    assert isinstance(body["candles"], list) and len(body["candles"]) > 0
    assert isinstance(body["markers"], list)
    assert isinstance(body["overlays"], dict)
