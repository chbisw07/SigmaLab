# PH4 Optimization-Readiness Enhancement Report

Branch: `feature/ph4-backtesting-optimization-readiness`  
Generated: 2026-03-15 16:05 IST  
HEAD: `3ba328ccd9433e9845f7ae523626980e22ef4fba`

## Purpose

This enhancement pass prepares SigmaLab’s PH4 backtesting stack for a fast PH5 Optimization Engine by reducing repeated work across parameter evaluations:

- reuse prepared candle datasets (per symbol, per timeframe, per date range)
- reuse computed indicators safely via a local cache
- keep strategies pure and deterministic (signals only)
- keep trade generation in the replay/simulation engine (PH4)

PH5 orchestration (grid search, ranking, etc.) is intentionally not implemented here.

## Architecture Added

Target flow:

MarketDataService  
↓  
PreparedBacktestInput  
↓  
IndicatorCache / scoped indicator context  
↓  
Strategy evaluation  
↓  
SignalResult  
↓  
ReplayEngine  
↓  
MetricsEngine

### PreparedBacktestInput

Added in [prepared_input.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/prepared_input.py).

- Normalizes OHLCV frames (`timestamp, open, high, low, close, volume`)
- Stores per-symbol datasets in memory for reuse across repeated evaluations
- Designed to support both single-symbol and watchlist backtests

### IndicatorCache

Added in [indicator_cache.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/indicator_cache.py).

- In-process cache for indicator outputs (`pd.Series` / `pd.DataFrame`)
- Keyed by `(instrument_id, timeframe, indicator_key, params_hash)`
- Provides a `scoped(...)` adapter that strategies can use via the existing `indicators.get(key, compute)` pattern

Design choice:

- The evaluator scopes the cache without full strategy params, so indicator keys must include indicator-specific params (e.g. `("ema","close",20)`), enabling reuse across param sweeps where unrelated params change.

### StrategyEvaluator

Added in [strategy_evaluator.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/backtesting/strategy_evaluator.py).

- Injects a scoped indicator cache into strategy evaluation
- Uses the “compute indicators then generate signals” structure where available
- Falls back to calling `generate_signals(...)` for backward compatibility

## Strategy Refactor

Updated built-in strategies to separate:

- `compute_indicators(...)`
- `generate_signals_from_indicators(...)`

Files:

- [swing_trend_pullback.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/builtin/swing_trend_pullback.py)
- [intraday_vwap_pullback.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/strategies/builtin/intraday_vwap_pullback.py)

## Backtest Runner Integration

Updated the PH4 backtest runner to:

- prepare per-symbol datasets once (`PreparedBacktestInput`)
- evaluate strategies through `StrategyEvaluator` with a shared `IndicatorCache`
- preserve PH4 replay semantics and persistence behavior

File:

- [backtests.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/backend/app/services/backtests.py)

## Tests Added

Added coverage for:

- candle normalization
- indicator cache hit/miss behavior
- evaluator reuse across repeated evaluations
- evaluator output matches direct strategy output for built-ins

File:

- [test_ph4_optimization_readiness.py](/home/cbiswas/Documents/Work/tvapp/SigmaLab/tests/test_ph4_optimization_readiness.py)

## Docs Updated

- README updated with a short section explaining PreparedBacktestInput + IndicatorCache and how this prepares PH5.

## PH5 Readiness Notes

PH5 can build on this by:

- preparing a `PreparedBacktestInput` once per (watchlist, timeframe, date range)
- running many parameter evaluations while reusing:
  - the same candles dataset
  - the same cached indicator series for unchanged indicator parameters
- calling PH4 replay + metrics without changing strategy code

