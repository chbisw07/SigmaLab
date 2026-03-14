from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy, StrategyParams
from indicators import atr, ema, rsi
from strategies.models import ParameterSpec, StrategyCategory, StrategyMetadata, StrategySignals
from strategies.utils import cross_above, cross_below, normalize_signal_frame


class SwingTrendPullbackStrategy(BaseStrategy):
    """Simple swing trend + pullback entry with EMA trend filter.

    This is a PH3 reference strategy intended to validate the strategy contract.
    """

    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="Swing Trend Pullback",
            slug="swing_trend_pullback",
            description="Trend filter via EMA; enter on pullback reclaim; exit on trend break.",
            category=StrategyCategory.SWING,
            timeframe="1D",
            long_only=True,
            version="0.1.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                key="ema_fast",
                label="Fast EMA Period",
                type="int",
                default=20,
                min=2,
                max=200,
                step=1,
                description="Fast EMA used for pullback reclaim and exit.",
            ),
            ParameterSpec(
                key="ema_slow",
                label="Slow EMA Period",
                type="int",
                default=50,
                min=3,
                max=300,
                step=1,
                description="Slow EMA trend filter.",
            ),
            ParameterSpec(
                key="rsi_period",
                label="RSI Period",
                type="int",
                default=14,
                min=2,
                max=50,
                step=1,
            ),
            ParameterSpec(
                key="rsi_entry_max",
                label="RSI Max For Entry",
                type="float",
                default=55.0,
                min=1.0,
                max=100.0,
                step=0.5,
            ),
            ParameterSpec(
                key="rsi_exit_min",
                label="RSI Min For Exit",
                type="float",
                default=65.0,
                min=1.0,
                max=100.0,
                step=0.5,
                tunable=False,
            ),
            ParameterSpec(
                key="use_atr_stop",
                label="Enable ATR Stop",
                type="bool",
                default=False,
                tunable=False,
            ),
            ParameterSpec(
                key="atr_period",
                label="ATR Period",
                type="int",
                default=14,
                min=2,
                max=50,
                step=1,
                tunable=False,
            ),
            ParameterSpec(
                key="atr_mult",
                label="ATR Multiplier",
                type="float",
                default=2.0,
                min=0.5,
                max=10.0,
                step=0.25,
                tunable=False,
            ),
        ]

    def generate_signals(self, candles: pd.DataFrame, params: StrategyParams) -> StrategySignals:
        self._validate_input(candles)
        df = candles.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        df = df.sort_values("timestamp").reset_index(drop=True)

        close = df["close"].astype("float64")
        high = df["high"].astype("float64")
        low = df["low"].astype("float64")

        ema_fast = ema(close, int(params.values["ema_fast"]))
        ema_slow = ema(close, int(params.values["ema_slow"]))
        r = rsi(close, int(params.values["rsi_period"]))

        trend = close > ema_slow
        reclaim = cross_above(close, ema_fast)
        entry = trend & reclaim & (r < float(params.values["rsi_entry_max"]))

        exit_trend_break = cross_below(close, ema_fast)
        exit_rsi = r > float(params.values["rsi_exit_min"])
        exit_ = exit_trend_break | exit_rsi

        out = pd.DataFrame(
            {
                "timestamp": df["timestamp"],
                "long_entry": entry,
                "long_exit": exit_,
                "short_entry": False,
                "short_exit": False,
                "ema_fast": ema_fast,
                "ema_slow": ema_slow,
                "rsi": r,
            }
        )

        if bool(params.values["use_atr_stop"]):
            a = atr(high, low, close, int(params.values["atr_period"]))
            out["long_stop"] = close - (a * float(params.values["atr_mult"]))
        else:
            out["long_stop"] = pd.NA

        out = normalize_signal_frame(out)
        return StrategySignals(frame=out)
