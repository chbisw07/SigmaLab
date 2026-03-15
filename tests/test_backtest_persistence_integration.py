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
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.backtesting.models import CloseReason, ExecutionAssumptions
from app.backtesting.replay_engine import ReplayEngine
from app.models.base import Base
from app.models.orm import (
    BacktestMetric,
    BacktestRun,
    BacktestRunStatus,
    BacktestTrade,
    Instrument,
    Watchlist,
    WatchlistItem,
)
from app.services.backtests import BacktestRunService
from strategies.base import BaseStrategy, StrategyParams
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata
from strategies.registry import StrategyRegistry
from strategies.service import StrategyService


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reset_public_schema(engine) -> None:  # type: ignore[no-untyped-def]
    """Reset the test database schema.

    We avoid `Base.metadata.drop_all()` because the schema contains a FK cycle
    (`strategies` <-> `strategy_versions`) which can cause `drop_all()` to raise
    CircularDependencyError when FK constraints don't have names in SQLAlchemy's
    in-memory metadata.
    """
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


class _FakeMarketDataService:
    def __init__(self, candles: pd.DataFrame) -> None:
        self._candles = candles
        self.calls = 0

    def get_candles(self, instrument_id, timeframe, start, end):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._candles.copy()


class _PH4TestStrategy(BaseStrategy):
    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="PH4 Persistence Test",
            slug="ph4_persistence_test",
            description="",
            category=StrategyCategory.SWING,
            timeframe="1h",
            version="0.0.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return []

    def generate_signals(self, data: pd.DataFrame, params: StrategyParams, context=None, indicators=None) -> SignalResult:  # type: ignore[override]
        self._validate_input(data)
        n = len(data)
        long_entry = pd.Series([False] * n)
        long_exit = pd.Series([False] * n)
        stop_loss = pd.Series([None] * n)

        if n >= 6:
            # Trade 1: signal exit
            long_entry.iloc[0] = True
            long_exit.iloc[2] = True
            # Trade 2: stop loss intrabar
            long_entry.iloc[3] = True
            stop_loss.iloc[4] = 95.0

        return SignalResult(
            timestamp=data["timestamp"],
            indicators=pd.DataFrame(),
            long_entry=long_entry,
            long_exit=long_exit,
            short_entry=pd.Series([False] * n),
            short_exit=pd.Series([False] * n),
            stop_loss=stop_loss,
        )


def _candles_utc(n: int = 6) -> pd.DataFrame:
    t0 = datetime(2024, 1, 1, 3, 45, 0, tzinfo=ZoneInfo("UTC"))
    ts = [t0 + timedelta(hours=i) for i in range(n)]
    opens = [100.0 + i for i in range(n)]
    highs = [o + 2.0 for o in opens]
    lows = [o - 2.0 for o in opens]
    closes = [o + 1.0 for o in opens]

    df = pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [1000] * n,
        }
    )
    # Stop-loss hit intrabar on bar 4.
    df.loc[4, "low"] = 90.0
    return df


@pytest.mark.integration
def test_backtest_persists_runs_trades_and_metrics_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    # Ensure Alembic sees the test DB URL.
    env = os.environ.copy()
    env["SIGMALAB_DATABASE_URL"] = url
    env["SIGMALAB_ENV"] = "test"

    engine = create_engine(url, future=True)

    # Start from a clean schema state and ensure migrations are the source of truth.
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

        registry = StrategyRegistry()
        registry.register(_PH4TestStrategy)
        strat_svc = StrategyService(registry=registry)

        candles = _candles_utc(6)
        mds = _FakeMarketDataService(candles)
        svc = BacktestRunService(
            session=session,
            market_data_service=mds,  # type: ignore[arg-type]
            strategy_service=strat_svc,
            replay_engine=ReplayEngine(),
            assumptions=ExecutionAssumptions(),
        )

        start = candles["timestamp"].iloc[0].to_pydatetime()
        end = candles["timestamp"].iloc[-1].to_pydatetime()
        result = svc.run(
            strategy_slug=_PH4TestStrategy.metadata().slug,
            watchlist_id=wl.id,
            timeframe="1h",
            start=start,
            end=end,
            params={},
        )

        run = session.get(BacktestRun, result.run_id)
        assert run is not None
        assert run.status == BacktestRunStatus.SUCCESS
        assert run.started_at is not None
        assert run.completed_at is not None
        assert run.strategy_slug == _PH4TestStrategy.metadata().slug

        trades = list(
            session.execute(
                select(BacktestTrade).where(BacktestTrade.run_id == result.run_id).order_by(BacktestTrade.entry_ts.asc())
            ).scalars()
        )
        assert len(trades) == 2

        reasons = {t.close_reason for t in trades}
        assert CloseReason.SIGNAL_EXIT.value in reasons
        assert CloseReason.STOP_LOSS.value in reasons

        # Verify key ledger fields were persisted and look sane.
        for t in trades:
            assert t.symbol == "TEST"
            assert t.entry_price is not None
            assert t.exit_price is not None
            assert t.pnl is not None
            assert t.pnl_pct is not None
            assert t.holding_period_bars is not None and t.holding_period_bars >= 1
            assert t.holding_period_sec is not None and t.holding_period_sec >= 0

        # Trade 1 expected entry/exit per next-open semantics.
        ts = list(candles["timestamp"])
        t1 = trades[0]
        assert t1.entry_ts == ts[1].to_pydatetime()
        assert t1.exit_ts == ts[3].to_pydatetime()

        # Trade 2 stop-loss exit on bar 4.
        t2 = trades[1]
        assert t2.entry_ts == ts[4].to_pydatetime()
        assert t2.exit_ts == ts[4].to_pydatetime()
        assert t2.close_reason == CloseReason.STOP_LOSS.value

        metrics_rows = list(session.execute(select(BacktestMetric).where(BacktestMetric.run_id == result.run_id)).scalars())
        assert len(metrics_rows) == 2  # one per symbol + one overall
        assert any(m.symbol is None for m in metrics_rows)
        assert any(m.symbol == "TEST" for m in metrics_rows)
