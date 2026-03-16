# PH5 Implementation Plan (Optimization / Parameter Tuning)

Branch: `feature/ph5-optimization-engine`  
Generated: 2026-03-16 (IST)

## 1) Docs Inspected First (Primary References)

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH6_Implementation_Report.md`
- `docs/PH8_Implementation_Report.md`
- `README.md`

## 2) Relevant Code Inspected First

Backend:

- Backtests runner + persistence: `backend/app/services/backtests.py`, `backend/app/services/repos/backtests.py`
- Backtests APIs + PH8 chart/CSV endpoints: `backend/app/api/routes/backtests.py`
- ORM + schema contracts: `backend/app/models/orm.py`, `backend/app/models/schemas.py`
- Strategy catalog persistence: `backend/app/services/repos/strategy_catalog.py`
- Strategy param schema + validation: `backend/strategies/models.py`, `backend/strategies/params.py`, `backend/strategies/service.py`
- PH4 optimization-readiness layer:
  - `backend/app/backtesting/prepared_input.py`
  - `backend/app/backtesting/indicator_cache.py`
  - `backend/app/backtesting/strategy_evaluator.py`
- Market data access remains via `MarketDataService` (PH2): `backend/data/market_data_service.py` and `backend/app/services/market_data.py`

Frontend:

- App shell + patterns: `frontend/src/app/App.tsx`
- Strategy + backtest runner UX: `frontend/src/pages/StrategiesPage.tsx`, `frontend/src/pages/StrategyDetailPage.tsx`, `frontend/src/pages/BacktestNewPage.tsx`
- Results/runs UX (PH8): `frontend/src/pages/BacktestsListPage.tsx`, `frontend/src/pages/BacktestRunDetailPage.tsx`
- API client/types: `frontend/src/app/api/client.ts`, `frontend/src/app/api/types.ts`

## 3) PH5 Scope Derived From PRD + Current State

PH5 adds an Optimization/Parameter-Tuning system that is a thin orchestration layer over PH4:

- user selects tunable params and defines ranges/values
- system enumerates deterministic parameter combinations (grid search)
- system runs many PH4 backtests and persists each candidate as a real `BacktestRun`
- optimization results are ranked by a chosen objective metric
- user can save a top candidate as a parameter preset
- frontend exposes:
  - optimization list
  - new optimization form
  - optimization detail with ranked candidates table
  - click-through to existing PH8 run detail pages

Non-goals:

- No new replay/simulation engine (reuse PH4).
- No separate optimization result viewer for a candidate (reuse `/backtests/:runId`).
- No heavy distributed job infra (Celery/RQ).
- No Bayesian/genetic optimization (grid search first).

## 4) Key PH5 Design Decisions

### 4.1 Execution model (sync vs async)

Optimization can be long-running. To avoid blocking HTTP requests, PH5 will implement a lightweight background execution using FastAPI `BackgroundTasks`.

- `POST /optimizations` creates an `OptimizationJob` row immediately and schedules a background runner.
- Job status is persisted (`pending/running/success/failed`) with progress counters.
- Frontend polls job status and candidate results.

This keeps PH5 minimal and avoids introducing heavy infra while preserving an async-ready domain model for later improvements.

### 4.2 Reuse PH4 optimization-readiness primitives

Each optimization job will:

1. Prepare market datasets once via `PreparedBacktestInput` for the chosen (watchlist, timeframe, date range).
2. Reuse an in-process `IndicatorCache` across candidates to avoid recomputing compatible indicators across parameter combos.
3. Evaluate strategy signals via `StrategyEvaluator`, then run PH4 `ReplayEngine` and PH4 metrics.

### 4.3 Reproducibility

Persist enough to reproduce:

- strategy slug + code version + `strategy_version_id`
- watchlist id + watchlist snapshot
- timeframe, start/end
- search space definition (ranges/values)
- enumeration limits (safety caps)
- execution assumptions
- objective metric + direction
- candidate params and linked `backtest_run_id`

## 5) Data Model / Migrations (PH5)

Current DB already includes:

- `parameter_presets` (table exists, but not yet exposed in UX)
- `optimization_jobs` (exists but needs more fields)

PH5 will add:

1. Extend `optimization_jobs` to include:
   - `strategy_slug`, `strategy_code_version`
   - `timeframe`, `start_at`, `end_at`
   - `objective_metric`, `sort_direction`
   - `total_combinations`, `completed_combinations`
   - `started_at`, `completed_at`
   - `execution_assumptions_json`
   - keep `search_space_json`, `result_summary_json`, `status`
2. Add `optimization_candidate_results` (new table):
   - `optimization_job_id` (FK)
   - `backtest_run_id` (FK)
   - `params_json`
   - `rank`
   - `objective_value`
   - `metrics_json` (portfolio-level metrics snapshot for table display)
   - indexes: `(optimization_job_id, rank)` and `(optimization_job_id)`

Alembic migrations will be created for these changes.

## 6) Search Space & Enumeration

Search space input will be validated against PH3 parameter specs:

- only `tunable=True` params selectable
- range: `(min, max, step)` for int/float
- values: explicit list for enum/bool or explicit grid values
- if `grid_values` exist in `ParameterSpec`, UI can default to those

Determinism requirements:

- stable ordering by sorted param keys
- stable value ordering for each param
- reproducible candidate list

Safety limits (enforced server-side, surfaced in UI):

- max selected params: 4
- max combinations per job: configurable constant (start with 250; can be adjusted)
- hard reject jobs exceeding the cap with a helpful error including computed combination count

Nice-to-have:

- `POST /optimizations/preview` returns validation + estimated combination count

## 7) Backend Services and APIs (PH5)

New service layer:

- `OptimizationService`:
  - validate + normalize search space
  - enumerate candidates
  - orchestrate PH4 backtest runs per candidate (reusing prepared input + indicator cache)
  - persist job/candidates and ranking metadata
- Repos:
  - `OptimizationRepository`
  - `ParameterPresetRepository` (if needed beyond minimal save/list)

New/updated API routes:

- `POST /optimizations`
- `GET /optimizations`
- `GET /optimizations/{optimization_id}`
- `GET /optimizations/{optimization_id}/candidates`
- `POST /optimizations/{optimization_id}/save-preset`
- optional `POST /optimizations/preview`

Preset support endpoints (minimal UX integration):

- `GET /strategies/{slug}/presets` (list presets for current strategy version)
- `POST /strategies/{slug}/presets` (create preset by name + values)

## 8) Frontend UX Integration (PH6 Shell)

Add a new navigation entry: **Optimization**.

Pages:

1. Optimization list:
   - show recent jobs with status, objective, strategy, watchlist, created_at
   - show best candidate summary if available
2. New optimization form:
   - select watchlist
   - select strategy
   - timeframe + date range
   - choose objective metric + direction
   - select tunable params (1–4) and configure range/values
   - show estimated combinations + guardrail warnings
   - launch job
3. Optimization detail:
   - job status + progress
   - config summary (reproducibility)
   - ranked candidates table with guardrail metrics
   - actions per candidate:
     - open `BacktestRun` (link to `/backtests/:runId`)
     - save as preset (prompt for name)

Backtest run form enhancement (minimal):

- Add optional “Preset” dropdown after selecting a strategy.
- Selecting a preset populates the params form from preset values.

## 9) Testing Plan

Backend unit tests:

- search space validation (reject unknown params, reject non-tunable params)
- combination counting and safety cap enforcement
- deterministic enumeration order
- ranking correctness by objective/direction

Backend integration tests (marked `integration`):

- run a tiny optimization with a mocked MarketDataService/backtest path (or a deterministic synthetic dataset path)
- verify candidates link to persisted `BacktestRun` rows
- verify `optimization_job` and `candidate_results` persistence
- verify save-preset flow persists `ParameterPreset`

Frontend tests (Vitest/RTL):

- optimization list renders empty state
- new optimization form validation + combination estimate display
- optimization detail renders candidates and run click-through link
- save-preset action triggers API call and shows success/error state

## 10) Deliverables

- `docs/PH5_Implementation_Plan.md` (this doc)
- PH5 backend implementation (models, migrations, services, routes)
- PH5 frontend pages integrated into PH6 shell
- tests + test results
- `docs/PH5_Implementation_Report.md`

