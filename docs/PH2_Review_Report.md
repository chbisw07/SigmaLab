# PH2 Review Report — Data Engine

**Date:** 2026-03-15  
**Branch:** `feature/ph2-data-engine`  
**Scope Reference:** `docs/SigmaLab_PRD.md` (PH2 Data Engine + Data Architecture Roadmap), `docs/SigmaLab_Phase_Level_Tasks.xlsx` (Phase 2: Data Engine)

This report summarizes the PH2 Data Engine implementation for review. It does not merge any code to `main`.

---

## 1) Branch Name

`feature/ph2-data-engine`

---

## 2) Commit List (With Short Descriptions)

Commits on this branch relative to `main`:

- `ad44bb5` docs: document candle persistence and PH2 sanity script  
  Adds README guidance for the candle table, migrations, verification, and sanity script usage.
- `581446f` chore: add PH2 data engine sanity script  
  Adds `scripts/test_data_engine.py` demonstrating instrument resolution + fetch + persistence + aggregation.
- `88eb79e` test: validate MarketDataService DB-first behavior  
  Adds tests asserting DB-first reads and skip-fetch when DB coverage is complete.
- `c309b59` feat: DB-first candle reads with gap backfill via Kite  
  Implements DB-first base-candle reads and missing-range backfill through Kite.
- `22945f3` test: cover MarketDataService fetch and aggregation  
  Adds unit tests covering base timeframe vs aggregated timeframe behavior.
- `a0c9438` feat: persist base candles via MarketDataService  
  Adds candle persistence plumbing and JSON-safe API response formatting for timestamps.
- `e42bb41` feat: add base candle storage table and migration  
  Adds the `candles` table + index and ORM model.
- `bd102cd` docs: add Data Architecture Roadmap to PRD for phased data-engine implementation  
  Documents the complete intended data architecture and phase plan.
- `a77cd63` fix: batch instrument master upserts to avoid pg parameter limit  
  Avoids Postgres bind parameter limit during instrument master sync.
- `fe8fea8` fix: sanitize Kite instrument metadata for JSONB  
  Ensures Kite instrument fields (e.g., `date`/`datetime`) serialize cleanly to JSONB.
- `0c3d44b` fix: instrument upsert avoids metadata collision  
  Fixes SQLAlchemy collision with the column name `metadata`.
- `20bfd62` chore: make .env loading robust and stabilize tests  
  Improves `.env` loading consistency and stabilizes tests.
- `49f8101` chore: allow exchange using redirect URL and improve errors  
  Improves Kite token helper UX.
- `1530748` chore: auto-load .env in Kite token helper  
  Loads repo `.env` automatically in the helper.
- `11751f1` chore: add Kite access token helper script  
  Adds `scripts/kite_access_token_helper.py`.
- `3ae97de` chore: ensure runner script installs PH2 deps  
  Runner script improvement to avoid missing deps.
- `20e7f01` docs: update README for PH2 data engine  
  Initial PH2 docs updates.
- `edaedad` test: add optional Postgres integration coverage  
  Adds a Postgres integration test gated by `SIGMALAB_TEST_DATABASE_URL`.
- `003e75c` feat: wire MarketDataService for candle retrieval  
  Adds initial service wiring for candle retrieval.
- `d1fff1b` feat: add instrument sync API endpoint  
  Adds `POST /instruments/sync`.
- `aed092d` feat: add watchlist persistence service and API routes  
  Adds watchlist CRUD + items endpoints and persistence.
- `fa65751` test: cover instrument normalization and sync wiring  
  Adds unit tests for normalization + sync wiring.
- `e5ea8d7` feat: add instrument sync service and idempotent upsert  
  Adds instrument master normalization + idempotent upsert behavior.
- `6364d8a` test: add PH2 data engine unit tests  
  Adds unit tests for PH2 data modules.
- `4afb0df` feat: add PH2 data engine core modules  
  Adds timeframe abstraction, historical fetcher, candle aggregator, market data service interface.

---

## 3) Database Schema And Migrations Added

