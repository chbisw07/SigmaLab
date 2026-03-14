# SigmaLab

SigmaLab is a research and backtesting platform designed for systematic trading using Zerodha Kite data.

## Purpose

SigmaLab is a **strategy research and backtesting workbench** that complements SigmaTrader.

It is designed as a **dual-engine system**:

- Research Engine: fast watchlist-wide research (vectorized later)
- Replay / Simulation Engine: detailed trade reconstruction (event-driven later)

Important rule: strategy modules generate signals and metadata; simulation engines generate trades.

## Current Phase

PH2 – Data Engine: instrument master ingestion, historical OHLCV retrieval with pagination, timeframe abstraction/aggregation, watchlist persistence, and a MarketDataService interface.

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

Example Alembic commands:

```bash
.venv/bin/alembic -c backend/alembic.ini revision --autogenerate -m "init"
.venv/bin/alembic -c backend/alembic.ini upgrade head
```

Note: PH1 does not require a running PostgreSQL instance to boot the API and run tests.

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

## Documentation

See `/docs`
