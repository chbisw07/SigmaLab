from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime

from sqlalchemy import text

from app.core.db import Database
from app.core.settings import get_settings
from app.services.backtests import BacktestRunService
from app.services.repos.backtests import BacktestRepository


def _parse_dt(s: str) -> datetime:
    # Accept ISO 8601-ish formats like 2026-01-01 or 2026-01-01T09:15:00
    try:
        return datetime.fromisoformat(s)
    except ValueError as e:
        raise SystemExit(f"Invalid datetime: {s!r} (use ISO format)") from e


def main() -> int:
    p = argparse.ArgumentParser(description="PH4 sanity: run a backtest and print summary/trades.")
    p.add_argument("--watchlist-id", required=True, help="UUID of an existing watchlist in the DB")
    p.add_argument("--strategy-slug", default="swing_trend_pullback")
    p.add_argument("--timeframe", default="1D", help="e.g. 15m, 45m, 1h, 1D")
    p.add_argument("--start", required=True, help="ISO datetime, e.g. 2026-01-01")
    p.add_argument("--end", required=True, help="ISO datetime, e.g. 2026-03-01")
    p.add_argument("--params", default="{}", help="Strategy params as JSON (optional)")
    args = p.parse_args()

    settings = get_settings()
    db = Database.from_settings(settings)

    watchlist_id = uuid.UUID(args.watchlist_id)
    start = _parse_dt(args.start)
    end = _parse_dt(args.end)
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--params must be valid JSON: {e}") from e
    if not isinstance(params, dict):
        raise SystemExit("--params must be a JSON object/dict")

    with db.session() as session:
        svc = BacktestRunService.from_settings(session, settings=settings)
        res = svc.run(
            strategy_slug=args.strategy_slug,
            watchlist_id=watchlist_id,
            timeframe=args.timeframe,
            start=start,
            end=end,
            params=params,
        )

        repo = BacktestRepository(session)
        trades = repo.list_trades(res.run_id, limit=20)
        metrics = repo.list_metrics(res.run_id)

        print("run_id:", res.run_id)
        print("status:", res.status)
        print("overall_metrics:", res.overall_metrics)
        print("metrics_rows:", len(metrics))
        print("sample_trades:", len(trades))
        for t in trades[:10]:
            print(
                {
                    "symbol": t.symbol,
                    "entry_ts": t.entry_ts,
                    "exit_ts": t.exit_ts,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl_pct": t.pnl_pct,
                    "close_reason": t.close_reason,
                }
            )

        # Quick DB sanity counts.
        n_trades = session.execute(text("select count(*) from backtest_trades where run_id = :id"), {"id": res.run_id}).scalar_one()
        n_metrics = session.execute(text("select count(*) from backtest_metrics where run_id = :id"), {"id": res.run_id}).scalar_one()
        print("persisted backtest_trades:", n_trades)
        print("persisted backtest_metrics:", n_metrics)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
