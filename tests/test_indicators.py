from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from indicators import adx, atr, ema, rsi, sma, vwap


def test_sma_and_ema_match_pandas_definitions() -> None:
    s = pd.Series([1, 2, 3, 4, 5], dtype="float64")
    assert sma(s, 3).iloc[-1] == pd.Series([1, 2, 3, 4, 5], dtype="float64").rolling(3, min_periods=3).mean().iloc[-1]
    assert ema(s, 3).iloc[-1] == s.ewm(span=3, adjust=False, min_periods=3).mean().iloc[-1]


def test_rsi_bounds() -> None:
    close = pd.Series([1, 2, 3, 2, 2, 4, 3, 3, 5], dtype="float64")
    out = rsi(close, 2).dropna()
    assert (out >= 0).all()
    assert (out <= 100).all()


def test_atr_and_adx_shapes() -> None:
    high = pd.Series([10, 11, 12, 11, 13, 14], dtype="float64")
    low = pd.Series([9, 10, 11, 10, 12, 13], dtype="float64")
    close = pd.Series([9.5, 10.5, 11.5, 10.5, 12.5, 13.5], dtype="float64")
    a = atr(high, low, close, 3)
    d = adx(high, low, close, 3)
    assert len(a) == len(close)
    assert len(d) == len(close)


def test_vwap_resets_each_day() -> None:
    t0 = datetime(2026, 3, 14, 9, 15)
    rows = []
    for i in range(3):
        rows.append({"timestamp": t0 + timedelta(minutes=15 * i), "high": 100, "low": 100, "close": 100, "volume": 10})
    # Next day with different price.
    t1 = datetime(2026, 3, 15, 9, 15)
    for i in range(2):
        rows.append({"timestamp": t1 + timedelta(minutes=15 * i), "high": 200, "low": 200, "close": 200, "volume": 10})
    df = pd.DataFrame(rows)
    vw = vwap(df)
    assert float(vw.iloc[0]) == 100.0
    assert float(vw.iloc[2]) == 100.0
    assert float(vw.iloc[3]) == 200.0
