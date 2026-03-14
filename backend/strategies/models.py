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


@dataclass(frozen=True)
class StrategySignals:
    """Normalized strategy outputs.

    `frame` must be a DataFrame with a `timestamp` column and boolean signal columns.
    Strategies may also include indicator/overlay columns for later visualization.
    """

    frame: pd.DataFrame
    explanation: dict[str, Any] | None = None