PH2 adds or refines schema elements supporting instrument sync, watchlists, and base candle persistence.

**Migrations**

- `backend/alembic/versions/3f2a1b0e1c12_ph2_unique_constraints.py`  
  Adds unique constraints for idempotency:
  - `instruments`: `(broker_instrument_token, exchange)` unique
  - `watchlist_items`: `(watchlist_id, instrument_id)` unique

- `backend/alembic/versions/6b2d5f8b1c9a_ph2_add_candles_table.py`  
  Adds base candle persistence table:
  - `candles` with composite primary key `(instrument_id, base_interval, ts)`
  - index `ix_candles_instrument_ts (instrument_id, ts)`

**ORM Models**

- `Instrument`, `Watchlist`, `WatchlistItem` (PH2 constraints + repos/services)
- `Candle` base storage model (`backend/app/models/orm.py`)

Notes:

- Candle storage is **base-interval only** by design (derived timeframes are aggregated dynamically).
- No partitioning/caching schema is introduced in PH2.

---

## 4) Services / Modules Added

**Core data engine modules (`backend/data/`)**

- `timeframe.py`  
  Parses user timeframes and maps them to Kite-supported base intervals + aggregation plans.
- `historical_fetcher.py`  
  Splits long date ranges into Kite-compatible chunks, rate limits, retries, merges, sorts, dedupes.
- `candle_aggregator.py`  
  Aggregates OHLCV into higher timeframes (fixed-factor intraday; calendar resample for week/month).
- `market_data_service.py`  
  Canonical interface for later engines: fetch base candles, persist base candles, aggregate if needed.

**App services (`backend/app/services/`)**

- `kite_provider.py`  
  Config-driven Kite client creation.
- `instruments.py` + `repos/instruments.py`  
  Normalization + idempotent sync/upsert logic (batched).
- `watchlists.py` + `repos/watchlists.py`  
  Watchlist CRUD and item membership persistence.
- `market_data.py` + `repos/candles.py`  
  Wires DB resolver/store into `MarketDataService` and persists base candles into PostgreSQL.

**Scripts**

- `scripts/kite_access_token_helper.py`  
  Helper for generating and exchanging Kite tokens.
- `scripts/test_data_engine.py`  
  PH2 sanity script for instrument resolution, fetching, persistence, aggregation.

---

## 5) API Routes Added

API router wiring: `backend/app/api/router.py`.

- `POST /instruments/sync`  
  Sync and upsert Kite instrument master into PostgreSQL.

- `GET /watchlists`, `POST /watchlists`, `PATCH /watchlists/{watchlist_id}`, `DELETE /watchlists/{watchlist_id}`  
  Watchlist CRUD.

- `POST /watchlists/{watchlist_id}/items/{instrument_id}`, `DELETE /watchlists/{watchlist_id}/items/{instrument_id}`, `GET /watchlists/{watchlist_id}/items`  
  Watchlist membership management.

- `GET /market-data/candles?instrument_id=...&timeframe=...&start=...&end=...`  
  Candle retrieval through `MarketDataService` (DB-first with backfill; dynamic aggregation).

---

## 6) Tests Added And Test Results

**Notable test files added/updated in PH2**

- `tests/test_timeframe.py` (timeframe parsing/plans)
- `tests/test_candle_aggregator.py` (aggregation correctness)
- `tests/test_historical_fetcher.py` (pagination chunking, ordering, dedupe behavior)
- `tests/test_instrument_normalization.py` (normalization + JSONB sanitization behavior)
- `tests/test_instrument_repo_upsert_statement.py` (SQLAlchemy `metadata` collision regression)
- `tests/test_instrument_repo_upsert_batching.py` (instrument master batching regression)
- `tests/test_market_data_service.py` (DB-first behavior, skip-fetch coverage, aggregation wiring)
- `tests/test_postgres_integration.py` (optional; requires `SIGMALAB_TEST_DATABASE_URL`)

**Latest run**

`18 passed, 1 skipped in 1.12s`  
Skip reason: Postgres integration tests are gated unless `SIGMALAB_TEST_DATABASE_URL` is set.

