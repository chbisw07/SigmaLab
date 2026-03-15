from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


def normalize_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize candle dataframe to SigmaLab's expected shape.

    Required columns:
    - timestamp, open, high, low, close, volume

    Normalization:
    - ensure timestamp is datetime
    - sort by timestamp ascending
    - reset index
    - enforce stable column order
    """
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=False)
    out = out.sort_values("timestamp").reset_index(drop=True)
    return out[["timestamp", "open", "high", "low", "close", "volume"]]


@dataclass(frozen=True)
class PreparedSymbolInput:
    instrument_id: uuid.UUID
    symbol: str
    candles: pd.DataFrame


@dataclass(frozen=True)
class PreparedBacktestInput:
    """Reusable, in-memory backtest dataset for one run scope.

    This is a PH4 enhancement to avoid repeated market-data preparation work and
    provide a reusable evaluation context for PH5 optimization.
    """

    strategy_slug: str
    timeframe: str
    start: datetime
    end: datetime
    symbols: list[PreparedSymbolInput]

    def by_instrument_id(self) -> dict[uuid.UUID, PreparedSymbolInput]:
        return {s.instrument_id: s for s in self.symbols}

    def by_symbol(self) -> dict[str, PreparedSymbolInput]:
        return {s.symbol: s for s in self.symbols}

