from __future__ import annotations

import pandas as pd

from strategies.builtin.supertrend_v6_pro import SuperTrendV6ProStrategy
from strategies.params import validate_params


def _make_synthetic_candles() -> pd.DataFrame:
    # 40 bars: downtrend then uptrend then downtrend to force at least 2 flips.
    n1, n2, n3 = 14, 13, 13
    close = (
        list(pd.Series(range(n1)).apply(lambda i: 120.0 - i * 1.5))  # down
        + list(pd.Series(range(n2)).apply(lambda i: 100.0 + i * 1.8))  # up
        + list(pd.Series(range(n3)).apply(lambda i: 123.4 - i * 2.0))  # down again
    )
    n = len(close)
    ts = pd.date_range("2026-01-01", periods=n, freq="15min")
    close_s = pd.Series(close, dtype="float64")
    open_s = close_s.shift(1).fillna(close_s.iloc[0]).astype("float64")
    high_s = (pd.concat([open_s, close_s], axis=1).max(axis=1) + 0.4).astype("float64")
    low_s = (pd.concat([open_s, close_s], axis=1).min(axis=1) - 0.4).astype("float64")
    vol_s = pd.Series([1000] * n, dtype="int64")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": open_s,
            "high": high_s,
            "low": low_s,
            "close": close_s,
            "volume": vol_s,
        }
    )


def test_supertrend_emits_flip_signals_without_filters() -> None:
    df = _make_synthetic_candles()
    strat = SuperTrendV6ProStrategy()
    specs = strat.parameters()
    params = validate_params(
        specs,
        {
            "atr_period": 3,
            "atr_multiplier": 1.0,
            "use_wicks": True,
            "trade_mode": "Both",
            "use_adx_filter": False,
            "use_rsi_filter": False,
            "dmi_len": 3,
            "adx_smoothing": 3,
            "rsi_len": 3,
        },
    )

    res = strat.generate_signals(df, params=params)
    # At least one flip in each direction should occur on this synthetic path.
    assert bool(res.long_entry.any()) is True
    assert bool(res.long_exit.any()) is True
    assert bool(res.short_entry.any()) is True
    assert bool(res.short_exit.any()) is True

    # Exit flips should be independent of filter settings.
    assert (res.long_exit == res.short_entry).all()
    assert (res.short_exit == res.long_entry).all()


def test_supertrend_filters_gate_entries_but_not_flip_exits() -> None:
    df = _make_synthetic_candles()
    strat = SuperTrendV6ProStrategy()
    specs = strat.parameters()
    params = validate_params(
        specs,
        {
            "atr_period": 3,
            "atr_multiplier": 1.0,
            "use_wicks": True,
            "trade_mode": "Long only",
            "use_adx_filter": True,
            "adx_min": 99.0,  # unrealistically high => should block entries
            "use_rsi_filter": False,
            "dmi_len": 3,
            "adx_smoothing": 3,
            "rsi_len": 3,
        },
    )

    res = strat.generate_signals(df, params=params)
    assert bool(res.long_entry.any()) is False
    # Flip exits still happen when direction flips.
    assert bool(res.long_exit.any()) is True
    # trade_mode=Long only disables short entries.
    assert bool(res.short_entry.any()) is False

