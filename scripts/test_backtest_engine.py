from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timedelta

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
    p.add_argument("--watchlist-id", required=False, help="UUID of an existing watchlist in the DB")
    p.add_argument(
        "--list-watchlists",
        action="store_true",
        help="List available watchlists and exit",
    )
    p.add_argument("--strategy-slug", default="swing_trend_pullback")
    p.add_argument("--timeframe", default="1D", help="e.g. 15m, 45m, 1h, 1D")
    p.add_argument(
        "--start",
        required=False,
        help="ISO datetime, e.g. 2026-01-01 (default: 30 days ago, local time)",
    )
    p.add_argument(
        "--end",
        required=False,
        help="ISO datetime, e.g. 2026-03-01 (default: now, local time)",
    )
    p.add_argument("--params", default="{}", help="Strategy params as JSON (optional)")
    args = p.parse_args()

    settings = get_settings()
    db = Database.from_settings(settings)

    now = datetime.now()
    start = _parse_dt(args.start) if args.start else (now - timedelta(days=30))
    end = _parse_dt(args.end) if args.end else now
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--params must be valid JSON: {e}") from e
    if not isinstance(params, dict):
        raise SystemExit("--params must be a JSON object/dict")

    with db.session() as session:
        # Helper: list watchlists for the user.
        if args.list_watchlists or not args.watchlist_id:
            rows = session.execute(text("select id, name from watchlists order by created_at desc limit 50")).all()
            if rows:
                print("Available watchlists:")
                for r in rows:
                    print(f"  {r.id}  {r.name}")
            else:
                print("No watchlists found in DB yet.")

            if args.list_watchlists:
                return 0

            print()
            print("Missing required --watchlist-id.")
            print("Example:")
            print(
                ".venv/bin/python scripts/test_backtest_engine.py "
                "--watchlist-id <WATCHLIST_UUID> "
                f"--strategy-slug {args.strategy_slug} "
                f"--timeframe {args.timeframe} "
                f"--start {start.date().isoformat()} "
                f"--end {end.date().isoformat()}"
            )
            return 2

        watchlist_id = uuid.UUID(args.watchlist_id)
        svc = BacktestRunService.from_settings(session, settings=settings)
        try:
            result = svc.run(
                strategy_slug=args.strategy_slug,
                watchlist_id=watchlist_id,
                timeframe=args.timeframe,
                start=start,
                end=end,
                params=params,
            )
        except Exception as e:
            msg = str(e)
            print("Backtest failed.")
            print("Error:", msg)
            if "invalid token" in msg.lower():
                print()
                print("This usually means the instrument token sent to Kite is not valid.")
                print("In SigmaLab, `Instrument.broker_instrument_token` must be the numeric Kite instrument_token.")
                print("Check your watchlist items:")
                print(f"  curl http://127.0.0.1:8000/watchlists/{watchlist_id}/items")
                print("If `broker_instrument_token` looks like 'NSE:SYMBOL' (non-numeric), resync instruments and re-add the correct Instrument UUIDs.")
            raise

        repo = BacktestRepository(session)
        n_trades = session.execute(
            text("select count(*) from backtest_trades where run_id = :id"),
            {"id": result.run_id},
        ).scalar_one()
        # Per-symbol metric rows are stored with symbol != null.
        n_symbols = session.execute(
            text("select count(*) from backtest_metrics where run_id = :id and symbol is not null"),
            {"id": result.run_id},
        ).scalar_one()

        m = result.overall_metrics or {}
        win_rate = float(m.get("win_rate", 0.0)) * 100.0
        profit_factor = float(m.get("profit_factor", 0.0))
        max_dd = float(m.get("max_drawdown_pct", 0.0)) * 100.0

        print("Backtest completed")
        print(f"Strategy: {args.strategy_slug}")
        print(f"Symbols: {int(n_symbols)}")
        print(f"Trades: {int(n_trades)}")
        print(f"Win rate: {win_rate:.0f}%")
        print(f"Profit factor: {profit_factor:.2f}")
        print(f"Max drawdown: {max_dd:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