---

## 7) How DB-First Candle Read Works

Implemented in `data.market_data_service.MarketDataService.get_candles()` with an optional `candle_store`:

1. Determine base interval from the requested `Timeframe` plan.
2. If a `candle_store` is present:
   - Read base candles from PostgreSQL for `[start, end]`.
   - Compute missing sub-ranges.
   - Fetch only missing sub-ranges from Kite via `HistoricalFetcher`.
   - Upsert fetched base candles into PostgreSQL.
   - Re-read from PostgreSQL and return the complete base dataset.
3. If no `candle_store` is present:
   - Fetch from Kite directly (no persistence).
4. If the requested timeframe is derived:
   - Aggregate dynamically (no derived-timeframe persistence).

Returned schema is always normalized to:

`timestamp, open, high, low, close, volume`

---

## 8) How Missing-Range Backfill Works

Missing-range detection is implemented in `data.market_data_service._compute_missing_ranges()`:

- If DB has no candles for the range: fetch `[start, end]`.
- If DB partially covers the range:
  - Fetch leading edge `[start, first_ts]` if needed.
  - Fetch trailing edge `[last_ts, end]` if needed.
- For intraday intervals (non-daily) the logic also checks for **same-day gaps**:
  - If consecutive candles within the same date are separated by more than ~1.5× the expected interval step, that window is fetched.

This algorithm is intentionally conservative: it is designed to guarantee coverage and correctness rather than perfect minimality.

Pagination constraints, retry logic, rate limiting, sorting, and deduplication are handled inside `HistoricalFetcher`.

---

## 9) How Timeframe Aggregation Works

**Timeframe planning (`backend/data/timeframe.py`)**

- Parses supported user timeframes:
  - `1m, 3m, 5m, 10m, 15m, 30m, 45m, 1h, 2h, 4h, 1D, 1W, 1M`
- Maps each to a Kite base interval plus:
  - fixed aggregation factor (e.g., `45m` uses base `15m` with factor 3)
  - or calendar rule for weekly/monthly resampling (from daily)

**Aggregation (`backend/data/candle_aggregator.py`)**

- Fixed-factor OHLCV aggregation (intraday) anchored to `Asia/Kolkata` and `09:15` market open.
- Calendar aggregation for `1W`/`1M` uses pandas resampling rules.

OHLCV rules:

- open = first candle open
- high = max(high)
- low = min(low)
- close = last candle close
- volume = sum(volume)

---

## 10) How To Run `scripts/test_data_engine.py`

Prereqs:

- Apply migrations: `.venv/bin/alembic -c backend/alembic.ini upgrade head`
- `.env` configured (at minimum):
  - `SIGMALAB_DATABASE_URL` (PostgreSQL)
  - `SIGMALAB_KITE_API_KEY`
  - `SIGMALAB_KITE_ACCESS_TOKEN`

Example run (sync instruments, then fetch + persist + aggregate):

```bash
source .venv/bin/activate
.venv/bin/python scripts/test_data_engine.py \
  --sync-instruments \
  --symbol RELIANCE \
  --exchange NSE \
  --timeframe 45m \
  --start 2026-01-01 \
  --end 2026-01-15
```

Expected output includes:

- resolved `instrument_id`
- returned candle count and range
- persisted base candle count for the same window

---

## 11) Deferred Items For PH3+

Deferred intentionally (per PRD and phase plan):

- PH3 Strategy Engine: strategy framework, indicators, signal generation
- PH4 Backtesting Engine: replay/simulation engine, trade ledger persistence, candle caching layer
- PH5 Optimization Engine: vectorized research engine, parameter sweeps, optimization result storage/ranking
- Performance enhancements: dataset reuse, caching, partitioning (only if/when volume demands it)

Note: `docs/SigmaLab_Phase_Level_Tasks.xlsx` mentions a “caching layer” under Phase 2 deliverables, but SigmaLab’s PRD explicitly defers candle caching to PH4 to avoid premature optimization in PH2.

