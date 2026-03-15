# SigmaLab

SigmaLab is a research and backtesting platform designed for systematic trading using Zerodha Kite data.

## Purpose

SigmaLab is a **strategy research and backtesting workbench** that complements SigmaTrader.

It is designed as a **dual-engine system**:

- Research Engine: fast watchlist-wide research (vectorized later)
- Replay / Simulation Engine: detailed trade reconstruction (event-driven later)

Important rule: strategy modules generate signals and metadata; simulation engines generate trades.

## Current Phase

PH4 – Backtesting Engine: replay/simulation engine that turns strategy `SignalResult` outputs into trades, persisted runs, and metrics. (Built on PH2 Data Engine + PH3 Strategy Engine.)

PH8 – Visualization / Results UX: a lightweight React UI to inspect persisted backtest runs, metrics, trades, and annotated chart context. It does not change PH4 semantics; it consumes PH4 artifacts.

PH6 – Frontend UX (this branch): productizes the full research workflow (Dashboard → Watchlists → Strategies → Run Backtest → Results → Trade chart → Settings) on top of the PH8 results foundation.

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
Backtest Engine (PH4) generates trades, ledgers, and metrics

Strategies never call broker APIs directly; they consume MarketDataService-compatible candles and only output signals/metadata.

Built-in strategies:

- `swing_trend_pullback`
- `intraday_vwap_pullback`

PH3 API endpoints (dev):

- `GET /strategies`
- `GET /strategies/{slug}`
- `POST /strategies/{slug}/validate`

## PH4 Backtesting Engine

PH4 adds a deterministic replay engine that converts strategy signals into trades and metrics.

Execution semantics (explicit assumptions in code):

- Entries/exits execute on the **next bar open** after the signal bar (conservative, avoids lookahead).
- Stop-loss / take-profit (if provided by a strategy) are checked **intrabar** using candle `low/high`.
- If stop-loss and take-profit are both hit in the same candle, **stop-loss wins** (conservative).
- Intraday strategies are forced closed at end-of-range with `intraday_squareoff`.

Backtest artifacts persisted to PostgreSQL:

- `backtest_runs`
- `backtest_trades`
- `backtest_metrics` (includes equity + drawdown curves as JSON arrays)

PH4 API endpoints (dev):

- `POST /backtests`
- `GET /backtests`
- `GET /backtests/{run_id}`
- `GET /backtests/{run_id}/trades`
- `GET /backtests/{run_id}/metrics`

## PH8 Visualization / Results UX

PH8 adds:

- CSV export endpoints for trades and metrics
- a chart-context endpoint that returns candles + trade markers + optional indicator overlays
- a minimal React UI under `frontend/` for inspecting completed runs

Additional PH8 API endpoints (dev):

- `GET /backtests/{run_id}/export/trades.csv`
- `GET /backtests/{run_id}/export/metrics.csv`
- `GET /backtests/{run_id}/chart?instrument_id=<INSTRUMENT_UUID>`

Run the frontend (local dev):

```bash
cd frontend
npm install
npm run dev
```

Run frontend tests:

```bash
cd frontend
npm run test
```

By default the frontend calls `http://127.0.0.1:8000`. To change:

- copy `frontend/.env.example` to `frontend/.env`
- set `VITE_API_BASE_URL=...`

If the frontend is on a different origin, set backend CORS explicitly (or rely on the default local dev origins):

```bash
SIGMALAB_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Notes:

- Trade markers come from persisted `backtest_trades`.
- Equity/drawdown curves come from persisted `backtest_metrics`.
- Indicator overlays are recomputed deterministically from strategy code + stored params (they are not persisted artifacts yet).

## PH4 Optimization-Readiness Enhancements

To prepare for a fast PH5 Optimization Engine (parameter sweeps) without implementing PH5 yet, PH4 adds a reusable evaluation-preparation layer:

MarketDataService  
↓  
`PreparedBacktestInput` (normalized OHLCV datasets per symbol)  
↓  
`IndicatorCache` / scoped indicator context (reusable indicator outputs)  
↓  
`StrategyEvaluator` (strategy evaluation)  
↓  
`SignalResult`  
↓  
ReplayEngine (PH4) generates trades and metrics

Key rule remains unchanged:

- Strategy modules generate **signals and metadata**.
- Simulation/backtesting modules generate **trades**.

These components are designed so PH5 can evaluate many parameter combinations while reusing:

- prepared candle datasets
- computed indicator series

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

## PH4 Sanity Script

Run a backtest against an existing watchlist (requires PostgreSQL + Kite creds and instruments/watchlist populated):

```bash
source .venv/bin/activate
.venv/bin/python scripts/test_backtest_engine.py \
  --watchlist-id <WATCHLIST_UUID> \
  --strategy-slug swing_trend_pullback \
  --timeframe 1D \
  --start 2026-01-01 \
  --end 2026-03-01
```

## Documentation

See `/docs`
