from __future__ import annotations

from datetime import datetime, timedelta
import uuid

import pandas as pd

from app.backtesting.candle_cache import CandleCache
from app.backtesting.metrics import compute_metrics
from app.backtesting.replay_engine import ReplayEngine
from data.timeframe import Timeframe
from strategies.base import BaseStrategy, StrategyParams
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata


class _DeterministicStrategy(BaseStrategy):
    """Test-only strategy: deterministic signals to exercise PH4 semantics."""

    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="PH4 Deterministic Test",
            slug="ph4_deterministic_test",
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
        # Two trades:
        # - enter on bar 0 -> entry at bar 1 open; exit on bar 2 -> exit at bar 3 open (signal exit).
        # - enter on bar 3 -> entry at bar 4 open; stop-loss hit intrabar on bar 4 (stop loss).
        long_entry = pd.Series([False] * n)
        long_exit = pd.Series([False] * n)
        if n >= 5:
            long_entry.iloc[0] = True
            long_exit.iloc[2] = True
            long_entry.iloc[3] = True

        stop_loss = pd.Series([None] * n)
        if n >= 5:
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


def _candles(n: int = 6) -> pd.DataFrame:
    t0 = datetime(2024, 1, 1, 9, 15, 0)
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
    # Ensure stop-loss hit on bar 4.
    if n >= 5:
        df.loc[4, "low"] = 90.0
    return df


def _serialize_trades(trades) -> list[dict]:  # type: ignore[no-untyped-def]
    out = []
    for t in trades:
        d = t.to_orm_row()
        # Normalize datetimes for equality checks.
        d["entry_ts"] = d["entry_ts"].isoformat()
        d["exit_ts"] = d["exit_ts"].isoformat() if d["exit_ts"] else None
        out.append(d)
    return out


def test_backtest_repeatability_unit() -> None:
    candles = _candles(6)
    strat = _DeterministicStrategy()
    engine = ReplayEngine()

    sig1 = strat.generate_signals(candles, StrategyParams(values={}))
    r1 = engine.run(candles, sig1, metadata=strat.metadata(), symbol="TEST")
    m1 = compute_metrics(r1.trades, r1.equity_curve)

    sig2 = strat.generate_signals(candles, StrategyParams(values={}))
    r2 = engine.run(candles, sig2, metadata=strat.metadata(), symbol="TEST")
    m2 = compute_metrics(r2.trades, r2.equity_curve)

    assert _serialize_trades(r1.trades) == _serialize_trades(r2.trades)
    assert m1.metrics == m2.metrics
    assert [p.to_json() for p in m1.equity_curve] == [p.to_json() for p in m2.equity_curve]
    assert [p.to_json() for p in m1.drawdown_curve] == [p.to_json() for p in m2.drawdown_curve]


class _FakeMDS:
    def __init__(self, candles: pd.DataFrame) -> None:
        self._candles = candles
        self.calls = 0

    def get_candles(self, instrument_id, timeframe, start, end):  # type: ignore[no-untyped-def]
        self.calls += 1
        # Return a copy to mimic a fresh DB read / aggregation each time.
        return self._candles.copy()


def test_cache_on_off_identical_results_unit() -> None:
    candles = _candles(6)
    strat = _DeterministicStrategy()
    engine = ReplayEngine()
    fake = _FakeMDS(candles)

    def run_once(use_cache: bool) -> tuple[list[dict], dict, int]:
        cache = CandleCache() if use_cache else None
        # Simulate repeated data access within the same run (e.g., multiple stages).
        if cache is None:
            df1 = fake.get_candles("x", Timeframe.H1, candles["timestamp"].iloc[0], candles["timestamp"].iloc[-1])
            df2 = fake.get_candles("x", Timeframe.H1, candles["timestamp"].iloc[0], candles["timestamp"].iloc[-1])
        else:
            inst_id = uuid.uuid4()
            df1 = cache.get(
                fake,  # type: ignore[arg-type]
                instrument_id=inst_id,  # not used by FakeMDS
                timeframe=Timeframe.H1,
                start=candles["timestamp"].iloc[0],
                end=candles["timestamp"].iloc[-1],
            )
            df2 = cache.get(
                fake,  # type: ignore[arg-type]
                instrument_id=inst_id,  # not used by FakeMDS
                timeframe=Timeframe.H1,
                start=candles["timestamp"].iloc[0],
                end=candles["timestamp"].iloc[-1],
            )

        assert df1.equals(df2)
        sig = strat.generate_signals(df1, StrategyParams(values={}))
        replay = engine.run(df1, sig, metadata=strat.metadata(), symbol="TEST")
        metrics = compute_metrics(replay.trades, replay.equity_curve)
        return _serialize_trades(replay.trades), metrics.metrics, fake.calls

    fake.calls = 0
    trades_no_cache, metrics_no_cache, calls_no_cache = run_once(use_cache=False)
    fake.calls = 0
    trades_cache, metrics_cache, calls_cache = run_once(use_cache=True)

    assert trades_no_cache == trades_cache
    assert metrics_no_cache == metrics_cache
    assert calls_no_cache == 2
    assert calls_cache == 1
