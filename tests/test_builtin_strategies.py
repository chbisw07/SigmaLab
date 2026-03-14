from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from strategies.builtin import IntradayVWAPPullbackStrategy, SwingTrendPullbackStrategy
from strategies.base import StrategyParams


def _daily_candles() -> pd.DataFrame:
    # Construct a sequence with a clear up-jump (entry) and down-jump (exit).
    closes = [10, 10, 10, 12, 12, 12, 9]
    ts0 = datetime(2026, 3, 1)
    rows = []
    for i, c in enumerate(closes):
        rows.append(
            {
                "timestamp": ts0 + timedelta(days=i),
                "open": c,
                "high": c + 0.5,
                "low": c - 0.5,
                "close": c,
                "volume": 100,
            }
        )
    return pd.DataFrame(rows)


def _intraday_candles() -> pd.DataFrame:
    closes = [100, 100, 100, 102, 102, 98]
    ts0 = datetime(2026, 3, 14, 9, 15)
    rows = []
    for i, c in enumerate(closes):
        rows.append(
            {
                "timestamp": ts0 + timedelta(minutes=15 * i),
                "open": c,
                "high": c,
                "low": c,
                "close": c,
                "volume": 10,
            }
        )
    return pd.DataFrame(rows)


def test_swing_trend_pullback_emits_normalized_signal_columns() -> None:
    strat = SwingTrendPullbackStrategy()
    candles = _daily_candles()
    params = StrategyParams(
        values={
            "ema_fast": 2,
            "ema_slow": 3,
            "rsi_period": 2,
            "rsi_entry_max": 100.0,
            "rsi_exit_min": 0.0,
            "use_atr_stop": False,
            "atr_period": 2,
            "atr_mult": 2.0,
        }
    )
    out = strat.generate_signals(candles, params).to_frame()
    for c in ["timestamp", "long_entry", "long_exit", "short_entry", "short_exit"]:
        assert c in out.columns
    assert out["long_entry"].dtype == bool
    assert out["long_exit"].dtype == bool
    assert out["long_entry"].any()
    assert out["long_exit"].any()


def test_intraday_vwap_pullback_emits_signals() -> None:
    strat = IntradayVWAPPullbackStrategy()
    candles = _intraday_candles()
    params = StrategyParams(
        values={
            "rsi_period": 2,
            "rsi_entry_max": 100.0,
            "rsi_exit_min": 0.0,
            "vwap_buffer_pct": 0.0,
        }
    )
    out = strat.generate_signals(candles, params).to_frame()
    assert out["long_entry"].any()
    assert out["long_exit"].any()
    assert "vwap" in out.columns
