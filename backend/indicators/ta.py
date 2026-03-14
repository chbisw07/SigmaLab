from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    # Wilder's smoothing via EMA(alpha=1/period).
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    avg_loss_safe = avg_loss.where(avg_loss != 0.0, other=1e-12)
    rs = (avg_gain / avg_loss_safe).astype("float64")
    out = 100.0 - (100.0 / (1.0 + rs))

    flat = (avg_gain == 0.0) & (avg_loss == 0.0)
    out = out.where(~flat, other=50.0)
    return out.astype("float64")


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def rolling_high(high: pd.Series, period: int) -> pd.Series:
    return high.rolling(window=period, min_periods=period).max()


def rolling_low(low: pd.Series, period: int) -> pd.Series:
    return low.rolling(window=period, min_periods=period).min()


def vwap(df: pd.DataFrame) -> pd.Series:
    """Intraday VWAP computed per day from typical price and volume.

    Expects columns: timestamp, high, low, close, volume.
    """
    required = {"timestamp", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing VWAP columns: {sorted(missing)}")

    ts = pd.to_datetime(df["timestamp"], utc=False)
    day = ts.dt.floor("D")
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].astype("float64").fillna(0.0)

    pv = typical * vol
    cum_pv = pv.groupby(day).cumsum()
    cum_vol = vol.groupby(day).cumsum().replace(0.0, pd.NA)
    return (cum_pv / cum_vol).astype("float64")


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index (ADX)."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr = true_range(high, low, close)
    atr_w = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    plus_di = 100.0 * (plus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / atr_w)
    minus_di = 100.0 * (minus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / atr_w)

    dx = (100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, pd.NA)).astype("float64")
    return dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

