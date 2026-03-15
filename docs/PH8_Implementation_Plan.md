# PH8 Implementation Plan (Visualization & Results UX)

Branch: `feature/ph8-visualization-and-results-ux`  
Generated: 2026-03-15 (IST)

## 1) Confirmed PH8 Scope

PH8 implements the Visualization / Results UX layer that turns **persisted PH4 backtest artifacts** into a practical research interface for inspection and trust-building.

In scope (PH8):

1. Backtest runs list and run detail UX.
2. Result detail tabs:
   - Summary
   - Equity
   - Trades
   - Symbols
   - Charts
   - Config
3. Summary charts:
   - equity curve
   - drawdown curve
4. Trades table with explainability fields and export.
5. Symbol-level inspection (per-symbol metrics and drilldowns).
6. Detailed price chart with:
   - candles (or OHLC fallback)
   - entry/exit markers
   - close reason labels/tooltips
   - optional indicator overlays when truthfully available
7. Minimal backend API additions/wiring required by the UI.

Out of scope (PH8):

- Changing PH4 replay semantics or trade generation.
- Implementing optimization orchestration (PH5).
- Adding async job infrastructure beyond what is already in the API model.
- Inventing or fabricating explainability fields not captured by PH4.

## 2) Current Backend Capabilities Available From PH4

Persisted entities (PostgreSQL):

- `backtest_runs` (`BacktestRun`)
  - includes: strategy identity snapshots, watchlist snapshot, timeframe, params, execution assumptions, status/timestamps
- `backtest_trades` (`BacktestTrade`)
  - includes: entry/exit timestamps/prices, PnL, close reason, instrument_id/symbol
- `backtest_metrics` (`BacktestMetric`)
  - `metrics_json`
  - `equity_curve_json` (visualization-ready time series)
  - `drawdown_curve_json` (visualization-ready time series)

Existing API endpoints (already present):

- `GET /backtests` (list runs)
- `GET /backtests/{run_id}` (run header/detail)
- `GET /backtests/{run_id}/trades` (trade ledger)
- `GET /backtests/{run_id}/metrics` (overall and per-symbol metrics, including curves)
- `GET /market-data/candles` (candles via MarketDataService; DB-first with backfill)

## 3) Current Frontend Gaps

- `frontend/` is currently empty (no React app scaffold).
- No results UX pages exist yet.
- No shared UI primitives exist yet (cards/tables/tabs/charts).

PH8 must introduce a minimal but usable frontend scaffold under `frontend/` that can:

- list backtest runs
- open a run detail view
- render charts and tables from the existing backend APIs

## 4) Exact Modules / Files To Be Added Or Changed

### Backend

Files to change/add:

- `backend/app/api/routes/backtests.py`
  - add export endpoints (CSV)
  - add chart-context endpoint(s) if needed for a single ergonomic payload
- `backend/app/main.py`
  - add CORS middleware for local frontend dev
- `backend/app/core/settings.py`
  - add `cors_origins` setting (CSV list) so CORS is configurable
- `backend/app/models/schemas.py`
  - add any response schemas needed for new endpoints (CSV export does not need schemas)

Optional (only if needed after inspection during implementation):

- a small `VisualizationService` module under `backend/app/services/` to keep route handlers thin

### Frontend (new)

Add a Vite + React + TypeScript app under `frontend/`.

Planned structure:

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/app/App.tsx` (router shell)
- `frontend/src/app/api/client.ts` (fetch wrapper + types)
- `frontend/src/pages/BacktestsListPage.tsx`
- `frontend/src/pages/BacktestRunDetailPage.tsx`
- `frontend/src/components/RunTabs.tsx`
- `frontend/src/components/MetricCards.tsx`
- `frontend/src/components/EquityChart.tsx`
- `frontend/src/components/DrawdownChart.tsx`
- `frontend/src/components/TradesTable.tsx`
- `frontend/src/components/SymbolsTable.tsx`
- `frontend/src/components/TradeChart.tsx` (candles + markers)

## 5) API Additions / Changes Required

PH8 will keep existing endpoints and add only what the UI needs for usability.

Planned additions:

1. `GET /backtests/{run_id}/export/trades.csv`
   - CSV export of the trade ledger
2. `GET /backtests/{run_id}/export/metrics.csv`
   - CSV export of overall + per-symbol metrics
3. `GET /backtests/{run_id}/chart`
   - Parameters: `instrument_id`, optional `start`, `end`
   - Returns: candles + markers (from trades) + optional indicator overlays

Notes:

- If indicator overlays cannot be produced truthfully (or add too much backend complexity), the endpoint will return an empty overlays map and the UI will show “Overlays not captured”.

## 6) UI Pages / Components Required

### Backtests List

- A table of recent runs:
  - strategy slug/version
  - timeframe
  - date range
  - status
  - created/completed timestamps
  - link to run detail

### Run Detail (Tabbed)

Tabs:

- Summary
  - metric cards from overall `metrics_json`
- Equity
  - equity curve chart
  - drawdown chart
- Trades
  - trade ledger table (sortable/filterable)
  - CSV export
  - row click drives chart selection
- Symbols
  - per-symbol metrics table
  - click symbol opens chart context
- Charts
  - detailed symbol chart (candles)
  - entry/exit markers + close reason tooltip
  - optional overlays
- Config
  - params snapshot
  - execution assumptions
  - watchlist snapshot
  - engine/version fields and timestamps

## 7) Testing Plan

Backend:

- FastAPI tests for:
  - CSV export endpoints return correct content type + expected columns
  - chart endpoint returns candles and markers shape and is JSON-serializable
  - behavior when candles are unavailable (clear error or empty response)

Frontend:

- If a test harness exists, add minimal component tests for:
  - run detail page render states (loading/error/ok)
  - tab switching
  - trades table renders and “Export CSV” triggers download

If frontend test infra does not exist yet, PH8 will at least add a lightweight smoke path (manual validation checklist in the PH8 implementation report) and keep the UI code modular for later tests.

## 8) Assumptions, Limitations, And Out-Of-Scope Items

Known data truth limitations in the current PH4 model:

- `BacktestTrade.entry_reason` is currently persisted as the generic `"signal_entry"` (replay engine hardcoded).
- `BacktestTrade.exit_reason` is currently not populated; `BacktestTrade.close_reason` is the correct “exit reason” to display.
- Strategy indicator overlays are not persisted as artifacts in PH4 runs today.

PH8 will be truthful:

- The UI will show `close_reason` as the exit reason.
- The UI will show `entry_reason` if present (but will not pretend it is richer than it is).
- Indicator overlays will be either:
  - recomputed on-demand (via strategy evaluation against the same candles + params), or
  - shown as “not captured” if not available without violating architecture.

Deferred (PH5/PH8+):

- monthly/periodic returns heatmap (only if not derivable cleanly from persisted curves)
- compare-runs UX (PH8 will keep URL/state structure compare-ready but not implement full comparisons)
- caching layers or vectorized optimization workflows (PH5)

