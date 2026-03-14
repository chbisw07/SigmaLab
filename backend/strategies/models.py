from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd


class StrategyCategory(str, enum.Enum):
    SWING = "swing"
    INTRADAY = "intraday"


class StrategyStatus(str, enum.Enum):
    EXPERIMENTAL = "experimental"
    STABLE = "stable"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class StrategyMetadata:
    name: str
    slug: str
    description: str
    category: StrategyCategory
    timeframe: str
    long_only: bool = True
    supported_segments: tuple[str, ...] = ("NSE", "BSE")
    version: str = "0.1.0"
    status: StrategyStatus = StrategyStatus.EXPERIMENTAL
    notes: str | None = None


ParamType = Literal["int", "float", "bool", "enum"]


@dataclass(frozen=True)
class ParameterSpec:
    key: str
    label: str
    type: ParamType
    default: Any
    description: str | None = None
    tunable: bool = True
    min: int | float | None = None
    max: int | float | None = None
    step: int | float | None = None
    enum_values: tuple[str, ...] | None = None
    # Optional explicit grid values (useful for optimization in PH5).
    grid_values: tuple[Any, ...] | None = None


@dataclass(frozen=True)
class SignalResult:
    """Structured, vectorized signal outputs returned by strategies.

    Strategies are pure signal generators. They output:
    - entry/exit signals (vectorized boolean Series)
    - indicator overlays (DataFrame / Series)
    - optional stop-loss / take-profit series
    - optional metadata for later explanation/visualization
    """

    timestamp: pd.Series
    indicators: pd.DataFrame
    long_entry: pd.Series
    long_exit: pd.Series
    short_entry: pd.Series
    short_exit: pd.Series
    stop_loss: pd.Series | None = None
    take_profit: pd.Series | None = None
    metadata: dict[str, Any] | None = None

    def to_frame(self) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "timestamp": self.timestamp,
                "long_entry": self.long_entry.astype(bool),
                "long_exit": self.long_exit.astype(bool),
                "short_entry": self.short_entry.astype(bool),
                "short_exit": self.short_exit.astype(bool),
            }
        )
        if self.stop_loss is not None:
            df["stop_loss"] = self.stop_loss
        if self.take_profit is not None:
            df["take_profit"] = self.take_profit
        if self.indicators is not None and not self.indicators.empty:
            # Avoid column collisions by keeping indicator names distinct.
            df = pd.concat([df.reset_index(drop=True), self.indicators.reset_index(drop=True)], axis=1)
        return df


# Backward-compatible alias for earlier PH3 work (deprecated).
StrategySignals = SignalResult
