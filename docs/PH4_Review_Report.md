# PH4 Review Report

Branch: `feature/ph4-backtesting-engine`  
Generated: 2026-03-15 15:39 IST  
HEAD: `df2957964f797e21a7204d954f616ed6a0a3f2a6`

## Purpose Of PH4

PH4 implements SigmaLab’s **Backtesting Engine**: a deterministic pipeline that consumes PH3 strategy `SignalResult` outputs (signals, indicators, optional stop/take-profit) and converts them into persisted backtest runs, a trade ledger, and metrics. PH4 focuses on simulation and reproducibility, not optimization (PH5) or visualization UX (PH8).

## Branch Information

- Branch name: `feature/ph4-backtesting-engine`
- Current HEAD: `df2957964f797e21a7204d954f616ed6a0a3f2a6`
- Merge base: `main` (PH1/PH2/PH3 already merged into `main`)

## Commit List (PH4)

- `93d65ba` feat: add PH4 backtest metric persistence and run snapshots
- `41c1e4c` feat: add PH4 replay engine, candle cache, and metrics core
- `157ac46` feat: add PH4 backtest run service and persistence repos
- `f3e2b96` feat: add PH4 backtests API routes
- `f75862c` test: add PH4 replay engine, metrics, and candle cache coverage
- `c154128` docs: add PH4 backtesting usage notes and sanity script
- `3465d71` feat: persist holding period and harden backtest run failure status
- `1db7781` test: add PH4 repeatability and cache invariance unit tests
- `13b0608` test: add PH4 persistence integration test with migrations
- `64a1724` test: make integration DB reset use schema drop to avoid FK cycles
- `102206e` fix: disambiguate Strategy-Version ORM relationships
- `ebc89ac` chore: improve PH4 backtest sanity script UX and summary output
- `d939392` chore: add clearer Kite invalid token hint in backtest sanity script
- `df29579` chore: include symbol context when market data fetch fails

## Summary Of Work Completed

- Added a **ReplayEngine** that turns strategy signals into a **trade ledger** with explicit close reasons.
- Added a **BacktestRunService** pipeline that:
  - resolves strategy (code registry) + validates params
  - resolves watchlist instruments from DB
  - fetches candles via **MarketDataService** (PH2), with a per-run **CandleCache**
  - calls strategy `generate_signals(...) -> SignalResult`
  - simulates trades via replay engine
  - computes metrics, equity curve, drawdown curve
  - persists `BacktestRun`, `BacktestTrade`, `BacktestMetric` rows
- Added minimal API routes under `/backtests` to create and query runs.
- Added unit and integration test coverage for replay semantics, caching invariance, and persistence.
- Added a practical sanity script and README notes to run a backtest locally.

## Files / Modules Added Or Updated

Backtesting engine:

- [backend/app/backtesting/models.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/models.py)
- [backend/app/backtesting/replay_engine.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/replay_engine.py)
- [backend/app/backtesting/metrics.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/metrics.py)
- [backend/app/backtesting/candle_cache.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/candle_cache.py)

Service layer + persistence repos:

- [backend/app/services/backtests.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/services/backtests.py)
- [backend/app/services/repos/backtests.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/services/repos/backtests.py)
- [backend/app/services/repos/strategy_catalog.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/services/repos/strategy_catalog.py)

API routes:

- [backend/app/api/routes/backtests.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/api/routes/backtests.py)
- [backend/app/api/router.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/api/router.py)

DB models + migrations:

- [backend/app/models/orm.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/models/orm.py)
- [backend/app/models/schemas.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/models/schemas.py)
- [backend/alembic/versions/8c8d0b2c6b1a_ph4_backtest_metrics_and_run_fields.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/alembic/versions/8c8d0b2c6b1a_ph4_backtest_metrics_and_run_fields.py)
- [backend/alembic/versions/2a7e6dd0fce0_ph4_add_trade_holding_period.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/alembic/versions/2a7e6dd0fce0_ph4_add_trade_holding_period.py)

Tests:

- [tests/test_replay_engine.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_replay_engine.py)
- [tests/test_backtest_metrics.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_backtest_metrics.py)
- [tests/test_candle_cache.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_candle_cache.py)
- [tests/test_backtest_validation_unit.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_backtest_validation_unit.py)
- [tests/test_backtest_persistence_integration.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_backtest_persistence_integration.py)
- [tests/test_postgres_integration.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_postgres_integration.py) (updated reset/migrations behavior)

Scripts + docs:

- [scripts/test_backtest_engine.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/scripts/test_backtest_engine.py)
- [README.md](/home/cbiswas/Documents/Work/tvapp/SigmaLab/README.md)

## Backtest Engine Architecture Summary

PH4 preserves the core rule:

- Strategies are **pure signal generators** (PH3).
- Backtesting/replay is the **only** place that generates trade ledger rows.
- Market data is obtained **exclusively** through `MarketDataService` (PH2). Backtesting never calls broker adapters directly.

High-level flow (synchronous in PH4):

1. Resolve watchlist instruments from DB
2. For each symbol:
   - fetch candles via `MarketDataService` (DB-first, gap backfill via Kite, then aggregation if needed)
   - compute `SignalResult` via strategy `generate_signals`
   - simulate trades via replay engine
   - compute per-symbol metrics + equity/drawdown
3. Combine per-symbol equity curves into a simple equal-weight portfolio curve
4. Persist run + trades + metrics artifacts

