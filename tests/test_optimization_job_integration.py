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

from app.backtesting.replay_engine import ReplayEngine
from app.backtesting.models import ExecutionAssumptions
from app.core.settings import Settings
from app.models.orm import (
    BacktestMetric,
    BacktestRun,
    BacktestTrade,
    Candle,
    Instrument,
    OptimizationCandidateResult,
    OptimizationJob,
    OptimizationJobStatus,
    ParameterPreset,
    Watchlist,
    WatchlistItem,
)
from app.services.optimizations import OptimizationCreateInput, OptimizationService
from strategies.base import BaseStrategy, StrategyParams
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata
from strategies.registry import StrategyRegistry
from strategies.service import StrategyService


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reset_public_schema(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


class _OptTestStrategy(BaseStrategy):
    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="PH5 Opt Test",
            slug="ph5_opt_test",
            description="",
            category=StrategyCategory.SWING,
            timeframe="1D",
            version="0.0.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                key="n_trades",
                label="Number of trades",
                type="int",
                default=1,
                min=1,
                max=3,
                step=1,
                tunable=True,
            )
        ]

    def generate_signals(self, data: pd.DataFrame, params: StrategyParams, context=None, indicators=None) -> SignalResult:  # type: ignore[override]
        self._validate_input(data)
        n = len(data)
        n_trades = int(params.values["n_trades"])
        long_entry = pd.Series([False] * n)
        long_exit = pd.Series([False] * n)

        # Encode N trades as alternating entry/exit signals.
        # Replay engine executes on next-bar open, and enforces one position at a time.
        for i in range(n_trades):
            e_idx = 2 * i
            x_idx = 2 * i + 1
            if e_idx < n:
                long_entry.iloc[e_idx] = True
            if x_idx < n:
                long_exit.iloc[x_idx] = True

        false_s = pd.Series([False] * n)
        return SignalResult(
            timestamp=data["timestamp"],
            indicators=pd.DataFrame(),
            long_entry=long_entry,
            long_exit=long_exit,
            short_entry=false_s,
            short_exit=false_s,
            stop_loss=None,
            take_profit=None,
        )


@pytest.mark.integration
def test_ph5_optimization_job_persists_candidates_and_preset() -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    engine = create_engine(url, future=True)
    _reset_public_schema(engine)

    # Run Alembic migrations against the test DB.
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(_repo_root() / "backend" / "alembic.ini"),
            "upgrade",
            "head",
        ]
    )

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session
    with SessionLocal() as session:
        # Minimal instrument + watchlist.
        inst = Instrument(
            broker_instrument_token="123",
            exchange="NSE",
            symbol="TEST",
            name="Test Instrument",
            segment="NSE",
            instrument_metadata={},
        )
        wl = Watchlist(name="PH5 Test Watchlist", description=None)
        session.add_all([inst, wl])
        session.commit()
        session.refresh(inst)
        session.refresh(wl)
        session.add(WatchlistItem(watchlist_id=wl.id, instrument_id=inst.id))
        session.commit()

        # Seed daily candles for a small range; timestamps stored in UTC.
        # MarketDataService uses naive IST wall-clock; DBCandleStore converts to UTC for queries.
        tz_ist = ZoneInfo("Asia/Kolkata")
        start_local = datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_ist)
        rows = []
        for i in range(10):
            ts_local = start_local + timedelta(days=i)
            ts_utc = ts_local.astimezone(ZoneInfo("UTC"))
            price = 100.0 + i
            rows.append(
                Candle(
                    instrument_id=inst.id,
                    base_interval="day",
                    ts=ts_utc,
                    open=price,
                    high=price + 1.0,
                    low=price - 1.0,
                    close=price + 0.5,
                    volume=1000,
                )
            )
        session.add_all(rows)
        session.commit()

        # Strategy service with a custom registry containing our test strategy.
        reg = StrategyRegistry()
        reg.register(_OptTestStrategy)
        strat_svc = StrategyService(registry=reg)

        opt = OptimizationService(
            session=session,
            strategy_service=strat_svc,
            replay_engine=ReplayEngine(),
            assumptions=ExecutionAssumptions(),
        )

        inp = OptimizationCreateInput(
            strategy_slug="ph5_opt_test",
            watchlist_id=wl.id,
            timeframe="1D",
            start=start_local.replace(tzinfo=None),
            end=(start_local + timedelta(days=9)).replace(tzinfo=None),
            objective_metric="total_trades",
            sort_direction="desc",
            selection={"n_trades": {"mode": "range", "min": 1, "max": 3, "step": 1}},
            max_combinations=10,
        )
        created = opt.create_job(inp=inp)
        assert created.total_combinations == 3

        settings = Settings(env="test", database_url=url)
        opt.run_job(job_id=created.job_id, settings=settings)

        job = session.get(OptimizationJob, created.job_id)
        assert job is not None
        assert job.status == OptimizationJobStatus.SUCCESS
        assert job.completed_combinations == job.total_combinations == 3

        candidates = list(
            session.execute(
                select(OptimizationCandidateResult)
                .where(OptimizationCandidateResult.optimization_job_id == job.id)
                .order_by(OptimizationCandidateResult.rank.asc())
            ).scalars()
        )
        assert [c.rank for c in candidates] == [1, 2, 3]

        # Rank 1 should correspond to n_trades=3 when objective is total_trades desc.
        assert int(candidates[0].params_json["n_trades"]) == 3

        runs = list(session.execute(select(BacktestRun)).scalars())
        assert len(runs) == 3
        assert len(session.execute(select(BacktestMetric)).scalars().all()) >= 3  # per-run portfolio rows exist
        assert len(session.execute(select(BacktestTrade)).scalars().all()) >= 1

        preset = opt.save_preset_from_candidate(job_id=job.id, candidate_id=candidates[0].id, name="best")
        assert preset.name == "best"
        assert preset.values_json["n_trades"] == 3
        assert len(list(session.execute(select(ParameterPreset)).scalars())) == 1
