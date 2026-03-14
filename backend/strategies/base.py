from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategies.models import ParameterSpec, StrategyMetadata, StrategySignals


def _require_candle_columns(df: pd.DataFrame) -> None:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing candle columns: {sorted(missing)}")


@dataclass(frozen=True)
class StrategyParams:
    """Validated params as a plain dict wrapper (keeps contracts simple for PH3)."""

    values: dict[str, Any]


class BaseStrategy(ABC):
    """Base strategy contract for SigmaLab PH3.

    Strategy implementations must be deterministic and side-effect free.
    They must never call broker adapters directly.
    """

    @classmethod
    @abstractmethod
    def metadata(cls) -> StrategyMetadata: ...

    @classmethod
    @abstractmethod
    def parameters(cls) -> list[ParameterSpec]: ...

    @abstractmethod
    def generate_signals(self, candles: pd.DataFrame, params: StrategyParams) -> StrategySignals: ...

    def _validate_input(self, candles: pd.DataFrame) -> None:
        _require_candle_columns(candles)

