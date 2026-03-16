from __future__ import annotations

import numpy as np
import pandas as pd

from indicators import atr, dmi, rsi
from strategies.base import BaseStrategy, StrategyParams
from strategies.context import IndicatorContext, StrategyContext
from strategies.models import ParameterSpec, SignalResult, StrategyCategory, StrategyMetadata


def _compute_supertrend_dir_and_stops(
    df: pd.DataFrame,
    *,
    atr_period: int,
    atr_multiplier: float,
    use_wicks: bool,
    indicators: IndicatorContext,
) -> pd.DataFrame:
    """Compute SuperTrend stop bands + direction (Pine-compatible, stateful).

    Pine reference:
    - src = hl2
    - atrRaw = ta.atr(length)
    - atrST  = atrRaw * mult
    - highPrice = wicks ? high : close
    - lowPrice  = wicks ? low  : close
    - longStop/shortStop recursion and dir flip rules
    """
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    close = df["close"].astype("float64")

    src = (high + low) / 2.0
    a = indicators.get(("atr", atr_period), lambda: atr(high, low, close, atr_period)).astype("float64")
    atr_st = (a * float(atr_multiplier)).astype("float64")

    high_price = high if use_wicks else close
    low_price = low if use_wicks else close

    src_v = src.to_numpy(dtype="float64", copy=False)
    atr_st_v = atr_st.to_numpy(dtype="float64", copy=False)
    high_v = high_price.to_numpy(dtype="float64", copy=False)
    low_v = low_price.to_numpy(dtype="float64", copy=False)

    n = len(df)
    long_stop = np.full(n, np.nan, dtype="float64")
    short_stop = np.full(n, np.nan, dtype="float64")
    direction = np.full(n, 1, dtype="int64")  # 1 = long, -1 = short

    for i in range(n):
        atr_i = atr_st_v[i]
        src_i = src_v[i]

        # longStopPrev = nz(longStop[1], src - atrST)
        if i > 0 and not np.isnan(long_stop[i - 1]):
            long_stop_prev = long_stop[i - 1]
        else:
            long_stop_prev = src_i - atr_i

        # longStop := (lowPrice[1] > longStopPrev) ? max(src - atrST, longStopPrev) : (src - atrST)
        if i > 0 and not np.isnan(low_v[i - 1]) and not np.isnan(long_stop_prev) and (low_v[i - 1] > long_stop_prev):
            long_stop[i] = max(src_i - atr_i, long_stop_prev)
        else:
            long_stop[i] = src_i - atr_i

        # shortStopPrev = nz(shortStop[1], src + atrST)
        if i > 0 and not np.isnan(short_stop[i - 1]):
            short_stop_prev = short_stop[i - 1]
        else:
            short_stop_prev = src_i + atr_i

        # shortStop := (highPrice[1] < shortStopPrev) ? min(src + atrST, shortStopPrev) : (src + atrST)
        if i > 0 and not np.isnan(high_v[i - 1]) and not np.isnan(short_stop_prev) and (high_v[i - 1] < short_stop_prev):
            short_stop[i] = min(src_i + atr_i, short_stop_prev)
        else:
            short_stop[i] = src_i + atr_i

        if i == 0:
            direction[i] = 1
        else:
            prev_dir = int(direction[i - 1])
            # dir := (dir == -1 and highPrice > shortStopPrev) ? 1 :
            #        (dir == 1  and lowPrice  < longStopPrev)  ? -1 : dir
            if prev_dir == -1 and (not np.isnan(high_v[i])) and (not np.isnan(short_stop_prev)) and (high_v[i] > short_stop_prev):
                direction[i] = 1
            elif prev_dir == 1 and (not np.isnan(low_v[i])) and (not np.isnan(long_stop_prev)) and (low_v[i] < long_stop_prev):
                direction[i] = -1
            else:
                direction[i] = prev_dir

    return pd.DataFrame(
        {
            "atr": a.astype("float64"),
            "supertrend_long_stop": pd.Series(long_stop, index=df.index, dtype="float64"),
            "supertrend_short_stop": pd.Series(short_stop, index=df.index, dtype="float64"),
            "supertrend_dir": pd.Series(direction, index=df.index, dtype="int64"),
        }
    )


