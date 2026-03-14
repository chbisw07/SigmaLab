# SigmaLab — Product Requirements Document (PRD)

**Version:** v1.0  
**Date:** 2026-03-14  
**Author:** OpenAI / ChatGPT for Chandan Biswas  
**Audience:** Product owner, Codex, implementation contributors  
**Status:** Draft for build kickoff

---

## 1. Executive summary

SigmaLab is a dedicated **strategy research and backtesting workbench** for Indian markets, designed to complement SigmaTrader rather than replace it.

Its purpose is to help the user:

- define and maintain **reusable strategies** for swing trading and intraday trading
- run those strategies on **watchlists**, not just on a single symbol
- tune parameters with confidence
- inspect backtest results through **tables, charts, and annotated trade markers**
- identify whether a strategy is robust enough to support real daily and monthly trading goals
- later export validated signals or strategy configurations into SigmaTrader for monitoring and execution

SigmaLab should feel like a clean, trustworthy research product with a professional UX. It should prioritize:

- clarity over cleverness
- reproducibility over one-off tuning
- watchlist-level research over per-symbol overfitting
- rapid iteration without becoming a giant quant platform

---

## 2. Vision

Build a focused research application that lets the user answer questions like:

- “Which strategies on my watchlist have held up over the last 3–5 years?”
- “What parameter ranges are robust rather than fragile?”
- “Which symbols are suitable for this swing strategy?”
- “Why did this trade enter, exit, or fail?”
- “Can I trust this strategy enough to stop endlessly retuning it?”

SigmaLab is not intended to be a broker execution terminal. SigmaTrader remains the execution and monitoring product. SigmaLab is the **research, validation, and strategy design companion**.

---

## 3. Product goals

### Primary goals

1. Provide a great UX for **strategy research across watchlists**.
2. Support **broker-backed historical data** from Zerodha/Kite.
3. Support **strategy definitions + parameter management**.
4. Provide **real backtest results**, not superficial signal previews.
5. Render **annotated price charts** with:
   - buy/sell markers
   - close markers
   - close reason
   - optional overlay indicators
6. Support **parameter tuning** and robustness analysis.
7. Keep the system simple enough that Codex can implement it incrementally.

### Secondary goals

1. Prepare for future integration with SigmaTrader.
2. Support AI-assisted strategy explanation and comparison.
3. Support result persistence and reproducibility.

### Non-goals for v1

1. Live auto-trading.
2. Multi-broker live execution.
3. Options backtesting.
4. Tick-level backtesting.
5. Portfolio optimization across many simultaneous position-sizing regimes.
6. Full TradingView cloning.
7. Social/community features.

---

## 4. Project name

### Recommended name: **SigmaLab**

Why this name:

- naturally connected to SigmaTrader
- clearly suggests a research environment
- short, clean, professional
- flexible enough to expand later into AI-assisted strategy research

### Alternative names

- SigmaResearch
- SigmaBacktest
- SigmaForge
- SigmaStrategyLab

**Decision:** use **SigmaLab** unless the user strongly prefers another name.

---

## 5. Target users

### Primary user

A serious self-directed trader/researcher who:

- trades Indian equities
- uses Zerodha/Kite
- wants swing and intraday strategies
- prefers watchlist-based research over single-symbol tuning
- wants visual confidence in entries, exits, and reasons
- wants a system that reduces false positives and overfitting

### Secondary user

A future advanced SigmaTrader user who wants a research module before deployment.

---

## 6. Key product principles

1. **Research first.** Every result must be reproducible.
2. **Watchlist-first UX.** Strategies are tested across groups of symbols, not only one chart.
3. **Explainability matters.** Every trade should be inspectable.
4. **Parameter robustness over best-fit illusion.** Show stable ranges, not just best point values.
5. **Professional but lightweight.** Enough power for serious research, not an overbuilt quant platform.
6. **Broker truth for market data.** Use Kite historical data as the primary source of truth where available.
7. **Future SigmaTrader alignment.** Design entities and strategy artifacts so they can later be reused.

---

## 7. Scope overview

SigmaLab v1 will include these major modules:

1. Authentication/session shell (simple local or app-level auth if needed)
2. Broker settings
3. Instruments and watchlists
4. Strategy catalog
5. Strategy editor / configuration
6. Backtest run creation
7. Results summary and comparison
8. Detailed chart view with trade markers and indicators
9. Parameter tuning / optimization workspace
10. Saved runs and reproducibility metadata

---

## 8. High-level product workflow

### Core workflow

