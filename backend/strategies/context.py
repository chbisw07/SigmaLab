from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Hashable

import pandas as pd


@dataclass(frozen=True)
class StrategyContext:
    """Lightweight execution context for future engines (PH4/PH5)."""

    symbol: str | None = None
    timeframe: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


@dataclass
class IndicatorContext:
    """Minimal indicator cache to support parameter-grid evaluation.

    Engines can reuse one IndicatorContext when evaluating many param sets against the same candles.
    Keys should include any inputs that affect the output (e.g., period).
    """

    cache: dict[Hashable, pd.Series | pd.DataFrame] = field(default_factory=dict)

    def get(self, key: Hashable, compute: Callable[[], pd.Series | pd.DataFrame]):
        if key in self.cache:
            return self.cache[key]
        val = compute()
        self.cache[key] = val
        return val

