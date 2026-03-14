from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd

from strategies.defaults import get_default_registry
from strategies.service import StrategyService


def _daily_sample() -> pd.DataFrame:
    closes = [10, 10, 10, 12, 12, 12, 9]
    ts0 = datetime(2026, 3, 1)
    rows = []
    for i, c in enumerate(closes):
        rows.append(
            {
                "timestamp": ts0 + timedelta(days=i),
                "open": c,
                "high": c + 0.5,
                "low": c - 0.5,
                "close": c,
                "volume": 100,
            }
        )
    return pd.DataFrame(rows)


def _intraday_sample() -> pd.DataFrame:
    closes = [100, 100, 100, 102, 102, 98]
    ts0 = datetime(2026, 3, 14, 9, 15)
    rows = []
    for i, c in enumerate(closes):
        rows.append(
            {
                "timestamp": ts0 + timedelta(minutes=15 * i),
                "open": c,
                "high": c,
                "low": c,
                "close": c,
                "volume": 10,
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="SigmaLab PH3 sanity script: strategy engine")
    p.add_argument("--slug", default="swing_trend_pullback", help="Strategy slug")
    args = p.parse_args(argv)

    svc = StrategyService.default()
    detail = svc.get_detail(args.slug)

    print(f"[ok] strategy: {detail.metadata.slug} ({detail.metadata.name})")
    print(f"[ok] category={detail.metadata.category.value} timeframe={detail.metadata.timeframe}")
    print(f"[ok] params: {[p.key for p in detail.parameters]}")

    # Minimal override to reduce warm-up for the sample dataset.
    overrides = {}
    if args.slug == "swing_trend_pullback":
        overrides = {"ema_fast": 2, "ema_slow": 3, "rsi_period": 2, "rsi_entry_max": 100.0, "rsi_exit_min": 1.0}
        candles = _daily_sample()
    elif args.slug == "intraday_vwap_pullback":
        overrides = {"rsi_period": 2, "rsi_entry_max": 100.0, "rsi_exit_min": 1.0, "vwap_buffer_pct": 0.0}
        candles = _intraday_sample()
    else:
        candles = _daily_sample()

    params = svc.validate(args.slug, overrides)
    strat = svc.instantiate(args.slug)
    out = strat.generate_signals(candles, params).frame

    le = int(out["long_entry"].sum())
    lx = int(out["long_exit"].sum())
    print(f"[ok] long_entry signals: {le}")
    print(f"[ok] long_exit signals:  {lx}")
    print("[ok] output columns:", list(out.columns))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
