from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime

from sqlalchemy import select

from app.core.db import Database
from app.core.settings import get_settings
from app.models.orm import Instrument
from app.services.instruments import InstrumentService
from app.services.kite_provider import make_kite_client
from app.services.market_data import make_market_data_service
from app.services.repos.instruments import InstrumentRepository
from data.timeframe import Timeframe


def _parse_dt(s: str) -> datetime:
    # Accept ISO-ish dates. If time is omitted, midnight local is used.
    # Examples:
    # - 2026-03-01
    # - 2026-03-01T09:15:00
    return datetime.fromisoformat(s)


def _resolve_instrument_id(session, symbol: str, exchange: str) -> uuid.UUID | None:
    stmt = (
        select(Instrument.id)
        .where(Instrument.symbol == symbol)
        .where(Instrument.exchange == exchange)
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="SigmaLab PH2 sanity script: data engine flow")
    p.add_argument("--symbol", default="RELIANCE", help="Trading symbol (default: RELIANCE)")
    p.add_argument("--exchange", default="NSE", help="Exchange (default: NSE)")
    p.add_argument("--timeframe", default="45m", help="Timeframe string (default: 45m)")
    p.add_argument("--start", required=True, type=_parse_dt, help="Start datetime (ISO, e.g. 2026-01-01)")
    p.add_argument("--end", required=True, type=_parse_dt, help="End datetime (ISO, e.g. 2026-02-01)")
    p.add_argument(
        "--sync-instruments",
        action="store_true",
        help="Sync instrument master from Kite before resolving instrument_id",
    )
    args = p.parse_args(argv)

    settings = get_settings()
    db = Database.from_settings(settings)

    with db.session() as session:
        kite = make_kite_client(settings, session=session)
        if args.sync_instruments:
            repo = InstrumentRepository(session)
            n = InstrumentService(kite=kite, repo=repo).sync_instruments()
            print(f"[ok] instruments synced (processed={n})")

        inst_id = _resolve_instrument_id(session, symbol=args.symbol, exchange=args.exchange)
        if inst_id is None:
            print(
                f"[error] instrument not found in DB: {args.exchange}:{args.symbol}. "
                "Run POST /instruments/sync or re-run with --sync-instruments.",
                file=sys.stderr,
            )
            return 2

        tf = Timeframe.parse(args.timeframe)
        svc = make_market_data_service(settings, session=session)
        df = svc.get_candles(
            instrument_id=inst_id,
            timeframe=tf,
            start=args.start,
            end=args.end,
        )

        base_interval = tf.plan().kite_interval.value
        persisted_df = None
        if svc.candle_store is not None:
            persisted_df = svc.candle_store.get_base_candles(
                instrument_id=inst_id,
                base_interval=base_interval,
                start=args.start,
                end=args.end,
            )

        print(f"[ok] instrument_id={inst_id} {args.exchange}:{args.symbol}")
        print(f"[ok] requested timeframe={args.timeframe} (base_interval={base_interval})")
        print(f"[ok] returned candles={len(df)}")
        if not df.empty:
            print(f"[ok] returned range: {df['timestamp'].min()} -> {df['timestamp'].max()}")
        if persisted_df is not None:
            print(f"[ok] persisted base candles in DB for range={len(persisted_df)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