## Execution Semantics (Deterministic Assumptions)

The replay engine uses conservative, explicit semantics:

- Entry execution: **next bar open** after the signal bar (`long_entry` at i-1 executes at open of i).
- Exit execution: **next bar open** after `long_exit` signal (same convention).
- Stop-loss / take-profit: evaluated **intrabar** using candle `low/high`.
- If stop-loss and take-profit hit on the same candle: **stop-loss wins** (conservative).
- If a position remains open at end-of-range:
  - intraday strategies close with `intraday_squareoff`
  - otherwise close with `time_exit`
- v1 semantics: **long-only**, **one-position-at-a-time**.

Close reasons persisted in trade ledger:

- `stop_loss`
- `target_hit`
- `signal_exit`
- `time_exit`
- `intraday_squareoff`

## Database Schema And Migrations (PH4)

PH4 extends and adds:

- `backtest_runs`
  - adds `strategy_slug`, `strategy_code_version`
  - adds `watchlist_snapshot_json` (reproducibility)
  - adds `start_at`, `end_at`, `started_at`, `execution_assumptions_json`
- `backtest_trades`
  - adds `instrument_id`, `side`, `quantity`, `close_reason`
  - adds `holding_period_sec`, `holding_period_bars`
  - adds indexes for run/symbol/time querying
- `backtest_metrics` (new)
  - one row for overall metrics (`symbol = NULL`)
  - one row per symbol (`symbol != NULL`)
  - stores `metrics_json`, `equity_curve_json`, `drawdown_curve_json`

## Services / APIs Added

Service:

- `BacktestRunService` in [backend/app/services/backtests.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/services/backtests.py)
  - creates/updates run status
  - persists trades and metrics
  - uses a `StrategyCatalogRepository` to ensure `Strategy` + `StrategyVersion` rows exist for code-registered strategies

API routes:

- `POST /backtests` (runs synchronously)
- `GET /backtests`
- `GET /backtests/{run_id}`
- `GET /backtests/{run_id}/trades`
- `GET /backtests/{run_id}/metrics`

## Tests Added And Results

Unit tests cover:

- signal-to-trade conversion (next-open semantics)
- stop-loss intrabar exit
- forced intraday square-off
- drawdown math
- deterministic repeatability (same inputs -> same outputs)
- cache invariance (cache on/off does not change results)

Integration tests (requires a dedicated DB URL):

- Migrations are applied via Alembic (`alembic upgrade head`)
- A deterministic backtest is executed using a fake MarketDataService
- DB assertions verify `BacktestRun`, `BacktestTrade`, `BacktestMetric` persistence and close reasons

Latest test status (expected):

- `python -m pytest` passes (integration tests skip if `SIGMALAB_TEST_DATABASE_URL` is not set)
- `python -m pytest -m integration` passes when `SIGMALAB_TEST_DATABASE_URL` is set to a PostgreSQL DB the user can reset

## How To Run The PH4 Sanity Script

Prereqs:

- PostgreSQL running and migrations applied (or use `./run_sigmalab_backend.sh`)
- Kite env vars configured (`SIGMALAB_KITE_API_KEY`, `SIGMALAB_KITE_ACCESS_TOKEN`) and instruments synced
- A watchlist created and populated with Instrument UUIDs (not symbols)

List watchlists:

```bash
python scripts/test_backtest_engine.py --list-watchlists
```

Run a backtest:

```bash
python scripts/test_backtest_engine.py \
  --watchlist-id <WATCHLIST_UUID> \
  --strategy-slug intraday_vwap_pullback \
  --timeframe 15m \
  --start 2026-01-10 \
  --end 2026-01-20
```

## Assumptions And Design Decisions

- Synchronous backtest execution (no background jobs in PH4).
- Equal-weight portfolio equity curve is derived from per-symbol equity curves.
- No slippage/fees modeling in PH4.
- Long-only, one-position-at-a-time semantics for v1.
- Per-run CandleCache is in-process and scoped to a single run (not distributed).
- Integration tests reset the DB via `DROP SCHEMA public CASCADE` (requires DB privileges; use a dedicated test database/user).

## Deferred Items For PH5/PH8+

- PH5 optimization: parameter sweeps/grid search, result ranking, dataset reuse.
- PH8 visualization: chart rendering, annotated overlays, replay UI artifacts.
- More realistic execution semantics: slippage, fees, partial fills, position sizing, pyramiding, multi-position support.
- Performance improvements: parallel symbol runs, more aggressive caching, partitioning.
- Async job execution framework for long-running runs (statuses already exist, but queue/worker not implemented).

## Review Checklist

- `POST /backtests` runs a backtest successfully for a populated watchlist.
- Trades are persisted in `backtest_trades` with correct timestamps, pnl, and `close_reason`.
- `backtest_metrics` includes an overall row (`symbol = NULL`) and per-symbol rows.
- Replay semantics match expectations (next-open, stop-loss precedence).
- Running the same deterministic test inputs yields identical results (repeatability test).
- Cache on/off yields identical results (cache invariance test).
- `python -m pytest` passes.
- `python -m pytest -m integration` passes when `SIGMALAB_TEST_DATABASE_URL` is provided.

## Merge Readiness

This branch appears ready for product-owner review and merge once approved, with the main remaining caveats being intentionally deferred features (async runs, fees/slippage, richer portfolio semantics, visualization outputs).  

