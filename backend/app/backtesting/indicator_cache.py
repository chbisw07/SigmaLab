from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Hashable

import pandas as pd


def stable_params_hash(params: dict[str, Any] | None) -> str:
    """Stable hash surrogate for params (deterministic across processes).

    We intentionally avoid Python's built-in `hash()` because it is salted per process.
    """
    if not params:
        return "no-params"
    payload = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    # Keep it readable and stable; length is fine for in-memory keys.
    return payload


@dataclass
class IndicatorCache:
    """Local, deterministic indicator cache for backtest/optimization evaluation.

    Keying model is intentionally explicit:
    (instrument_id, timeframe, indicator_key, params_hash)

    The `indicator_key` should include any inputs that influence the output
    (e.g., ("ema","close",20)).
    """

    _cache: dict[Hashable, pd.Series | pd.DataFrame] = field(default_factory=dict)

    def get(
        self,
        *,
        instrument_id: uuid.UUID,
        timeframe: str,
        indicator_key: Hashable,
        params_hash: str,
        compute: Callable[[], pd.Series | pd.DataFrame],
    ) -> pd.Series | pd.DataFrame:
        key = (instrument_id, timeframe, indicator_key, params_hash)
        if key in self._cache:
            return self._cache[key]
        val = compute()
        self._cache[key] = val
        return val

    def scoped(
        self,
        *,
        instrument_id: uuid.UUID,
        timeframe: str,
        params: dict[str, Any] | None = None,
    ) -> "ScopedIndicatorContext":
        return ScopedIndicatorContext(
            cache=self,
            instrument_id=instrument_id,
            timeframe=timeframe,
            params_hash=stable_params_hash(params),
        )


@dataclass(frozen=True)
class ScopedIndicatorContext:
    """Adapter that mimics the StrategyEngine's IndicatorContext `.get()` API.

    Existing strategies already use tuple keys like ("ema","close",period). This wrapper
    prefixes them with (instrument_id, timeframe, params_hash) for safe reuse.
    """

    cache: IndicatorCache
    instrument_id: uuid.UUID
    timeframe: str
    params_hash: str

    def get(self, key: Hashable, compute: Callable[[], pd.Series | pd.DataFrame]):
        return self.cache.get(
            instrument_id=self.instrument_id,
            timeframe=self.timeframe,
            indicator_key=key,
            params_hash=self.params_hash,
            compute=compute,
        )

