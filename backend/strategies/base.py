from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategies.context import IndicatorContext, StrategyContext
from strategies.models import ParameterSpec, SignalResult, StrategyMetadata


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

    def compute_indicators(
        self,
        data: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
        indicators: IndicatorContext | None = None,
    ) -> pd.DataFrame:
        """Compute indicator overlays for this strategy.

        Strategies should compute indicators via shared indicator functions and reuse them
        through the provided `indicators` cache context.

        Important caching rule:
        - the cache key passed to `indicators.get(key, ...)` must include any indicator-specific
          parameters (e.g. period) so PH5 parameter sweeps can reuse unaffected indicators.
        """
        _ = (params, context, indicators)
        return pd.DataFrame()

    def generate_signals_from_indicators(
        self,
        data: pd.DataFrame,
        *,
        indicators_df: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
    ) -> SignalResult:
        """Generate entry/exit signals from candles + computed indicators."""
        raise NotImplementedError("Strategy must implement generate_signals_from_indicators() or override generate_signals()")

    def generate_signals(
        self,
        data: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
        indicators: IndicatorContext | None = None,
    ) -> SignalResult:
        """Default evaluation path (PH4 optimization-readiness).

        This preserves the "pure signal generator" rule while making it possible to:
        - compute indicators once
        - reuse them across parameter evaluations (PH5)
        - keep trade simulation in PH4 (not in strategies)
        """
        self._validate_input(data)
        df = self._normalize_candles(data)
        ind_df = self.compute_indicators(df, params, context=context, indicators=indicators)
        return self.generate_signals_from_indicators(
            df,
            indicators_df=ind_df,
            params=params,
            context=context,
        )

    def _validate_input(self, data: pd.DataFrame) -> None:
        _require_candle_columns(data)

    def _normalize_candles(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        return df.sort_values("timestamp").reset_index(drop=True)
