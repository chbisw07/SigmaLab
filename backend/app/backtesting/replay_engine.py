from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.backtesting.models import CloseReason, ExecutionAssumptions, EquityPoint, ReplayResult, Trade
from strategies.models import SignalResult, StrategyMetadata


def _require_sorted_unique(df: pd.DataFrame) -> None:
    if df.empty:
        return
    ts = pd.to_datetime(df["timestamp"], utc=False)
    if not ts.is_monotonic_increasing:
        raise ValueError("candles must be sorted by timestamp ascending")
    if ts.duplicated().any():
        raise ValueError("candles must not contain duplicate timestamps")


@dataclass(frozen=True)
class ReplayEngine:
    """Deterministic replay/simulation engine (PH4).

    Strategies emit vectorized signals; this engine turns signals into trades.
    """

    assumptions: ExecutionAssumptions = ExecutionAssumptions()

    def run(
        self,
        candles: pd.DataFrame,
        signals: SignalResult,
        *,
        metadata: StrategyMetadata,
        symbol: str,
        instrument_id: uuid.UUID | None = None,
        run_id: uuid.UUID | None = None,
    ) -> ReplayResult:
        if candles.empty:
            return ReplayResult(trades=[], equity_curve=[])

        _require_sorted_unique(candles)

        df = candles.reset_index(drop=True).copy()
        for col in ("open", "high", "low", "close"):
            df[col] = df[col].astype(float)

        # Align signal arrays to candle rows by position. PH3 strategies are expected
        # to generate signals over the same candle dataframe passed to them.
        n = len(df)
        if len(signals.long_entry) != n or len(signals.long_exit) != n:
            raise ValueError("signal lengths must match candle length")

        long_entry = pd.Series(signals.long_entry).fillna(False).astype(bool).reset_index(drop=True)
        long_exit = pd.Series(signals.long_exit).fillna(False).astype(bool).reset_index(drop=True)
        stop_loss = None
        take_profit = None
        if signals.stop_loss is not None:
            stop_loss = pd.Series(signals.stop_loss).reset_index(drop=True)
        if signals.take_profit is not None:
            take_profit = pd.Series(signals.take_profit).reset_index(drop=True)

        # Simulation state (single position, long-only for v1).
        in_pos = False
        entry_ts: datetime | None = None
        entry_price: float | None = None
        entry_idx: int | None = None
        quantity = 1.0
        cash_equity = 1.0
        trades: list[Trade] = []
        equity_curve: list[EquityPoint] = []

        def mark_to_market(i: int) -> float:
            nonlocal cash_equity
            if not in_pos or entry_price is None:
                return cash_equity
            return cash_equity * (float(df.loc[i, "close"]) / float(entry_price))

        for i in range(n):
            ts_i = df.loc[i, "timestamp"]
            # Next-bar execution: signals at i-1 execute at the open of i.
            if i > 0:
                if (not in_pos) and bool(long_entry.iloc[i - 1]):
                    in_pos = True
                    entry_ts = ts_i
                    entry_price = float(df.loc[i, "open"])
                    entry_idx = i

                if in_pos and bool(long_exit.iloc[i - 1]):
                    exit_ts = ts_i
                    exit_price = float(df.loc[i, "open"])
                    assert entry_ts is not None and entry_price is not None and entry_idx is not None
                    holding_period_sec = int((exit_ts - entry_ts).total_seconds())
                    holding_period_bars = int(max(1, i - entry_idx + 1))
                    pnl = (exit_price - entry_price) * quantity
                    pnl_pct = (exit_price / entry_price) - 1.0
                    cash_equity = cash_equity * (exit_price / entry_price)
                    trades.append(
                        Trade(
                            run_id=run_id,
                            instrument_id=instrument_id,
                            symbol=symbol,
                            side="long",
                            quantity=quantity,
                            entry_ts=entry_ts,
                            exit_ts=exit_ts,
                            holding_period_sec=holding_period_sec,
                            holding_period_bars=holding_period_bars,
                            entry_price=entry_price,
                            exit_price=exit_price,
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                            entry_reason="signal_entry",
                            close_reason=CloseReason.SIGNAL_EXIT,
                        )
                    )
                    in_pos = False
                    entry_ts = None
                    entry_price = None
                    entry_idx = None

            # Intrabar stop-loss / take-profit checks on the current bar.
            if in_pos and entry_price is not None and entry_ts is not None:
                low = float(df.loc[i, "low"])
                high = float(df.loc[i, "high"])

                stop_lvl = None if stop_loss is None else stop_loss.iloc[i]
                target_lvl = None if take_profit is None else take_profit.iloc[i]
                stop_hit = stop_lvl is not None and pd.notna(stop_lvl) and low <= float(stop_lvl)
                target_hit = target_lvl is not None and pd.notna(target_lvl) and high >= float(target_lvl)

                reason: CloseReason | None = None
                exit_price: float | None = None
                if stop_hit and target_hit:
                    if self.assumptions.stop_vs_target_precedence == "stop_first":
                        reason = CloseReason.STOP_LOSS
                        exit_price = float(stop_lvl)  # type: ignore[arg-type]
                    else:
                        reason = CloseReason.TARGET_HIT
                        exit_price = float(target_lvl)  # type: ignore[arg-type]
                elif stop_hit:
                    reason = CloseReason.STOP_LOSS
                    exit_price = float(stop_lvl)  # type: ignore[arg-type]
                elif target_hit:
                    reason = CloseReason.TARGET_HIT
                    exit_price = float(target_lvl)  # type: ignore[arg-type]

                if reason is not None and exit_price is not None:
                    exit_ts = df.loc[i, "timestamp"]
                    assert entry_idx is not None
                    holding_period_sec = int((exit_ts - entry_ts).total_seconds())
                    holding_period_bars = int(max(1, i - entry_idx + 1))
                    pnl = (exit_price - entry_price) * quantity
                    pnl_pct = (exit_price / entry_price) - 1.0
                    cash_equity = cash_equity * (exit_price / entry_price)
                    trades.append(
                        Trade(
                            run_id=run_id,
                            instrument_id=instrument_id,
                            symbol=symbol,
                            side="long",
                            quantity=quantity,
                            entry_ts=entry_ts,
                            exit_ts=exit_ts,
                            holding_period_sec=holding_period_sec,
                            holding_period_bars=holding_period_bars,
                            entry_price=entry_price,
                            exit_price=exit_price,
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                            entry_reason="signal_entry",
                            close_reason=reason,
                        )
                    )
                    in_pos = False
                    entry_ts = None
                    entry_price = None
                    entry_idx = None

            equity_curve.append(EquityPoint(timestamp=ts_i, equity=mark_to_market(i)))

        # Force-close any open position at end of series.
        if in_pos and entry_price is not None and entry_ts is not None:
            ts_last = df.loc[n - 1, "timestamp"]
            exit_price = float(df.loc[n - 1, "close"])
            assert entry_idx is not None
            holding_period_sec = int((ts_last - entry_ts).total_seconds())
            holding_period_bars = int(max(1, (n - 1) - entry_idx + 1))
            pnl = (exit_price - entry_price) * quantity
            pnl_pct = (exit_price / entry_price) - 1.0
            cash_equity = cash_equity * (exit_price / entry_price)

            close_reason = (
                CloseReason.INTRADAY_SQUAREOFF
                if metadata.category.value == "intraday"
                else CloseReason.TIME_EXIT
            )
            trades.append(
                Trade(
                    run_id=run_id,
                    instrument_id=instrument_id,
                    symbol=symbol,
                    side="long",
                    quantity=quantity,
                    entry_ts=entry_ts,
                    exit_ts=ts_last,
                    holding_period_sec=holding_period_sec,
                    holding_period_bars=holding_period_bars,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    entry_reason="signal_entry",
                    close_reason=close_reason,
                )
            )

        return ReplayResult(trades=trades, equity_curve=equity_curve)
