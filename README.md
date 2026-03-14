# SigmaLab

SigmaLab is a research and backtesting platform designed for systematic trading using Zerodha Kite data.

## Purpose

SigmaLab is a **strategy research and backtesting workbench** that complements SigmaTrader.

It is designed as a **dual-engine system**:

- Research Engine: fast watchlist-wide research (vectorized later)
- Replay / Simulation Engine: detailed trade reconstruction (event-driven later)

Important rule: strategy modules generate signals and metadata; simulation engines generate trades.

## Current Phase

PH3 – Strategy Engine: strategy framework, indicator utilities, parameter schema/validation, strategy registry, and built-in strategies. (Built on the PH2 Data Engine foundation.)

## Core Features (Target)

- Watchlist-based strategy testing
- Parameter tuning
- Visual backtest charts
- Strategy comparison
- Integration with SigmaTrader

## Backend Setup (PH1)

Prereqs:

- Python 3.12+

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

Environment configuration:

- Copy `.env.example` to `.env` and fill in values as needed.
- Do not commit real credentials.

Run the API (local dev):

```bash
.venv/bin/uvicorn app.main:app --reload
```

One-command runner (starts PostgreSQL, applies migrations, runs API):

```bash
./run_sigmalab_backend.sh
```

Health check:

- `GET /health`

Run tests:

```bash
.venv/bin/pytest
```

PostgreSQL integration tests (optional):

```bash
SIGMALAB_TEST_DATABASE_URL="postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab" .venv/bin/pytest -m integration
```

## Database & Migrations

PostgreSQL is the intended system of record for SigmaLab. Alembic migrations are provided for PH1 and PH2 schema needs.

PH2 introduces base candle persistence in the `candles` table (store base intervals only; higher timeframes are derived by aggregation). The migration that adds the table is:

- `6b2d5f8b1c9a_ph2_add_candles_table.py`

Example Alembic commands:

```bash
.venv/bin/alembic -c backend/alembic.ini revision --autogenerate -m "init"
.venv/bin/alembic -c backend/alembic.ini upgrade head
```

Note: PH1 does not require a running PostgreSQL instance to boot the API and run tests.

### Candle Persistence (PH2)

`MarketDataService` uses a DB-first flow:

- read base candles from PostgreSQL first
- detect missing ranges
- fetch only missing ranges from Kite (with automatic pagination)
- upsert fetched base candles into PostgreSQL
- aggregate dynamically for higher timeframes (when requested)

Verify candle persistence after a `/market-data/candles` call:

```bash
.venv/bin/python - <<'PY'
from app.core.db import Database
from app.core.settings import get_settings
from sqlalchemy import text

db = Database.from_settings(get_settings())
with db.session() as s:
    n = s.execute(text("select count(*) from candles")).scalar_one()
    print("candles rows:", n)
PY
```

## PH2 API Endpoints (Dev)

- `POST /instruments/sync` (requires `SIGMALAB_KITE_API_KEY` + `SIGMALAB_KITE_ACCESS_TOKEN`)
- `GET /watchlists`
- `POST /watchlists`
- `PATCH /watchlists/{watchlist_id}`
- `DELETE /watchlists/{watchlist_id}`
- `POST /watchlists/{watchlist_id}/items/{instrument_id}`
- `DELETE /watchlists/{watchlist_id}/items/{instrument_id}`
- `GET /watchlists/{watchlist_id}/items`
- `GET /market-data/candles?instrument_id=...&timeframe=45m&start=...&end=...` (requires Kite creds)

## PH3 Strategy Engine

PH3 adds a reusable strategy foundation that produces **pure, vectorized signals** and indicator overlays.

Architecture:

Strategy (pure signal generator)  
↓  
`SignalResult` (signals + indicators + optional stop/take-profit)  
↓  
Backtest Engine (PH4) generates trades and ledgers

Strategies never call broker APIs directly; they consume MarketDataService-compatible candles and only output signals/metadata.

Built-in strategies:

- `swing_trend_pullback`
- `intraday_vwap_pullback`

PH3 API endpoints (dev):

- `GET /strategies`
- `GET /strategies/{slug}`
- `POST /strategies/{slug}/validate`

## PH2 Sanity Script

This repo includes a practical sanity script that demonstrates:

- instrument resolution from PostgreSQL (optionally sync from Kite)
- historical fetch with automatic pagination for long ranges
- base candle persistence in PostgreSQL
- higher timeframe aggregation via `MarketDataService`

Example:

```bash
source .venv/bin/activate
.venv/bin/python scripts/test_data_engine.py --sync-instruments --symbol RELIANCE --exchange NSE --timeframe 45m --start 2026-01-01 --end 2026-01-15
```

## PH3 Sanity Script

Strategy engine sanity (no broker calls, deterministic sample candles):

```bash
source .venv/bin/activate
.venv/bin/python scripts/test_strategy_engine.py --slug swing_trend_pullback
.venv/bin/python scripts/test_strategy_engine.py --slug intraday_vwap_pullback
```

## Documentation

See `/docs`