class SuperTrendV6ProStrategy(BaseStrategy):
    """SuperTrend direction-flip strategy with optional ADX/RSI filters.

    This is a port of the provided TradingView Pine script (signal logic only).
    Execution routing, qty, and JSON alert payload concerns are intentionally not modeled here.
    """

    @classmethod
    def metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            name="SuperTrend v6 PRO",
            slug="supertrend_v6_pro",
            description="SuperTrend direction flips with optional ADX + RSI filters.",
            category=StrategyCategory.INTRADAY,
            timeframe="15m",
            long_only=False,
            version="0.1.0",
        )

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                key="atr_period",
                label="ATR Period",
                type="int",
                default=22,
                min=1,
                max=100,
                step=1,
            ),
            ParameterSpec(
                key="atr_multiplier",
                label="ATR Multiplier",
                type="float",
                default=3.0,
                min=0.1,
                max=20.0,
                step=0.1,
            ),
            ParameterSpec(
                key="use_wicks",
                label="Use Wicks",
                type="bool",
                default=True,
                tunable=False,
            ),
            ParameterSpec(
                key="trade_mode",
                label="Trade Direction",
                type="enum",
                default="Both",
                enum_values=("Long only", "Short only", "Both"),
                tunable=False,
                description="Controls whether long/short entries are emitted. Flip exits are always emitted.",
            ),
            ParameterSpec(
                key="use_adx_filter",
                label="Use ADX Filter",
                type="bool",
                default=True,
                tunable=False,
            ),
            ParameterSpec(
                key="dmi_len",
                label="DMI Length (DI)",
                type="int",
                default=14,
                min=1,
                max=100,
                step=1,
            ),
            ParameterSpec(
                key="adx_smoothing",
                label="ADX Smoothing",
                type="int",
                default=14,
                min=1,
                max=100,
                step=1,
            ),
            ParameterSpec(
                key="adx_min",
                label="ADX Min",
                type="float",
                default=18.0,
                min=0.0,
                max=100.0,
                step=0.5,
            ),
            ParameterSpec(
                key="use_rsi_filter",
                label="Use RSI Filter",
                type="bool",
                default=True,
                tunable=False,
            ),
            ParameterSpec(
                key="rsi_len",
                label="RSI Length",
                type="int",
                default=14,
                min=1,
                max=100,
                step=1,
            ),
            ParameterSpec(
                key="rsi_min_long",
                label="RSI Min for Long",
                type="float",
                default=55.0,
                min=0.0,
                max=100.0,
                step=0.5,
            ),
            ParameterSpec(
                key="rsi_max_short",
                label="RSI Max for Short",
                type="float",
                default=45.0,
                min=0.0,
                max=100.0,
                step=0.5,
            ),
        ]

    def compute_indicators(
        self,
        data: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
        indicators: IndicatorContext | None = None,
    ) -> pd.DataFrame:
        _ = context
        df = data
        ic = indicators or IndicatorContext()

        atr_period = int(params.values["atr_period"])
        atr_multiplier = float(params.values["atr_multiplier"])
        use_wicks = bool(params.values["use_wicks"])

        st_df = ic.get(
            ("supertrend_v6_pro", "hl2", atr_period, atr_multiplier, use_wicks),
            lambda: _compute_supertrend_dir_and_stops(
                df,
                atr_period=atr_period,
                atr_multiplier=atr_multiplier,
                use_wicks=use_wicks,
                indicators=ic,
            ),
        )

        high = df["high"].astype("float64")
        low = df["low"].astype("float64")
        close = df["close"].astype("float64")

        dmi_len = int(params.values["dmi_len"])
        adx_smoothing = int(params.values["adx_smoothing"])
        dmi_df = ic.get(
            ("dmi", dmi_len, adx_smoothing),
            lambda: pd.DataFrame(
                dict(
                    zip(
                        ("plus_di", "minus_di", "adx"),
                        dmi(high, low, close, di_len=dmi_len, adx_smoothing=adx_smoothing),
                    )
                )
            ),
        )

        rsi_len = int(params.values["rsi_len"])
        rsi_val = ic.get(("rsi", "close", rsi_len), lambda: rsi(close, rsi_len))

        out = pd.concat(
            [
                st_df.reset_index(drop=True),
                dmi_df.reset_index(drop=True),
                pd.DataFrame({"rsi": pd.Series(rsi_val, index=df.index, dtype="float64")}).reset_index(drop=True),
            ],
            axis=1,
        )
        return out

    def generate_signals_from_indicators(
        self,
        data: pd.DataFrame,
        *,
        indicators_df: pd.DataFrame,
        params: StrategyParams,
        context: StrategyContext | None = None,
    ) -> SignalResult:
        df = data
        dir_s = indicators_df["supertrend_dir"].astype("int64")
        prev_dir = dir_s.shift(1)

        buy_signal = ((dir_s == 1) & (prev_dir == -1)).fillna(False).astype(bool)
        sell_signal = ((dir_s == -1) & (prev_dir == 1)).fillna(False).astype(bool)

        trade_mode = str(params.values["trade_mode"])
        allow_long = trade_mode in {"Both", "Long only"}
        allow_short = trade_mode in {"Both", "Short only"}

        use_adx = bool(params.values["use_adx_filter"])
        use_rsi = bool(params.values["use_rsi_filter"])
        adx_min = float(params.values["adx_min"])
        rsi_min_long = float(params.values["rsi_min_long"])
        rsi_max_short = float(params.values["rsi_max_short"])

        adx_val = indicators_df["adx"].astype("float64")
        rsi_val = indicators_df["rsi"].astype("float64")

        if not use_adx:
            adx_ok = pd.Series(True, index=df.index)
        else:
            adx_ok = (adx_val >= adx_min)

        if not use_rsi:
            rsi_ok_long = pd.Series(True, index=df.index)
            rsi_ok_short = pd.Series(True, index=df.index)
        else:
            rsi_ok_long = (rsi_val >= rsi_min_long)
            rsi_ok_short = (rsi_val <= rsi_max_short)

        long_filters_ok = (adx_ok & rsi_ok_long).fillna(False).astype(bool)
        short_filters_ok = (adx_ok & rsi_ok_short).fillna(False).astype(bool)

        long_entry = (buy_signal & allow_long & long_filters_ok).fillna(False).astype(bool)
        short_entry = (sell_signal & allow_short & short_filters_ok).fillna(False).astype(bool)

        # Flip exits are always emitted (Pine closes on flip regardless of filters).
        long_exit = sell_signal.fillna(False).astype(bool)
        short_exit = buy_signal.fillna(False).astype(bool)

        return SignalResult(
            timestamp=df["timestamp"],
            indicators=indicators_df,
            long_entry=long_entry,
            long_exit=long_exit,
            short_entry=short_entry,
            short_exit=short_exit,
            stop_loss=None,
            take_profit=None,
            metadata={"context": context.__dict__ if context else None},
        )
