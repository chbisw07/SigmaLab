from __future__ import annotations

import pandas as pd


def cross_above(a: pd.Series, b: pd.Series) -> pd.Series:
    """True when `a` crosses above `b` at this row."""
    return (a > b) & (a.shift(1) <= b.shift(1))


def cross_below(a: pd.Series, b: pd.Series) -> pd.Series:
    """True when `a` crosses below `b` at this row."""
    return (a < b) & (a.shift(1) >= b.shift(1))


def normalize_signal_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure required signal columns exist and are boolean."""
    required = ["long_entry", "long_exit", "short_entry", "short_exit"]
    for c in required:
        if c not in df.columns:
            df[c] = False
        df[c] = df[c].fillna(False).astype(bool)
    return df

