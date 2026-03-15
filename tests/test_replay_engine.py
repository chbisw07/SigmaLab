from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.backtesting.models import CloseReason, ExecutionAssumptions
from app.backtesting.replay_engine import ReplayEngine
from strategies.models import SignalResult, StrategyCategory, StrategyMetadata


def _meta(category: StrategyCategory) -> StrategyMetadata:
    return StrategyMetadata(
        name="Test Strategy",
        slug="test",
        description="",
        category=category,
        timeframe="1h",
        long_only=True,
        version="0.1.0",
    )


def _candles(n: int = 6) -> pd.DataFrame:
    t0 = datetime(2024, 1, 1, 9, 15, 0)
    ts = [t0 + timedelta(minutes=60 * i) for i in range(n)]
    # Simple rising market by default.
    opens = [100 + i for i in range(n)]
    highs = [o + 2 for o in opens]
    lows = [o - 2 for o in opens]
    closes = [o + 1 for o in opens]
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


def test_replay_next_open_entry_and_exit() -> None:
    candles = _candles(6)
    n = len(candles)
    # Entry signal on bar 1 -> entry at bar 2 open. Exit signal on bar 3 -> exit at bar 4 open.
    long_entry = pd.Series([False, True, False, False, False, False])
    long_exit = pd.Series([False, False, False, True, False, False])

    sig = SignalResult(
        timestamp=candles["timestamp"],
        indicators=pd.DataFrame(),
        long_entry=long_entry,
        long_exit=long_exit,
        short_entry=pd.Series([False] * n),
        short_exit=pd.Series([False] * n),
    )
    engine = ReplayEngine(assumptions=ExecutionAssumptions())
    res = engine.run(candles, sig, metadata=_meta(StrategyCategory.SWING), symbol="ABC")

    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.entry_ts == candles.loc[2, "timestamp"]
    assert t.entry_price == float(candles.loc[2, "open"])
    assert t.exit_ts == candles.loc[4, "timestamp"]
    assert t.exit_price == float(candles.loc[4, "open"])
    assert t.close_reason == CloseReason.SIGNAL_EXIT


def test_replay_stop_loss_triggers_intrabar() -> None:
    candles = _candles(5)
    n = len(candles)

    # Entry signal on bar 0 -> enter at bar 1 open.
    long_entry = pd.Series([True] + [False] * (n - 1))
    long_exit = pd.Series([False] * n)

    # Stop loss at 95 triggers on bar 1 because low is open-2 and open at bar1 is 101 => low 99, not hit.
    # We force a stop hit by lowering bar 1 low.
    candles.loc[1, "low"] = 90
    stop_loss = pd.Series([None, 95, 95, 95, 95])

    sig = SignalResult(
        timestamp=candles["timestamp"],
        indicators=pd.DataFrame(),
        long_entry=long_entry,
        long_exit=long_exit,
        short_entry=pd.Series([False] * n),
        short_exit=pd.Series([False] * n),
        stop_loss=stop_loss,
    )

    engine = ReplayEngine()
    res = engine.run(candles, sig, metadata=_meta(StrategyCategory.SWING), symbol="ABC")
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.close_reason == CloseReason.STOP_LOSS
    assert t.exit_ts == candles.loc[1, "timestamp"]
    assert t.exit_price == 95.0


def test_replay_forced_close_intraday_squareoff() -> None:
    candles = _candles(4)
    n = len(candles)
    long_entry = pd.Series([False, True, False, False])
    long_exit = pd.Series([False] * n)

    sig = SignalResult(
        timestamp=candles["timestamp"],
        indicators=pd.DataFrame(),
        long_entry=long_entry,
        long_exit=long_exit,
        short_entry=pd.Series([False] * n),
        short_exit=pd.Series([False] * n),
    )
    res = ReplayEngine().run(candles, sig, metadata=_meta(StrategyCategory.INTRADAY), symbol="ABC")
    assert len(res.trades) == 1
    assert res.trades[0].close_reason == CloseReason.INTRADAY_SQUAREOFF

