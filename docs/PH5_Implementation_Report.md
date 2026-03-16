# PH5 Implementation Report (Optimization / Parameter Tuning)

Branch: `feature/ph5-optimization-engine`  
Generated: 2026-03-16 (IST)

## 1) Final Implemented PH5 Scope

PH5 adds a grid-search Optimization system as a thin orchestration layer over the existing PH4 backtesting engine, integrated into the existing PH6 app shell and reusing PH8 run detail UX for candidate inspection.

Implemented:

- Optimization job persistence (`optimization_jobs`)
- Optimization candidate persistence (`optimization_candidate_results`)
- Deterministic search-space validation + grid enumeration (reproducible candidate set)
- Orchestration over PH4 backtests:
  - each candidate produces a real persisted `BacktestRun` (and trades/metrics)
  - candidate rows link to `backtest_run_id` for click-through into `/backtests/:runId`
- Ranking by a chosen objective metric + direction
- Save top candidate as a parameter preset (`parameter_presets`)
- Frontend:
  - Optimization list page
  - New optimization form
  - Optimization detail page with ranked candidates table
  - click-through to existing run detail UX
  - save-preset action
  - backtest-run form supports selecting a saved preset (optional dropdown)

Not implemented (intentionally deferred / out of scope for PH5):

- Bayesian/genetic/random search
- distributed execution / Celery/RQ
- walk-forward validation / train-test splits
- partial-progress candidate table streaming (candidates are persisted after completion in v1)
- compare-run workspace UX (candidate rows are compare-ready via `backtest_run_id`)

## 2) Docs Inspected First

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH6_Implementation_Report.md`
- `docs/PH8_Implementation_Report.md`
- `README.md`

## 3) Code Inspected First

Backend:

- `backend/app/services/backtests.py`
- `backend/app/services/repos/backtests.py`
- `backend/app/api/routes/backtests.py`
- `backend/app/models/orm.py`
- `backend/app/models/schemas.py`
- `backend/strategies/models.py`
- `backend/strategies/params.py`
- `backend/strategies/service.py`
- `backend/app/backtesting/prepared_input.py`
- `backend/app/backtesting/indicator_cache.py`
- `backend/app/backtesting/strategy_evaluator.py`

Frontend:

- `frontend/src/app/App.tsx`
- `frontend/src/pages/BacktestNewPage.tsx`
- `frontend/src/pages/BacktestsListPage.tsx`
- `frontend/src/pages/BacktestRunDetailPage.tsx`

## 4) Database / Migrations Added

Migration added:

- `backend/alembic/versions/9f3a0f3b6a21_ph5_optimization_jobs_and_candidates.py`

Schema changes:

- Extended `optimization_jobs` with:
  - strategy snapshots (`strategy_slug`, `strategy_code_version`)
  - run scope (`timeframe`, `start_at`, `end_at`)
  - ranking (`objective_metric`, `sort_direction`)
  - progress (`total_combinations`, `completed_combinations`, `started_at`, `completed_at`)
  - `execution_assumptions_json`
- Added `optimization_candidate_results`:
  - links to `optimization_jobs` and to the persisted `backtest_runs`
  - stores `rank`, `params_json`, `objective_value`, and a portfolio `metrics_json` snapshot for table display
  - indexed by `(optimization_job_id, rank)`

## 5) Backend APIs Added/Updated

New routes:

- `POST /optimizations/preview`
  - validates selection and returns combination count
- `POST /optimizations`
  - creates an optimization job and starts a lightweight background runner
- `GET /optimizations`
  - list recent jobs
- `GET /optimizations/{job_id}`
  - job detail/status
- `GET /optimizations/{job_id}/candidates`
  - ranked candidate rows (each contains `backtest_run_id`)
- `POST /optimizations/{job_id}/save-preset`
  - create `ParameterPreset` from a selected candidate

Preset support (minimal, for PH5 + backtest form):

- `GET /strategies/{slug}/presets`
- `POST /strategies/{slug}/presets`

Key backend files:

- `backend/app/api/routes/optimizations.py`
- `backend/app/services/optimizations.py`
- `backend/app/optimization/search_space.py`
- `backend/app/services/repos/optimizations.py`
- `backend/app/services/repos/presets.py`
- `backend/app/api/routes/strategies.py`

## 6) Frontend Pages/Components Added

Navigation:

- Added “Optimization” to the PH6 sidebar.

Pages:

- `frontend/src/pages/OptimizationsListPage.tsx`
- `frontend/src/pages/OptimizationNewPage.tsx`
- `frontend/src/pages/OptimizationDetailPage.tsx`

Integration points:

- `frontend/src/pages/BacktestNewPage.tsx`:
  - optional preset dropdown populated from `/strategies/{slug}/presets`
- `frontend/src/pages/StrategyDetailPage.tsx`:
  - added “Optimize” CTA → `/optimizations/new?strategy=...`

## 7) Ranking / Objective Design

PH5 v1 supports ranking by a user-selected metric key from portfolio-level metrics:

- `net_return_pct`
- `profit_factor`
- `max_drawdown_pct`
- `expectancy_pct`
- `win_rate`
- `total_trades`

Sorting direction is user-selectable (`asc` or `desc`).

Robustness emphasis:

- Optimization results table surfaces guardrail metrics alongside the objective so users can avoid fragile “best return, 3 trades” outcomes.

## 8) Execution Model (Async vs Sync)

- `POST /optimizations` schedules execution using FastAPI `BackgroundTasks`.
- Job status and progress counters are persisted.
- Frontend polls job status while running.

This keeps PH5 minimal and avoids introducing Celery/RQ, while keeping the domain model async-ready for later improvements.

## 9) Tests Added and Results

Backend unit tests:

- `tests/test_optimization_search_space.py`
  - validates deterministic key ordering, combination count, range/value validation, tunable enforcement

Backend integration test (marked `integration`, uses `SIGMALAB_TEST_DATABASE_URL`):

- `tests/test_optimization_job_integration.py`
  - runs migrations, creates candles/watchlist, executes a tiny optimization, verifies:
    - job status/progress
    - candidate results + ranking
    - candidate-linked `BacktestRun` persistence
    - save-preset persistence

Frontend tests:

- `frontend/src/__tests__/optimizations_list_empty.test.tsx` (empty state)
- updated `frontend/src/__tests__/app_shell.test.tsx` to include Optimization nav item

Commands run:

- Backend: `.venv/bin/python -m pytest -q`
- Frontend: `cd frontend && npm test`
- Frontend build: `cd frontend && npm run build`

## 10) Manual Validation Checklist

1. Apply migrations: `alembic -c backend/alembic.ini upgrade head`
2. Start backend + frontend.
3. Create watchlist and ensure it has instruments.
4. Go to Optimization:
   - create a small optimization (1–2 params, small ranges)
   - confirm job status moves to `running` and then `success`
   - confirm candidates table appears with “Open run” links
5. Open a candidate run:
   - verify `/backtests/:runId` shows summary/trades/charts as expected
6. Save preset from a candidate:
   - confirm preset saved message
7. Run backtest with preset:
   - Backtest form shows preset dropdown and populates params from the preset

## 11) Deferred Items for PH5+ (Next Iterations)

- Stream candidate rows during job execution (persist partial ranks or allow sorting by objective_value while running)
- Add CSV export for candidates table
- Add compare-candidate selection UX (reuse run detail pages)
- Add composite “robust score” option (documented weighting)
- Add cancel/stop job support and better progress ETA
- Add randomized search modes (optional) once grid-search v1 is stable

