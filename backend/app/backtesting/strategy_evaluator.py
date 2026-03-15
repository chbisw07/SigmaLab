from __future__ import annotations

import uuid
from dataclasses import dataclass

import pandas as pd

from app.backtesting.indicator_cache import IndicatorCache
from app.backtesting.prepared_input import normalize_candles
from strategies.base import BaseStrategy, StrategyParams
from strategies.context import StrategyContext
from strategies.models import SignalResult


@dataclass(frozen=True)
class StrategyEvaluator:
    """Evaluation layer between prepared market data and simulation.

    This is reusable by both:
    - PH4 backtesting
    - future PH5 optimization (parameter sweeps)
    """

    indicator_cache: IndicatorCache

    def evaluate(
        self,
        *,
        strategy: BaseStrategy,
        instrument_id: uuid.UUID,
        symbol: str,
        timeframe: str,
        candles: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
    ) -> SignalResult:
        df = normalize_candles(candles)
        scoped = self.indicator_cache.scoped(
            instrument_id=instrument_id,
            timeframe=timeframe,
            params=params.values,
        )
        try:
            ind_df = strategy.compute_indicators(df, params, context=context, indicators=scoped)  # type: ignore[arg-type]
            return strategy.generate_signals_from_indicators(
                df,
                indicators_df=ind_df,
                params=params,
                context=context,
            )
        except NotImplementedError:
            # Backward-compatible path for strategies that still implement only `generate_signals(...)`.
            return strategy.generate_signals(df, params, context=context, indicators=scoped)  # type: ignore[arg-type]