1. User configures Zerodha/Kite credentials.
2. User syncs instruments.
3. User creates/selects a watchlist.
4. User creates/selects a strategy.
5. User configures parameters and run settings.
6. User runs backtest.
7. System fetches historical data and executes strategy on selected watchlist.
8. User sees:
   - summary metrics
   - per-symbol metrics
   - trades table
   - equity curve
   - drawdown chart
   - price chart with annotations
9. User optionally tunes parameters.
10. User saves a strategy version or promotes it for future use in SigmaTrader.

---

## 9. UX goals

The UI should feel like a blend of:

- a clean research terminal
- a strategy dashboard
- a chart-driven validation tool

### UX must-haves

1. Low friction from idea to backtest.
2. A user should never wonder:
   - which data was used
   - which parameters were used
   - why a trade closed
3. Charts and tables should support quick trust-building.
4. Settings should be visually aligned with SigmaTrader so the user feels continuity.
5. Complex operations should be hidden behind good defaults.

---

## 10. Information architecture / navigation

### Primary navigation

1. Dashboard
2. Strategies
3. Watchlists
4. Backtests
5. Optimization
6. Instruments
7. Analytics
8. Settings

### Suggested sidebar

- Dashboard
- Strategies
- Watchlists
- Backtests
- Optimization
- Instruments
- Analytics
- System events
- Settings

This mirrors SigmaTrader’s style closely enough to reduce user learning cost.

---

## 11. Detailed module requirements

### 11.1 Dashboard

#### Purpose
Give the user an immediate overview of recent research activity.

#### Dashboard widgets

1. Recent backtest runs
2. Best recent strategies by selected metric
3. Recently modified watchlists
4. Recent optimization jobs
5. Broker/data status
6. Quick actions:
   - New strategy
   - New watchlist
   - Run backtest
   - Open latest result

#### Acceptance criteria

- User can reach the latest useful artifacts in 1–2 clicks.
- Dashboard displays status of Kite connectivity and instrument sync freshness.

---

### 11.2 Settings

#### Purpose
Provide app settings, especially broker/data connectivity.

#### Requirement: match SigmaTrader’s broker settings UX

SigmaLab should include **the same Zerodha/Kite broker settings experience and visual layout pattern** as SigmaTrader, especially for:

- broker section card layout
- connection status badges
- request_token login flow
- secure secret fields
- save/edit/delete row actions
- visible broker health / data availability state

##### Zerodha/Kite settings requirements

Fields and controls:

- Open Zerodha Login button
- request_token input
- Connect Zerodha button
- key/value secrets table for:
  - api_key
  - api_secret
  - access token or session artifacts as needed
- save / edit / delete per row or equivalent improved UX
- status indicators:
  - connected / not connected
  - market data available / unavailable

##### Behavior

- secrets must be stored securely, never logged in plain text
- “Show” must reveal only on explicit user action
- connection test should validate broker session and data availability
- expired sessions should surface a clear reconnect state

##### Future-ready

The structure should allow additional brokers later, but Zerodha/Kite is v1 priority.

#### Additional settings tabs

- General
- Data
- Backtesting
- Chart preferences
- Notifications (optional v1-lite)
- Advanced / developer

---

### 11.3 Instruments

#### Purpose
Maintain broker-derived instrument master and enable symbol selection.

#### Features

1. Pull instrument list from Zerodha/Kite.
2. Store normalized instrument metadata.
3. Support filtering by:
   - exchange
   - segment
   - symbol
   - series
4. Mark active vs inactive instruments.
5. Allow user to add instruments to watchlists.

#### Data fields

- instrument_token
- exchange_token
- tradingsymbol
- name
- exchange
- segment
- instrument_type
- tick_size
- lot_size
- expiry (if relevant, mostly future-ready)
- strike (future-ready)
- last sync time

#### Acceptance criteria

- User can search and add symbols quickly.
- Instrument sync is idempotent and repeatable.

---

### 11.4 Watchlists

#### Purpose
Create reusable symbol groups for backtests.

#### Features

1. Create watchlist
2. Rename watchlist
3. Delete watchlist
4. Add/remove symbols
5. Bulk add via search/filter
6. Copy watchlist
7. Optional tags (e.g. swing candidates, intraday liquid, defense, banking)

#### UX expectations

- fast symbol picker with search
- visible watchlist count
- preview of constituent symbols
- sorting and filtering

#### Backtest relevance

User should be able to select one or more watchlists as a backtest universe.

#### Acceptance criteria

- Watchlists are first-class objects.
- Watchlist membership is versioned enough to reproduce old runs.

---

### 11.5 Strategies

