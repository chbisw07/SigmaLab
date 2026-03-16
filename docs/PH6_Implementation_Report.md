# PH6 Implementation Report (Frontend UX)

Branch: `feature/ph6-frontend-ux`  
Generated: 2026-03-15 (IST)

## 1) Implemented PH6 Scope

PH6 “Frontend UX” was implemented to turn SigmaLab from a results-demo into a coherent research workflow UI built on the already-implemented PH1–PH4 backend plus the PH8 visualization/results foundation.

Target workflow (now supported in the UI):

Dashboard  
→ Watchlists (create + manage universe)  
→ Strategies (browse + inspect params)  
→ Run Backtest (form-driven run creation)  
→ Results (persisted run detail UX from PH8)  
→ Trade detail chart (select trade → annotated chart context)  
→ Settings (truthful broker/config guidance)

Non-goals respected:

- No PH4 replay semantic changes.
- No PH5 optimization orchestration.
- No broker login UI that fabricates connectivity; settings remain truthful and helper-oriented.

## 2) Docs Inspected First (Primary References)

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH8_Implementation_Report.md`
- `README.md`

## 3) Code Inspected First

Backend:

- `backend/app/api/routes/backtests.py`
- `backend/app/api/routes/watchlists.py`
- `backend/app/api/routes/strategies.py`
- `backend/app/api/routes/instruments.py`
- `backend/app/models/schemas.py`

Frontend:

- `frontend/src/app/App.tsx`
- `frontend/src/pages/BacktestsListPage.tsx`
- `frontend/src/pages/BacktestRunDetailPage.tsx` (PH8 run detail UX)
- `frontend/src/components/*` (PH8 charts/tables)

## 4) Backend/API Changes (Minimum Needed For PH6)

PH6 is primarily a UX phase, but watchlist-building requires instrument discovery. Minimal backend additions were made:

- Instruments list/search (read-only):
  - `GET /instruments?q=&exchange=&limit=`
  - Returns a JSON list of `InstrumentSchema` objects.
  - Purpose: power the watchlist “Add instruments” UX without requiring raw UUID copying.
- Watchlist detail endpoint:
  - `GET /watchlists/{watchlist_id}`
  - Purpose: ergonomic watchlist detail page header and data loading.

Key files:

- `backend/app/api/routes/instruments.py`
- `backend/app/services/repos/instruments.py`
- `backend/app/api/routes/watchlists.py`

## 5) Frontend UX Delivered

### App Shell and Navigation

Implemented a stable research-workbench shell with sidebar navigation and consistent page header patterns.

Routes (PH8 compatibility preserved):

- `/dashboard` (default landing)
- `/watchlists`, `/watchlists/:watchlistId`
- `/strategies`, `/strategies/:slug`
- `/backtests`, `/backtests/new`, `/backtests/:runId`
- `/results` (UX alias → `/backtests`), `/results/:runId` (redirect → `/backtests/:runId`)
- `/instruments`
- `/settings`

Shell and primitives:

- `frontend/src/app/App.tsx`
- `frontend/src/app/ui/PageHeader.tsx`
- `frontend/src/app/ui/EmptyState.tsx`
- `frontend/src/app/ui/InlineError.tsx`
- `frontend/src/app/hooks/useAsync.ts`
- `frontend/src/styles.css`

### Dashboard

Dashboard provides:

- API health status
- counts (watchlists, strategies, runs)
- recent runs table
- guided empty states for fresh DB setups

File:

- `frontend/src/pages/DashboardPage.tsx`

### Watchlists UX

Implemented:

- watchlists list + create
- watchlist detail view
- add/remove instruments via instrument search (UUID-safe UX)
- rename + delete watchlist

Files:

- `frontend/src/pages/WatchlistsPage.tsx`
- `frontend/src/pages/WatchlistDetailPage.tsx`

### Strategies UX

Implemented:

- built-in strategies list + simple filtering
- strategy detail view with metadata + parameter schema
- “Run backtest” CTAs that prefill the run form via query params

Files:

- `frontend/src/pages/StrategiesPage.tsx`
- `frontend/src/pages/StrategyDetailPage.tsx`

### Backtest Run UX

Implemented a form-driven backtest runner UI:

- select watchlist
- select strategy
- timeframe defaulted from strategy metadata (editable)
- date range selection
- parameter editing driven by strategy schema
- params are validated via `POST /strategies/{slug}/validate`
- backtest is created via `POST /backtests` and navigates to run detail on success

File:

- `frontend/src/pages/BacktestNewPage.tsx`

### Results UX (PH8 Integration)

PH8 result detail UX is preserved and made discoverable via PH6 navigation and routing.

- Runs list: `/backtests` (improved empty-state guidance)
- Run detail: `/backtests/:runId` (tabs: Summary, Equity, Trades, Symbols, Charts, Config)
- Trade table row selection drives chart context (trade → chart with markers + close reason)

Files:

- `frontend/src/pages/BacktestsListPage.tsx`
- `frontend/src/pages/BacktestRunDetailPage.tsx`

### Instruments and Settings UX

Implemented supportive UX screens:

- Instruments: sync from Kite + search for watchlist building
- Settings: health + truthful Kite configuration guidance (no fabricated “connected” state)

Files:

- `frontend/src/pages/InstrumentsPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`

## 6) Key UX Decisions

- Preserve PH8 route compatibility: `/backtests` and `/backtests/:runId` remain the canonical results routes.
- Add “Results” as a UX alias to improve discoverability without duplicating logic.
- Use instrument UUIDs everywhere in UI interactions (watchlist add/remove) to avoid the common “NSE:SYMBOL vs UUID” mistakes.
- Keep empty states actionable: “Sync instruments” → “Create watchlist” → “Run backtest”.

## 7) Tests Added/Updated

Frontend testing infrastructure added:

- Vitest + React Testing Library + jsdom
- Smoke + empty-state tests to validate shell navigation and key “fresh DB” experiences

Key files:

- `frontend/src/test/setup.ts`
- `frontend/src/test/test_utils.ts`
- `frontend/src/__tests__/app_shell.test.tsx`
- `frontend/src/__tests__/backtests_list_empty.test.tsx`
- `frontend/src/__tests__/watchlists_list_empty.test.tsx`

Backend tests were not expanded in PH6 beyond existing coverage because backend changes were minimal and already aligned with existing patterns.

## 8) Commands Run / Results

Backend:

- `.venv/bin/python -m pytest -q`

Frontend:

- `cd frontend && npm run test`
- `cd frontend && npm run build`

## 9) Known Limitations / Deferrals

- Kite “login / request_token exchange” is not implemented as a UI flow (still done via env + helper scripts). This is intentionally deferred to the broker-integration phase.
- Results comparison UX is not implemented beyond browsing runs (compare-ready structure is a later enhancement).
- Frontend tests currently focus on workflow smoke/empty-state coverage, not deep component interaction testing.

## 10) Manual Validation Checklist

1. Start backend and frontend; confirm sidebar navigation works.
2. Dashboard shows API health and guided next steps on a fresh DB.
3. Instruments:
   - run sync
   - search returns instruments
4. Watchlists:
   - create a watchlist
   - add/remove instruments via search
   - rename and delete work
5. Strategies:
   - list loads
   - detail shows metadata + params
6. Run backtest:
   - validate params works
   - submitting creates a run and navigates to run detail
7. Results:
   - trades table loads
   - selecting a trade opens chart context with markers and close reason

## 11) Recommended Next Phase

After PH6, the next natural step is PH5 Optimization Engine (or PH7 Broker integration, depending on priority):

- PH5: parameter sweep orchestration + result ranking, reusing the existing deterministic backtest pipeline.
- PH7: broker session UX and credential flows (Kite token lifecycle), which would reduce friction for everyday use.

