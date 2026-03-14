# PH3 Review Report (Strategy Engine)

**Branch:** `feature/ph3-strategy-engine-enhancements`  
**Generated:** 2026-03-15 01:34:30 +0530 (IST)
**Location:** `docs/PH3_Review_Report.md` (kept under `docs/` alongside `docs/PH2_Review_Report.md`)

---

## 1. Purpose of PH3

PH3 implements SigmaLab’s **Strategy Engine**: a reusable, testable framework for defining strategies as **pure signal generators**. PH3 intentionally does not implement full backtesting, replay simulation, optimization, or chart rendering. Those are deferred to PH4/PH5.

---

## 2. Branch Information

- **Branch name:** `feature/ph3-strategy-engine-enhancements`
- **PH3 type:** PH3 enhancement pass (built on the previously implemented PH3 branch)
- **HEAD commit (at time of report update):** `b1cdd4a53a55d7a412ed1d3efedc929eec5bd94a`

---

## 3. Summary of Work Completed

Implemented a strategy framework and supporting components suitable for later PH4 backtesting and PH5 optimization:

- **Strategy base framework** with a stable contract for signal generation.
- **Strategy metadata contract** (name, slug, category, timeframe, version, status, etc.).
- **Parameter schema contract** for UI and optimization (type, default, min/max/step, tunable, plus optional grid values).
- **Signal output contract** via `SignalResult` (vectorized signals, indicators, optional stop/take-profit, metadata).
- **Shared indicator library** under `backend/indicators/` (deterministic, vectorized, testable).
- **Strategy registry + service layer** for discovery, metadata access, and parameter validation.
- **Built-in strategies**:
  - `swing_trend_pullback`
  - `intraday_vwap_pullback`
- **API routes** for strategy discovery and parameter validation (no execution endpoints).
- **Sanity script** to validate strategy engine behavior on deterministic datasets.

PH3 enhancement items included in this branch:

- Introduced `SignalResult` as the standard strategy output and refactored built-in strategies to return it.
- Added `StrategyContext` and `IndicatorContext` (minimal indicator reuse cache for parameter-grid evaluation).
- Moved indicator implementations to `backend/indicators/` and updated strategies/tests to use the shared library.

---

## 4. Files / Modules Added or Updated (Grouped)

### Strategy Engine (`backend/strategies/`)

- [backend/strategies/base.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/base.py): `BaseStrategy` contract (pure signal generation).
- [backend/strategies/models.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/models.py): `StrategyMetadata`, `ParameterSpec`, `SignalResult`.
- [backend/strategies/params.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/params.py): parameter validation (`validate_params`).
- [backend/strategies/registry.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/registry.py): strategy registration/discovery.
- [backend/strategies/service.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/service.py): service layer for list/detail/validate/instantiate.
- [backend/strategies/context.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/context.py): `StrategyContext`, `IndicatorContext` (indicator reuse).
- [backend/strategies/engine.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/engine.py): glue layer that consumes `MarketDataService` and returns signals (still no trades).
- [backend/strategies/builtin/](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/builtin/__init__.py): built-in strategies.

### Shared Indicators (`backend/indicators/`)

- [backend/indicators/ta.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/indicators/ta.py): SMA/EMA/RSI/ATR/VWAP/rolling-high/rolling-low/ADX.
- [backend/indicators/__init__.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/indicators/__init__.py): public exports.

Note: [backend/strategies/indicators.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/indicators.py) remains as a backward-compatible re-export, but new strategy code should import from `indicators`.

### API (`backend/app/api/routes/`)

- [backend/app/api/routes/strategies.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/api/routes/strategies.py): strategy list/detail/validate endpoints.
- [backend/app/api/router.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/api/router.py): wires `/strategies` routes.

### Scripts (`scripts/`)

- [scripts/test_strategy_engine.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/scripts/test_strategy_engine.py): deterministic sanity script for built-in strategies.

### Tests (`tests/`)

- [tests/test_strategy_registry.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_strategy_registry.py): registry coverage.
- [tests/test_strategy_params.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_strategy_params.py): param validation coverage.
- [tests/test_indicators.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_indicators.py): indicator correctness/sanity.
- [tests/test_builtin_strategies.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_builtin_strategies.py): built-in strategy signal generation.
- [tests/test_strategy_api.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_strategy_api.py): API behavior.
- [tests/test_signal_result.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_signal_result.py): `SignalResult` and indicator cache behavior.

### Docs

- [README.md](/home/cbiswas/Documents/Work/tvapp/SigmaLab/README.md): PH3 overview and the `Strategy -> SignalResult -> PH4 Backtest Engine` pipeline.

---

## 5. Strategy Engine Architecture Summary

Current design principles:

