from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from data.market_data_service import MarketDataService
from data.timeframe import Timeframe

from strategies.models import StrategySignals
from strategies.service import StrategyService


@dataclass(frozen=True)
class StrategyEngine:
    """Glue layer between strategies and MarketDataService.

    This is not a backtest engine: it only produces signals + indicators.
    """

    market_data: MarketDataService
    strategies: StrategyService

    def generate_signals_for_instrument(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        strategy_slug: str,
        params: dict[str, Any] | None = None,
    ) -> StrategySignals:
        candles = self.market_data.get_candles(
            instrument_id=instrument_id,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        strategy = self.strategies.instantiate(strategy_slug)
        validated = self.strategies.validate(strategy_slug, params)
        return strategy.generate_signals(candles, validated)