#### Purpose
Maintain a catalog of strategy definitions and configurations.

#### Strategy types in v1

1. Rules-based Python strategies
2. Long-only swing strategies
3. Long-only intraday strategies
4. Optional future support for shorting, MIS, or derivatives

#### Strategy object should include

- name
- slug
- description
- category
  - swing
  - intraday
- timeframe
- long_only flag
- supported segments
- default parameters
- parameter schema
- entry rule description
- exit rule description
- risk rule description
- version
- status
  - draft
  - validated
  - archived

#### Strategy UX

##### Strategy list page

Columns:
- Strategy name
- Category
- Timeframe
- Version
- Last modified
- Default metric summary
- Actions

##### Strategy detail page

Sections:
- overview
- parameters
- logic summary
- supported watchlists / segments
- recent runs
- notes

#### Important design choice

For v1, strategy execution code should live in Python modules, while the UI manages metadata and parameter configuration.

This is much more reliable than inventing a custom DSL too early.

---

### 11.6 Strategy parameters

#### Purpose
Make parameters explicit, editable, and tunable.

#### Parameter types

- int
- float
- bool
- enum
- timeframe selector (optional)

#### Examples

- fast_ema_length
- slow_ema_length
- atr_length
- atr_stop_multiplier
- adx_threshold
- rsi_threshold
- max_holding_days
- session_start / session_end for intraday

#### Required metadata per parameter

- key
- label
- type
- default value
- min/max (if numeric)
- step size
- description
- tunable flag

#### UX expectations

- inline edit form
- reset to default
- save as preset
- duplicate preset

---

### 11.7 Backtests

#### Purpose
Run a strategy against a watchlist and inspect results.

#### Run configuration inputs

- strategy
- strategy version
- parameter preset
- watchlist
- timeframe
- start date
- end date
- capital basis
- per-trade capital or portfolio capital basis
- commission/slippage assumptions
- execution assumptions
- square-off rules for intraday
- max concurrent positions (future-ready if not v1)

#### Run outputs

##### Portfolio-level metrics

- net return
- CAGR
- profit factor
- expectancy
- max drawdown
- Sharpe/Sortino (if feasible)
- total trades
- win rate
- avg win / avg loss
- exposure
- time in market

##### Symbol-level metrics

- return
- number of trades
- win rate
- profit factor
- max drawdown
- expectancy

##### Trade-level outputs

- symbol
- entry date/time
- entry price
- exit date/time
- exit price
- qty / normalized size
- pnl
- pnl %
- hold period
- entry reason
- exit reason
- tags

#### Acceptance criteria

- Every backtest run is reproducible from persisted configuration.
- User can compare multiple runs side by side.

---

### 11.8 Backtest charts

#### Purpose
Visually validate whether the strategy behaves sensibly.

#### Chart types required in v1

##### A. Equity curve
- overall equity curve
- optional benchmark comparison later

##### B. Drawdown chart
- drawdown over time

##### C. Price chart with annotations
For a selected symbol and trade instance, show:

- candlesticks or OHLC
- buy marker
- sell marker
- close marker
- close reason label
- overlay indicators used by strategy
- optional stop/target lines if available

##### D. Monthly/periodic returns chart
- bar chart or heatmap

#### Critical UX requirement

On detailed chart view, the user should be able to inspect:

- which bar triggered entry
- which bar triggered exit
- what the exit reason was
  - stop loss
  - trailing stop
  - time exit
  - indicator reversal
  - target hit
  - square off

#### Suggested interactions

- hover tooltip on markers
- filter to show only entry/exit markers
- toggle indicator overlays
- select a trade from table and center chart on it

#### Recommended charting approach

Frontend should use a chart library suitable for financial charting. Likely options:

- Apache ECharts
- TradingView Lightweight Charts + custom overlays
- Plotly (less ideal for product UX)

**Recommendation:** use **TradingView Lightweight Charts** or **ECharts** for price charts, and a standard React chart library for summary charts.

---

### 11.9 Trade table

#### Purpose
Provide auditability and explainability.

#### Required columns

- Symbol
- Entry time
- Entry price
- Exit time
- Exit price
- PnL
- PnL %
- Hold duration
- Entry reason
- Exit reason
- Strategy version

#### Interactions

- sort
- filter
- export CSV
- click row to open annotated chart

---

### 11.10 Optimization / parameter tuning

#### Purpose
Support robust tuning instead of blind curve fitting.

#### v1 optimization modes

1. Grid search
2. Limited random search (optional)

#### v1 tuning requirements

- user selects tunable params
- user defines ranges
- system runs combinations
- results shown in sortable table
- best combinations shown by selected metric
- user can save a discovered parameter set as a preset

