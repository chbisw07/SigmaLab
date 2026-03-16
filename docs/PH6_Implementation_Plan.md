# PH6 Implementation Plan (Frontend UX)

Branch: `feature/ph6-frontend-ux`  
Generated: 2026-03-15 (IST)

## 1) Docs Inspected First (Primary References)

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH8_Implementation_Report.md`
- Frontend source under `frontend/`
- Backend API routes/schemas under `backend/app/api/routes/*` and `backend/app/models/schemas.py`

## 2) Relevant Code Inspected First

Frontend (current):

- `frontend/src/app/App.tsx` (PH8 shell: Backtests only)
- `frontend/src/pages/BacktestsListPage.tsx`
- `frontend/src/pages/BacktestRunDetailPage.tsx`
- `frontend/src/components/*` (ECharts equity/drawdown + candlestick chart, tables)
- `frontend/src/app/api/client.ts` (only backtests API calls)

Backend (relevant to PH6 UX flow):

- Backtests: `backend/app/api/routes/backtests.py`
- Watchlists: `backend/app/api/routes/watchlists.py`
- Strategies: `backend/app/api/routes/strategies.py`
- Instruments: `backend/app/api/routes/instruments.py` (currently only `/sync`)
- Market data: `backend/app/api/routes/market_data.py`
- Schemas: `backend/app/models/schemas.py`

## 3) PH6 Scope Derived From PRD + Current State

PH6 is the “full user experience” phase:

Dashboard → Watchlists → Strategies → Run Backtest → Results → Trade chart → Settings

PH8 already provides a results UX foundation for run detail and charts. PH6 must productize and unify the workflow.

In scope:

- Proper app shell/navigation and consistent UI primitives
- Dashboard page with:
  - recent runs
  - counts (watchlists/strategies/runs)
  - status widgets and “next step” empty state guidance
- Watchlists UI:
  - list/create/rename/delete watchlists
  - watchlist detail with items
  - add/remove items via instrument search
- Strategies UI:
  - list built-in strategies
  - strategy detail view (metadata + parameter schema)
  - integration with backtest creation flow
- Backtest Run UI:
  - form-driven run creation: watchlist + strategy + timeframe + date range + params
  - validate params (backend already provides `/strategies/{slug}/validate`)
  - submit backtest (`POST /backtests`) and route to run detail on completion
- Results integration:
  - keep existing `/backtests` and `/backtests/:runId` compatibility (PH8)
  - add “Results” route alias for discoverability
  - improve empty states (e.g. “no runs yet” -> “create watchlist / sync instruments / run backtest”)
- Trade detail chart flow:
  - from results trade row -> chart tab centered on that trade (already implemented in PH8)
  - improve routing/state so this is a first-class flow (not “hidden”)
- Settings UX:
  - app status: backend health
  - broker/Kite placeholders + instrument sync action
  - show what is configured truthfully (no fabricated “connected” state)

Out of scope:

- PH5 optimization logic and orchestration (only nav placeholder if needed)
- Any PH4 replay semantic changes
- Full broker login flow UI (PH7/Broker Integration), beyond minimal “helper links”/placeholders

## 4) Current UX Gaps (What PH6 Must Fix)

- Only Backtests exist in navigation; no end-to-end workflow.
- No way to create watchlists in the UI, or add instruments to them.
- No instrument search/list UI; backend lacks an instrument list/search endpoint.
- No strategy list/detail UX beyond raw API.
- No backtest creation UX (only scripts/curl).
- Settings UX is missing; users don’t know where to sync instruments or check configuration.
- Empty states are not guided (fresh DB feels “blank”).

## 5) Minimal Backend/API Additions Required For PH6

PH6 is frontend-focused, but a coherent watchlist builder requires instrument discovery.

Planned backend additions (minimal):

1. Instruments list/search (read-only)
   - `GET /instruments`
   - Query params:
     - `q` (optional: symbol/name search)
     - `exchange` (optional)
     - `limit` (default 50)
   - Response: `{"status":"ok","instruments":[InstrumentSchema...]}` or a plain list (match existing route style; choose one and keep consistent).

2. Watchlist detail endpoint (ergonomics)
   - `GET /watchlists/{watchlist_id}` (returns WatchlistSchema)

Optional (only if needed for Settings dashboard):

3. System status endpoint
   - `GET /system/status` (health + booleans like “kite_configured”)
   - This should not leak secrets, only presence/absence.

## 6) Frontend Pages / Routes To Add Or Update

Keep PH8 routes working:

- `/backtests`
- `/backtests/:runId`

Add PH6 app pages:

- `/dashboard` (new, default landing)
- `/watchlists` (list + create)
- `/watchlists/:watchlistId` (detail + items + instrument search/add)
- `/strategies` (list)
- `/strategies/:slug` (detail + params)
- `/backtests/new` (create run form)
- `/results` (alias to `/backtests` for UX)
- `/settings` (status + Kite placeholders + instrument sync)
- `/instruments` (optional page; can be a simple “sync + search” screen if it helps watchlists)

## 7) UI / Design System Plan (Primitives)

Introduce reusable, consistent UI primitives:

- `AppShell` (sidebar + header)
- `PageHeader` (title, subtitle, actions)
- `Card` / `Panel`
- `EmptyState` with next-step CTA
- `Toast`/inline error banner pattern
- `FormField` (label + hint + error)
- `DataTable` helpers (sort/filter patterns, at least for trades/runs)

Keep styling:

- professional, research-terminal feel
- table-first, chart-aware
- consistent spacing/typography

## 8) Testing Plan

Frontend:

- Add Vitest + React Testing Library
- Tests (minimum):
  - shell renders and nav links exist
  - dashboard empty state renders and suggests actions
  - watchlists list empty state renders
  - backtest creation form validates required fields (watchlist, strategy, date range)
  - results navigation preserves PH8 routes

Backend:

- Only if new endpoints are added:
  - instruments list/search shape
  - watchlist detail endpoint returns expected schema

## 9) Implementation Sequence (Incremental)

1. Refactor app shell + routing, preserve PH8 Backtests routes.
2. Add Dashboard with guided empty states and recent runs.
3. Add Watchlists list/detail UI.
4. Add Instruments discovery UI + minimal backend endpoint(s) if required.
5. Add Strategies list/detail UI.
6. Add Backtest Run creation UI with params validation and run submission.
7. Integrate Results/Backtests polish, trade->chart flow ergonomics.
8. Add Settings UX (status + sync + placeholders).
9. Add tests and docs report.

## 10) Out-of-Scope Items / Deferrals

- Optimization workflows: deferred to PH5 (only nav placeholder)
- Broker “request_token” login flow and secrets management UI: deferred to PH7
- Persisting indicator overlays as artifacts: deferred (PH8 recomputes overlays on demand today)