- Strategies are **declarative** and **vectorization-friendly** (operate on full `DataFrame`/`Series`).
- Strategies generate **signals and indicator overlays**, not trades.
- Strategies do not call broker adapters directly and do not access the database.
- Strategies consume **prepared market data** (MarketDataService output shape: `timestamp, open, high, low, close, volume`).
- Trade simulation, close reasons, and ledgers are deferred to PH4.

---

## 6. Strategy Contracts

### Base strategy interface

Implemented in [backend/strategies/base.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/base.py):

- `BaseStrategy.metadata() -> StrategyMetadata`
- `BaseStrategy.parameters() -> list[ParameterSpec]`
- `BaseStrategy.generate_signals(data, params, context=None, indicators=None) -> SignalResult`

### Metadata model

Implemented in [backend/strategies/models.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/models.py) as `StrategyMetadata`:

- name, slug, description
- category (`swing` / `intraday`)
- timeframe (string)
- long_only, supported_segments
- version, status, notes

### Parameter schema model

Implemented in [backend/strategies/models.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/models.py) as `ParameterSpec`:

- key, label, type (`int|float|bool|enum`), default
- min/max/step, tunable
- enum_values (for enums)
- grid_values (optional explicit grid; PH5-ready)

Validation in [backend/strategies/params.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/params.py):

- unknown keys rejected
- types coerced/validated
- min/max enforced
- step enforced for ints (UI/optimization compatibility)

### Signal output model

Implemented in [backend/strategies/models.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/models.py) as `SignalResult`:

- vectorized boolean series: `long_entry`, `long_exit`, `short_entry`, `short_exit`
- indicator overlays: `indicators` (`DataFrame`)
- optional: `stop_loss`, `take_profit`, `metadata`
- `to_frame()` helper to produce a normalized `DataFrame` for consumers/tests

### Registry behavior

Implemented in [backend/strategies/registry.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/registry.py) and [backend/strategies/defaults.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/defaults.py):

- register by unique slug
- list metadata
- retrieve by slug (raises on unknown)
- default registry includes the two built-in strategies

---

## 7. Built-in Strategies Implemented

- `swing_trend_pullback`  
  Daily swing strategy using EMA trend filter and pullback reclaim logic; optional ATR-based stop series; emits long-only signals.

- `intraday_vwap_pullback`  
  Intraday VWAP reclaim entry with VWAP loss / RSI exhaustion exits; emits long-only signals and includes VWAP overlay.

Both are implemented with vectorized pandas operations and use the shared indicator library.

---

## 8. Tests Added

Added/updated tests cover:

- parameter schema validation and coercion
- registry behavior and built-in discovery
- indicator functions sanity/correctness
- built-in strategy signal generation on deterministic datasets
- API listing/detail/validation endpoints
- `SignalResult` structure and indicator reuse cache (`IndicatorContext`)

Sanity script added:

- `scripts/test_strategy_engine.py` (runs built-in strategies against deterministic sample candles)

Test command used:

```bash
.venv/bin/pytest -ra
```

---

## 9. Test Results

Latest results (from this branch):

- **Passed:** 32
- **Skipped:** 1 (`tests/test_postgres_integration.py` requires `SIGMALAB_TEST_DATABASE_URL`)
- **Failed:** 0

---

## 10. Assumptions and Design Decisions

- `SignalResult` is the stable output boundary between PH3 strategies and PH4 simulation/trade generation.
- `IndicatorContext` is intentionally minimal and opt-in to support reuse during parameter grid evaluation without introducing PH4/PH5 caching complexity.
- Indicators live in `backend/indicators/` so they can be shared across strategies and later engines.
- Strategies remain long-only in PH3 built-ins (short signals exist in the contract but default to False).

---

## 11. Deferred Items for PH4

Explicitly deferred to PH4 (Backtesting Engine):

- turning signals into trades (entry/exit execution semantics)
- replay engine / simulation rules (fills, slippage, partial fills, timing rules)
- trade ledger persistence
- close reasons at simulation level (not strategy-level placeholders)
- backtest metrics (returns, drawdown, win rate, etc.)
- per-symbol and watchlist-level backtest orchestration

---

## 12. Review Checklist (Product Owner)

- `GET /strategies` returns both built-in strategies.
- `GET /strategies/{slug}` returns metadata and parameter schema fields (including tunable/min/max/step, and optional grid_values).
- `POST /strategies/{slug}/validate` rejects unknown keys and returns validated values.
- `scripts/test_strategy_engine.py --slug swing_trend_pullback` runs successfully and prints signal counts.
- `scripts/test_strategy_engine.py --slug intraday_vwap_pullback` runs successfully and prints signal counts.
- `.venv/bin/pytest -ra` passes on the branch.

---

## 13. Merge Readiness

This branch appears **ready for product-owner review** and is structurally aligned with the PRD’s architecture rule that strategies generate signals while PH4 generates trades. Merge should proceed only after owner validation.