#### Strong requirement

Optimization UI should emphasize **robustness**:

- not only best return
- also consider drawdown, number of trades, and stability

#### Recommended metrics for ranking options

- net return
- profit factor
- max drawdown
- expectancy
- composite score

#### Nice-to-have (v1.1 or v2)

- walk-forward analysis
- train/test split
- rolling validation
- heatmaps for two-parameter grids

---

### 11.11 Analytics

#### Purpose
Help the user judge whether a strategy is trustworthy.

#### v1 analytics

- per-symbol contribution
- distribution of trade returns
- win/loss distribution
- hold time distribution
- monthly return distribution
- drawdown episodes
- best/worst symbols

#### Goal
Help identify false-positive-heavy or regime-dependent strategies.

---

## 12. Functional requirements

### FR-1 Broker connectivity
SigmaLab shall allow the user to connect Zerodha/Kite through a settings flow visually consistent with SigmaTrader.

### FR-2 Instrument sync
SigmaLab shall sync and persist broker instrument master data.

### FR-3 Watchlist management
SigmaLab shall allow creating, editing, deleting, and reusing watchlists.

### FR-4 Strategy catalog
SigmaLab shall maintain a list of strategy definitions and versions.

### FR-5 Parameter management
SigmaLab shall allow storing parameter presets and ranges.

### FR-6 Backtest execution
SigmaLab shall run backtests for a selected strategy/watchlist/timeframe/date range.

### FR-7 Result persistence
SigmaLab shall persist backtest results and run metadata.

### FR-8 Chart visualization
SigmaLab shall render annotated charts with trade markers and indicator overlays.

### FR-9 Trade explainability
SigmaLab shall expose entry reason and exit reason per trade.

### FR-10 Optimization
SigmaLab shall support parameter tuning through configurable search ranges.

### FR-11 Export
SigmaLab shall support exporting trades and summary metrics to CSV.

### FR-12 Compare runs
SigmaLab shall support comparing multiple backtest runs.

---

## 13. Non-functional requirements

### Performance

- Typical backtests across a moderate watchlist should complete within practical user expectations.
- UI should remain responsive while jobs execute.
- Long-running jobs should be asynchronous.

### Reliability

- Every run should have immutable config metadata.
- Errors should be visible and diagnosable.

### Security

- API secrets encrypted at rest.
- No broker secrets in logs.
- Role/auth can be simple in v1 if single-user, but storage must still be safe.

### Maintainability

- Clear separation of UI, API, backtest engine, and data adapters.
- Strategy modules should follow a consistent interface.

### Auditability

- Run inputs and outputs must be inspectable later.

---

## 14. Technical architecture recommendation

### Recommended stack

#### Frontend
- React
- TypeScript
- MUI or the UI stack already used by SigmaTrader frontend
- TanStack Query for server state
- ECharts / Lightweight Charts for charting

#### Backend API
- Python FastAPI

#### Backtesting engine
- **VectorBT recommended for v1 research speed**
- Backtrader can be considered later if execution-model realism becomes more important

#### Data layer
- Zerodha/Kite historical data adapter
- PostgreSQL for v1 as the primary application database. SQLite may be used only for lightweight throwaway local prototyping, but it is not the intended persisted application database.

#### Async jobs
- RQ / Celery / lightweight job runner depending on existing infra

#### Storage domains
- broker settings / secrets
- instrument master
- watchlists
- strategies
- parameter presets
- backtest runs
- optimization jobs
- chart/trade artifacts

SigmaLab will persist broker settings metadata, instruments, watchlists, strategies, parameter presets, backtest runs, trade ledgers, optimization jobs, and visualization metadata. Because SigmaLab will run async backtests and optimization jobs and persist research artifacts, PostgreSQL is the preferred system of record. SQLite is intentionally not the primary production or long-lived application database.

---

## 14A. Recommended SigmaLab Architecture

SigmaLab should adopt a **layered, dual-engine architecture** so that it can be both:

- fast enough for research and parameter sweeps
- accurate enough for detailed trade reconstruction and chart explainability

This is a critical architectural decision for SigmaLab.

### Architecture rationale

A single monolithic backtesting engine would create one of two problems:

1. it would be too slow for watchlist-wide research and optimization, or
2. it would be fast but weak in trade-by-trade explainability, close reasons, and chart replay

To avoid this, SigmaLab should separate:

- **Research Engine** for fast experimentation
- **Replay / Simulation Engine** for detailed validation

