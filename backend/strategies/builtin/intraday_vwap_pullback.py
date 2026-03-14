from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy, StrategyParams
from strategies.context import IndicatorContext, StrategyContext
from indicators import rsi, vwap
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata
from strategies.utils import cross_above, cross_below


class IntradayVWAPPullbackStrategy(BaseStrategy):
    """Intraday VWAP pullback entry.

    This is a PH3 reference strategy intended to validate the strategy contract.
    """

    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="Intraday VWAP Pullback",
            slug="intraday_vwap_pullback",
            description="Enter on reclaim above VWAP; exit on VWAP loss or RSI exhaustion.",
            category=StrategyCategory.INTRADAY,
            timeframe="15m",
            long_only=True,
            version="0.1.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
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
                default=60.0,
                min=1.0,
                max=100.0,
                step=0.5,
            ),
            ParameterSpec(
                key="rsi_exit_min",
                label="RSI Min For Exit",
                type="float",
                default=70.0,
                min=1.0,
                max=100.0,
                step=0.5,
                tunable=False,
            ),
            ParameterSpec(
                key="vwap_buffer_pct",
                label="VWAP Buffer (%)",
                type="float",
                default=0.0,
                min=0.0,
                max=2.0,
                step=0.05,
                description="Optional buffer above VWAP for entry confirmation.",
            ),
        ]

    def generate_signals(
        self,
        data: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
        indicators: IndicatorContext | None = None,
    ) -> SignalResult:
        self._validate_input(data)
        df = data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        df = df.sort_values("timestamp").reset_index(drop=True)

        close = df["close"].astype("float64")
        ic = indicators or IndicatorContext()
        rsi_period = int(params.values["rsi_period"])
        vw = ic.get(("vwap",), lambda: vwap(df))
        r = ic.get(("rsi", "close", rsi_period), lambda: rsi(close, rsi_period))

        buffer_pct = float(params.values["vwap_buffer_pct"]) / 100.0
        entry_line = vw * (1.0 + buffer_pct)

        entry = (cross_above(close, entry_line) & (r < float(params.values["rsi_entry_max"]))).fillna(False).astype(bool)
        exit_ = (cross_below(close, vw) | (r > float(params.values["rsi_exit_min"]))).fillna(False).astype(bool)

        ind_df = pd.DataFrame({"vwap": vw, "rsi": r})
        false_s = pd.Series(False, index=entry.index)
        return SignalResult(
            timestamp=df["timestamp"],
            indicators=ind_df,
            long_entry=entry,
            long_exit=exit_,
            short_entry=false_s,
            short_exit=false_s,
            stop_loss=None,
            take_profit=None,
            metadata={"context": context.__dict__ if context else None},
        )
