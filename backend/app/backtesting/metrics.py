from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.backtesting.models import DrawdownPoint, EquityPoint, Trade


@dataclass(frozen=True)
class MetricsResult:
    metrics: dict[str, Any]
    equity_curve: list[EquityPoint]
    drawdown_curve: list[DrawdownPoint]


def compute_drawdown(equity_curve: list[EquityPoint]) -> list[DrawdownPoint]:
    if not equity_curve:
        return []
    equity = pd.Series([p.equity for p in equity_curve], dtype="float64")
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    return [
        DrawdownPoint(timestamp=equity_curve[i].timestamp, drawdown=float(dd.iloc[i]))
        for i in range(len(equity_curve))
    ]


def compute_metrics(trades: list[Trade], equity_curve: list[EquityPoint]) -> MetricsResult:
    total_trades = len(trades)
    wins = [t for t in trades if t.pnl_pct > 0]
    losses = [t for t in trades if t.pnl_pct < 0]
    win_rate = (len(wins) / total_trades) if total_trades else 0.0

    avg_win = float(pd.Series([t.pnl_pct for t in wins]).mean()) if wins else 0.0
    avg_loss = float(pd.Series([t.pnl_pct for t in losses]).mean()) if losses else 0.0

    sum_win = float(pd.Series([t.pnl for t in wins]).sum()) if wins else 0.0
    sum_loss = float(pd.Series([t.pnl for t in losses]).sum()) if losses else 0.0

    profit_factor = (sum_win / abs(sum_loss)) if sum_loss != 0 else (float("inf") if sum_win > 0 else 0.0)
    expectancy = (win_rate * avg_win) + ((1.0 - win_rate) * avg_loss)

    end_equity = float(equity_curve[-1].equity) if equity_curve else 1.0
    net_return_pct = end_equity - 1.0

    drawdown_curve = compute_drawdown(equity_curve)
    max_drawdown = float(min([p.drawdown for p in drawdown_curve], default=0.0))

    metrics: dict[str, Any] = {
        "net_return_pct": float(net_return_pct),
        "total_trades": int(total_trades),
        "win_rate": float(win_rate),
        "avg_win_pct": float(avg_win),
        "avg_loss_pct": float(avg_loss),
        "expectancy_pct": float(expectancy),
        "profit_factor": float(profit_factor),
        "max_drawdown_pct": float(max_drawdown),
        "end_equity": float(end_equity),
    }
    return MetricsResult(metrics=metrics, equity_curve=equity_curve, drawdown_curve=drawdown_curve)


def combine_equity_curves(curves: list[list[EquityPoint]]) -> list[EquityPoint]:
    """Combine multiple per-symbol equity curves into an equal-weight portfolio curve.

    Implementation:
    - union all timestamps
    - forward fill per-symbol equity
    - take the mean across symbols
    """
    curves = [c for c in curves if c]
    if not curves:
        return []

    frames = []
    for idx, curve in enumerate(curves):
        frames.append(
            pd.DataFrame(
                {"timestamp": [p.timestamp for p in curve], f"eq_{idx}": [p.equity for p in curve]}
            )
        )

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="timestamp", how="outer")

    merged = merged.sort_values("timestamp").reset_index(drop=True)
    eq_cols = [c for c in merged.columns if c.startswith("eq_")]
    merged[eq_cols] = merged[eq_cols].ffill().fillna(1.0)
    merged["equity"] = merged[eq_cols].mean(axis=1)
    return [
        EquityPoint(timestamp=row.timestamp, equity=float(row.equity))
        for row in merged.itertuples(index=False)
    ]