This separation ensures SigmaLab remains both:
- efficient for strategy research
- trustworthy for visual inspection and trade auditability

**Important rule:** **Strategy modules generate signals and metadata; simulation engines generate trades.**

---

### High-Level Architecture Diagram

```text
┌──────────────────────────────────────────────────────────────────────┐
│                              SigmaLab                                │
│        Strategy Research & Backtesting Workbench for SigmaTrader     │
└──────────────────────────────────────────────────────────────────────┘

                ┌────────────────────────────────────┐
                │          Frontend (React)          │
                │------------------------------------│
                │ Dashboard                          │
                │ Strategies                         │
                │ Watchlists                         │
                │ Backtests                          │
                │ Optimization                       │
                │ Visualization / Reporting          │
                │ Settings                           │
                └────────────────────────────────────┘
                                  │
                                  │ REST / WebSocket / Async Job Status
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Backend API (FastAPI)                        │
│----------------------------------------------------------------------│
│ API Routers                                                          │
│ - settings                                                           │
│ - instruments                                                        │
│ - watchlists                                                         │
│ - strategies                                                         │
│ - backtests                                                          │
│ - optimization                                                       │
│ - visualization                                                      │
│ - system / health                                                    │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Application / Service Layer                    │
│----------------------------------------------------------------------│
│ BrokerConnectionService                                              │
│ InstrumentService                                                    │
│ WatchlistService                                                     │
│ StrategyRegistryService                                              │
│ BacktestRunService                                                   │
│ OptimizationService                                                  │
│ VisualizationService                                                 │
│ ReportService                                                        │
└──────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          │                    │                    │
          ▼                    ▼                    ▼

┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐
│   Data Layer         │  │   Strategy Layer     │  │   Job Layer        │
│----------------------│  │----------------------│  │-------------------│
│ Broker adapters      │  │ Strategy base class  │  │ Async job runner   │
│ Kite historical data │  │ Strategy metadata    │  │ Backtest jobs      │
│ Instrument sync      │  │ Parameter schemas    │  │ Optimization jobs  │
│ OHLCV storage        │  │ Indicator library    │  │ Progress updates   │
│ Watchlist storage    │  │ Signal generation    │  │ Result persistence │
└──────────────────────┘  └──────────────────────┘  └───────────────────┘
          │                    │
          │                    │
          └──────────────┬─────┘
                         ▼
        ┌──────────────────────────────────────────────┐
        │         Research Engine (Vectorized)         │
        │----------------------------------------------│
        │ Purpose: fast watchlist-wide research        │
        │                                              │
        │ Inputs:                                      │
        │ - OHLCV data                                 │
        │ - strategy definition                        │
        │ - parameter ranges                           │
        │                                              │
        │ Outputs:                                     │
        │ - summary metrics                            │
        │ - ranked candidate runs                      │
        │ - parameter sweep results                    │
        │ - symbol-level performance                   │
        └──────────────────────────────────────────────┘
                         │
                         │ selected candidate run
                         ▼
        ┌──────────────────────────────────────────────┐
        │     Replay / Simulation Engine (Event)       │
        │----------------------------------------------│
        │ Purpose: detailed trade reconstruction       │
        │                                              │
        │ Inputs:                                      │
        │ - chosen strategy                            │
        │ - chosen params                              │
        │ - chosen watchlist / symbol                  │
        │ - historical candles                         │
        │                                              │
        │ Outputs:                                     │
        │ - trade ledger                               │
        │ - entry/exit timestamps                      │
        │ - close reasons                              │
        │ - marker annotations                         │
        │ - detailed replay-ready artifacts            │
        └──────────────────────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────────────┐
        │       Visualization / Reporting Layer        │
        │----------------------------------------------│
        │ Equity curve                                 │
        │ Drawdown chart                               │
        │ Trade table                                  │
        │ Annotated price chart                        │
        │ Indicator overlays                           │
        │ Optimization result tables                   │
        │ Export CSV / reports                         │
        └──────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          Persistence Layer                           │
│----------------------------------------------------------------------│
│ PostgreSQL                                                           │
│ - broker connections                                                 │
│ - instruments                                                        │
│ - watchlists                                                         │
│ - strategies                                                         │
│ - parameter presets                                                  │
│ - backtest runs                                                      │
│ - trade ledger                                                       │
│ - optimization jobs                                                  │
│ - visualization artifacts / metadata                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Architecture Roadmap

### Core Data Principles

- Store **base timeframe candles only**
- Higher timeframes are produced by **aggregation**
- Historical data fetching must support **automatic pagination**
- Strategies and backtesting engines must NOT call broker APIs directly
- All data access must go through **MarketDataService**

**Strategy modules and backtesting engines must obtain market data exclusively via MarketDataService.**

### Candle Storage Strategy

SigmaLab stores only **base timeframe** candles (the smallest persisted unit). Higher timeframes (e.g., 5m, 15m, 45m, 1h) are generated dynamically via aggregation.

Example:

- 1 minute candles stored
- 5m / 15m / 45m / 1h generated dynamically

Recommended schema example:

```sql
CREATE TABLE candle_1m (
    instrument_id BIGINT NOT NULL,
    ts TIMESTAMP NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT,
    PRIMARY KEY (instrument_id, ts)
);
```

Critical index example:

```sql
CREATE INDEX idx_candle_symbol_time
ON candle_1m(instrument_id, ts);
```

Storing only base timeframe candles avoids duplicating the same market history across many derived timeframes.

### Data Pipeline

Intended data pipeline:

Kite API  
↓  
HistoricalFetcher  
↓  
Base Candle Storage (PostgreSQL)  
↓  
MarketDataService  
↓  
Timeframe Aggregation  
↓  
Strategy Engine / Backtest Engine

HistoricalFetcher handles pagination automatically.

### Historical Fetch Strategy

Kite historical API has maximum range limits per request depending on interval. SigmaLab must:

- split large date ranges
- call broker API multiple times
- merge results
- deduplicate candles
- sort timestamps

This logic must exist inside `historical_fetcher`.

### Timeframe Aggregation

Supported user timeframes:

- 1m
- 3m
- 5m
- 10m
- 15m
- 30m
- 45m
- 1h
- 2h
- 4h
- 1D
- 1W
- 1M

Aggregation examples:

- 45m = 3 × 15m candles
- 2h = 2 × 60m candles

Aggregation rules:

- open = first candle open
- high = max(high)
- low = min(low)
- close = last candle close
- volume = sum(volume)

Aggregation is implemented in `candle_aggregator`.

### Phase Implementation Plan

PH2 – Data Engine

- instrument master ingestion
- watchlist persistence
- historical_fetcher
- timeframe abstraction
- candle_aggregator
- MarketDataService
- PostgreSQL schema and indexes

PH3 – Strategy Engine

- strategy framework
- indicator library
- signal generation

PH4 – Backtesting Engine

- replay simulation engine
- trade ledger persistence
- performance metrics
- candle caching layer

Example cache:

`CandleCache[(instrument_id, timeframe)] → dataframe`

PH5 – Optimization Engine

- vectorized research engine
- parameter sweep engine
- optimization result storage
- strategy ranking

### Future Performance Enhancements

Intentionally deferred to PH4/PH5:

- candle caching
- dataset reuse during optimization
- vectorized research engine
- PostgreSQL partitioning if data volume grows

## 15. Recommended domain model

### Entities

#### BrokerConnection
- id
- broker_name
- status
- config metadata
- encrypted secrets
- last_connected_at
- last_verified_at

#### Instrument
- id
- broker_instrument_token
- exchange
- symbol
- name
- segment
- metadata

#### Watchlist
- id
- name
- description
- created_at
- updated_at

#### WatchlistItem
- id
- watchlist_id
- instrument_id
- added_at

#### Strategy
- id
- name
- slug
- category
- description
- code_ref
- current_version_id

#### StrategyVersion
- id
- strategy_id
- version
- changelog
- parameter_schema
- default_params
- created_at

#### ParameterPreset
- id
- strategy_version_id
- name
- values_json

#### BacktestRun
- id
- strategy_version_id
- watchlist_id
- timeframe
- date_range
- params_json
- status
- engine_version
- created_at
- completed_at

#### BacktestMetric
- run_id
- metric_key
- metric_value

#### BacktestTrade
- run_id
- symbol
- entry_ts
- exit_ts
- entry_price
- exit_price
- pnl
- pnl_pct
- entry_reason
- exit_reason

#### OptimizationJob
- id
- strategy_version_id
- watchlist_id
- search_space_json
- status
- result_summary_json

---

## 16. Strategy engine interface recommendation

To keep Codex implementation disciplined, define a stable strategy contract.

### Suggested interface

Each strategy module should expose functions like:

- `get_metadata()`
- `get_parameter_schema()`
- `run_backtest(data, params, context)`
- `explain_trade(trade_row)`

### Notes

- Avoid custom DSL in v1.
- Keep Python strategy modules pure and testable.
- Strategy code should return both signals and explanation metadata where possible.

---

## 17. Data requirements

### Historical data

Minimum required for v1:

- OHLCV candles from Kite
- multiple timeframes derived or fetched as needed
- symbol-level historical coverage for selected range

### Data issues to handle

- missing candles
- bad broker sessions
- partial fetches
- timezone normalization
- instrument identity changes if any

### Data policy

Runs should store enough metadata to know:

- data source
- fetch timestamp
- timeframe
- coverage completeness if possible

---

## 18. Detailed UX flows

### 18.1 First-time setup flow

1. User opens SigmaLab.
2. User lands on Dashboard or Settings prompt.
3. User goes to Settings → Broker settings.
4. User connects Zerodha using a SigmaTrader-like flow.
5. User syncs instruments.
6. User creates first watchlist.
7. User selects or creates first strategy.
8. User runs first backtest.

Success criteria: first useful backtest in under 15 minutes.

---

### 18.2 Create watchlist flow

1. Open Watchlists.
2. Click New watchlist.
3. Provide name and optional description.
4. Search instruments.
5. Add symbols.
6. Save.

---

### 18.3 Create strategy preset flow

1. Open Strategies.
2. Select strategy.
3. Review default parameters.
4. Save as a preset.
5. Use preset in backtest.

---

### 18.4 Run backtest flow

1. Open Backtests.
2. Click New backtest.
3. Select strategy.
4. Select preset.
5. Select watchlist.
6. Select date range and timeframe.
7. Configure execution assumptions.
8. Submit.
9. View job progress.
10. Open result summary.

---

### 18.5 Inspect trade flow

1. Open a completed run.
2. Go to Trades tab.
3. Click a trade row.
4. Detailed chart opens for that symbol/time window.
5. Entry/exit markers and reason labels displayed.
6. Optional indicator overlay toggles shown.

---

### 18.6 Optimization flow

1. Open Optimization.
2. Pick strategy + watchlist + date range.
3. Select 1–4 tunable parameters.
4. Define ranges and steps.
5. Choose ranking metric.
6. Run optimization.
7. Inspect result table.
8. Save best candidate as parameter preset.

---

## 19. Suggested pages in detail

### Page: Strategies list

- search bar
- category filter
- timeframe filter
- create strategy button
- table/cards of strategies

### Page: Strategy detail

Tabs:
- Overview
- Parameters
- Presets
- Recent runs
- Notes

### Page: Watchlists

- watchlist cards/table
- symbol counts
- duplicate/delete actions

### Page: Backtests

- new backtest button
- recent runs table
- status filter

### Page: Backtest result detail

Tabs:
- Summary
- Equity
- Trades
- Symbols
- Charts
- Config

### Page: Optimization

- search space form
- results table
- candidate presets

### Page: Settings

Tabs:
- Broker settings
- Data
- Chart preferences
- Advanced

---

## 20. Metrics and scoring philosophy

The product should not over-reward raw return.

### Recommended default result cards

- Net return
- Profit factor
- Max drawdown
- Win rate
- Expectancy
- Trade count
- Avg holding period

### Composite score suggestion

Later, define a weighted score such as:

`score = f(return, drawdown, profit_factor, trade_count, expectancy)`

The UI should clearly state that this score is heuristic, not truth.

---

## 21. Strategy categories to support first

### Recommended initial built-in strategies

#### 1. Swing trend-pullback strategy
- long only
- suitable for watchlists
- 45m / daily

#### 2. Intraday VWAP trend-pullback strategy
- long only initially
- 15m
- session square-off

These two directly support the user’s stated goals.

---

## 22. AI integration opportunities (future-facing, not required for v1 core)

SigmaLab may later support an AI assistant that can:

- explain why a backtest performed poorly
- compare two runs
- summarize best parameter zones
- suggest which symbols are unsuitable for a strategy
- generate human-readable trade insights

Important: AI should **not invent data**. It should work off persisted backtest outputs.

---

## 23. Risks and mitigations

### Risk 1: Overfitting through optimization
Mitigation:
- emphasize robustness metrics
- support out-of-sample later
- display trade count and drawdown prominently

### Risk 2: Data fetch instability from broker sessions
Mitigation:
- strong reconnect UX
- fetch retry logic
- visible sync status

### Risk 3: Building too much too early
Mitigation:
- strict v1 scope
- only Zerodha/Kite first
- only rules-based strategies first

### Risk 4: Charting complexity
Mitigation:
- keep summary charts simple
- build one strong detailed trade chart first

### Risk 5: Confusion with SigmaTrader responsibilities
Mitigation:
- position SigmaLab clearly as research/backtest product
- later export approved strategies/signals into SigmaTrader

---

## 24. Correct Development Order

SigmaLab should be implemented in the following order:

### PH1 — Foundation

Core scaffolding.

Includes:

* project structure
* backend FastAPI setup
* frontend React scaffold
* database models
* configuration framework
* logging
* environment management

---

### PH2 — Data Engine

Market data foundation.

Includes:

* Zerodha/Kite integration
* instrument master sync
* OHLCV historical data fetch
* symbol metadata storage
* data adapter layer
* watchlist data access

---

### PH3 — Strategy Engine

Strategy definition framework.

Includes:

* Python strategy interface
* parameter schema definition
* signal generation model
* indicator computation utilities
* strategy registry
* strategy metadata

---

### PH4 — Backtesting Engine

Core simulation engine.

Includes:

* vectorized research engine
* trade generation
* equity curve computation
* metrics generation
* trade ledger creation
* run metadata persistence

---

### PH8 — Visualization and Reporting

Validation layer.

Includes:

* equity curve chart
* drawdown chart
* trade table
* symbol performance table
* annotated price charts
* indicator overlays
* trade markers

---

### PH6 — Frontend UX

Full user experience.

Includes:

* dashboard
* strategies UI
* watchlists UI
* backtest run UI
* results pages
* trade detail chart
* settings UX

---

### PH5 — Optimization Engine

Parameter research.

Includes:

* grid search
* parameter range definition
* optimization job execution
* sortable results
* preset saving

---

### PH7 — Broker Integration

Broker connectivity for future execution.

Includes:

* Zerodha/Kite credential management
* connection testing
* broker metadata
* future SigmaTrader interoperability

---

### PH9 — Deployment and Ops

Production readiness.

Includes:

* Docker
* environment configuration
* logging
* monitoring
* CI/CD
* backup strategy

---

## 25. Acceptance criteria for v1 release

SigmaLab v1 is acceptable when:

1. User can connect Zerodha/Kite through a SigmaTrader-like settings UX.
2. User can sync instruments and build watchlists.
3. User can select a built-in strategy and parameter preset.
4. User can run a backtest on a watchlist.
5. User can inspect summary metrics and trade-level results.
6. User can open an annotated chart showing entries, exits, and close reasons.
7. User can run basic parameter tuning on at least one strategy.
8. Results are saved and reproducible.

---

## 26. Codex implementation notes

### Implementation philosophy for Codex

1. Prefer clear, modular code over smart abstractions.
2. Keep the UI close to SigmaTrader where it helps continuity.
3. Do not prematurely build a DSL.
4. Keep strategy execution behind a stable Python interface.
5. Build vertical slices that become usable early.

### Coding priorities

1. Settings + Kite integration
2. Instruments + watchlists
3. Single built-in swing strategy
4. Backtest run pipeline
5. Result summary
6. Annotated chart
7. Optimization

### Suggested repository structure

```text
sigmalab/
  frontend/
  backend/
    app/
      api/
      core/
      models/
      services/
      brokers/
      data/
      strategies/
      backtesting/
      optimization/
      charts/
      jobs/
  docs/
