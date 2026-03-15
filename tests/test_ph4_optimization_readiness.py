from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pandas as pd

from app.backtesting.indicator_cache import IndicatorCache
from app.backtesting.prepared_input import normalize_candles
from app.backtesting.strategy_evaluator import StrategyEvaluator
from strategies.base import BaseStrategy, StrategyParams
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata
from strategies.builtin import IntradayVWAPPullbackStrategy, SwingTrendPullbackStrategy


def _candles_unsorted() -> pd.DataFrame:
    t0 = datetime(2026, 1, 1, 9, 15)
    ts = [t0 + timedelta(minutes=m) for m in [30, 0, 15]]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1.0, 1.0, 1.0],
            "high": [1.0, 1.0, 1.0],
            "low": [1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0],
            "volume": [1, 1, 1],
        }
    )


def test_normalize_candles_sorts_and_shapes() -> None:
    df = _candles_unsorted()
    out = normalize_candles(df)
    assert list(out.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert out["timestamp"].is_monotonic_increasing


def test_indicator_cache_scoped_hits_and_param_isolation() -> None:
    cache = IndicatorCache()
    inst = uuid.uuid4()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return pd.Series([1, 2, 3])

    scoped1 = cache.scoped(instrument_id=inst, timeframe="1h", params={"p": 1})
    a = scoped1.get(("x", 1), compute)
    b = scoped1.get(("x", 1), compute)
    assert calls["n"] == 1
    assert a.equals(b)

    scoped2 = cache.scoped(instrument_id=inst, timeframe="1h", params={"p": 2})
    _ = scoped2.get(("x", 1), compute)
    assert calls["n"] == 2


class _CacheCountingStrategy(BaseStrategy):
    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="Cache Counting",
            slug="cache_counting",
            description="",
            category=StrategyCategory.SWING,
            timeframe="1h",
            version="0.0.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return []

    def __init__(self) -> None:
        self.indicator_computes = 0

    def compute_indicators(self, data: pd.DataFrame, params: StrategyParams, context=None, indicators=None) -> pd.DataFrame:  # type: ignore[override]
        close = data["close"].astype("float64")
        ic = indicators

        def _compute():
            self.indicator_computes += 1
            return close.rolling(2).mean()

        assert ic is not None
        ma2 = ic.get(("ma2",), _compute)
        return pd.DataFrame({"ma2": ma2})

    def generate_signals_from_indicators(  # type: ignore[override]
        self, data: pd.DataFrame, *, indicators_df: pd.DataFrame, params: StrategyParams, context=None
    ) -> SignalResult:
        ma2 = indicators_df["ma2"]
        entry = (ma2.notna() & (data["close"] > ma2)).fillna(False).astype(bool)
        false_s = pd.Series(False, index=entry.index)
        return SignalResult(
            timestamp=data["timestamp"],
            indicators=indicators_df,
            long_entry=entry,
            long_exit=false_s,
            short_entry=false_s,
            short_exit=false_s,
        )


def test_strategy_evaluator_reuses_indicator_cache_across_calls() -> None:
    candles = normalize_candles(_candles_unsorted())
    cache = IndicatorCache()
    evaluator = StrategyEvaluator(indicator_cache=cache)
    strat = _CacheCountingStrategy()
    inst = uuid.uuid4()
    params = StrategyParams(values={})

    _ = evaluator.evaluate(strategy=strat, instrument_id=inst, symbol="X", timeframe="1h", candles=candles, params=params)
    _ = evaluator.evaluate(strategy=strat, instrument_id=inst, symbol="X", timeframe="1h", candles=candles, params=params)
    assert strat.indicator_computes == 1


def test_builtin_strategy_evaluator_matches_direct_generate_signals() -> None:
    candles = _candles_unsorted()
    inst = uuid.uuid4()
    cache = IndicatorCache()
    evaluator = StrategyEvaluator(indicator_cache=cache)

    strat = SwingTrendPullbackStrategy()
    params = StrategyParams(
        values={
            "ema_fast": 2,
            "ema_slow": 3,
            "rsi_period": 2,
            "rsi_entry_max": 100.0,
            "rsi_exit_min": 0.0,
            "use_atr_stop": False,
            "atr_period": 2,
            "atr_mult": 2.0,
        }
    )
    direct = strat.generate_signals(candles, params).to_frame()
    via_eval = evaluator.evaluate(
        strategy=strat,
        instrument_id=inst,
        symbol="X",
        timeframe="1D",
        candles=candles,
        params=params,
    ).to_frame()
    pd.testing.assert_frame_equal(direct, via_eval, check_dtype=False)

    strat2 = IntradayVWAPPullbackStrategy()
    params2 = StrategyParams(
        values={
            "rsi_period": 2,
            "rsi_entry_max": 100.0,
            "rsi_exit_min": 0.0,
            "vwap_buffer_pct": 0.0,
        }
    )
    direct2 = strat2.generate_signals(candles, params2).to_frame()
    via_eval2 = evaluator.evaluate(
        strategy=strat2,
        instrument_id=inst,
        symbol="X",
        timeframe="15m",
        candles=candles,
        params=params2,
    ).to_frame()
    pd.testing.assert_frame_equal(direct2, via_eval2, check_dtype=False)