```

### Suggested strategy package structure

```text
backend/app/strategies/
  base.py
  swing_trend_pullback.py
  intraday_vwap_pullback.py
```

### Suggested backtesting package structure

```text
backend/app/backtesting/
  engine.py
  metrics.py
  run_service.py
  trade_explainer.py
```

---

## 27. Open decisions

These can be finalized during implementation:

1. ECharts vs Lightweight Charts for detailed symbol chart
2. Exact backtest engine abstraction around VectorBT
3. Whether to support benchmark overlays in v1 or v1.1
4. How much auth is needed for a single-user first deployment
5. Whether SQLite convenience mode should be supported later for local-only experimentation as a low-priority future convenience, not a v1 architectural decision

---

## 28. Final recommendation

Build SigmaLab as a **focused strategy research companion** for SigmaTrader.

Do not try to match all of TradingView. Do not try to over-automate research. Build a system that gives the user:

- confidence
- clarity
- watchlist-level validation
- parameter discipline
- visual trust in signals and exits

If done well, SigmaLab becomes the place where strategies earn trust before they are used in SigmaTrader.

---

## 29. Immediate next step recommendation

Start implementation with this exact sequence:

1. Create project scaffold and docs
2. Implement Settings page with SigmaTrader-like Zerodha/Kite flow
3. Implement instrument sync and watchlist CRUD
4. Implement one built-in swing strategy
5. Implement one end-to-end backtest result page
6. Add annotated chart view
7. Add tuning

This yields a usable product quickly and avoids getting stuck in architecture-only work.
