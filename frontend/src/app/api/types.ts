export type UUID = string;

export type BacktestRunStatus = "pending" | "running" | "success" | "failed";

export type Instrument = {
  id: UUID;
  created_at: string;
  updated_at: string;
  broker_instrument_token: string;
  exchange: string;
  symbol: string;
  name: string | null;
  segment: string | null;
  instrument_metadata: Record<string, unknown>;
};

export type Watchlist = {
  id: UUID;
  created_at: string;
  updated_at: string;
  name: string;
  description: string | null;
};

export type StrategyCategory = "swing" | "intraday";

export type StrategyStatus = "draft" | "validated" | "archived";

export type StrategyMetadata = {
  name: string;
  slug: string;
  description: string | null;
  category: StrategyCategory;
  timeframe: string;
  long_only: boolean;
  supported_segments: string[];
  version: string;
  status: StrategyStatus;
  notes: string | null;
};

export type ParameterSpec = {
  key: string;
  label: string;
  type: "int" | "float" | "bool" | "enum";
  default: unknown;
  description: string | null;
  tunable: boolean;
  min: number | null;
  max: number | null;
  step: number | null;
  enum_values: string[] | null;
  grid_values: Array<string | number> | null;
};

export type BacktestRun = {
  id: UUID;
  created_at: string;
  updated_at: string;
  strategy_version_id: UUID;
  strategy_slug: string | null;
  strategy_code_version: string | null;
  watchlist_id: UUID;
  watchlist_snapshot_json: Array<{ instrument_id: UUID; symbol: string; exchange?: string }>;
  timeframe: string;
  date_range: string;
  start_at: string | null;
  end_at: string | null;
  params_json: Record<string, unknown>;
  execution_assumptions_json: Record<string, unknown>;
  status: BacktestRunStatus;
  engine_version: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type BacktestTrade = {
  id: UUID;
  created_at: string;
  updated_at: string;
  run_id: UUID;
  instrument_id: UUID | null;
  symbol: string;
  side: string;
  quantity: number;
  entry_ts: string;
  exit_ts: string | null;
  holding_period_sec: number | null;
  holding_period_bars: number | null;
  entry_price: number;
  exit_price: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  entry_reason: string | null;
  exit_reason: string | null;
  close_reason: string | null;
};

export type BacktestMetric = {
  id: UUID;
  created_at: string;
  updated_at: string;
  run_id: UUID;
  symbol: string | null;
  metrics_json: Record<string, unknown>;
  equity_curve_json: Array<{ timestamp: string; equity: number }>;
  drawdown_curve_json: Array<{ timestamp: string; drawdown: number }>;
};

export type BacktestsListResponse = {
  status: "ok";
  runs: BacktestRun[];
};

export type BacktestRunResponse = {
  status: "ok";
  run: BacktestRun;
};

export type BacktestTradesResponse = {
  status: "ok";
  trades: BacktestTrade[];
};

export type BacktestMetricsResponse = {
  status: "ok";
  metrics: BacktestMetric[];
};

export type CandleRow = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
};

export type ChartMarker = {
  trade_id: UUID;
  type: "entry" | "exit";
  timestamp: string;
  price: number;
  label?: string | null;
  close_reason?: string | null;
};

export type ChartPoint = { timestamp: string; value: number | null };

export type BacktestChartResponse = {
  status: "ok";
  run_id: UUID;
  instrument_id: UUID;
  symbol: string | null;
  timeframe: string;
  start: string;
  end: string;
  candles: CandleRow[];
  markers: ChartMarker[];
  overlays: Record<string, ChartPoint[]>;
  signals: Record<string, boolean[]>;
};

export type StrategiesListResponse = {
  status: "ok";
  strategies: StrategyMetadata[];
};

export type StrategyDetailResponse = {
  status: "ok";
  metadata: StrategyMetadata;
  parameters: ParameterSpec[];
};

export type StrategyValidateResponse = {
  status: "ok";
  validated: Record<string, unknown>;
};

export type BacktestCreateRequest = {
  strategy_slug: string;
  watchlist_id: UUID;
  timeframe: string;
  start: string; // ISO
  end: string; // ISO
  params?: Record<string, unknown> | null;
};

export type BacktestCreateResponse = {
  status: "ok";
  run_id: UUID;
  run_status: string;
  metrics: Record<string, unknown>;
};

export type HealthResponse = { status: "ok" };

export type BrokerConnectionStatus = "disconnected" | "connected" | "error";

export type KiteBrokerState = {
  broker_name: string;
  configured: boolean;
  status: BrokerConnectionStatus;
  masked: {
    api_key?: string | null;
    api_secret?: string | null;
    access_token?: string | null;
  };
  metadata: Record<string, unknown>;
  last_verified_at: string | null;
};

export type KiteBrokerSaveRequest = {
  api_key?: string | null;
  api_secret?: string | null;
  access_token?: string | null;
};

export type KiteBrokerTestResponse = {
  status: "ok" | "error";
  tested_at: string;
  message: string;
  profile?: Record<string, unknown>;
};

export type OptimizationJobStatus = "pending" | "running" | "success" | "failed";

export type OptimizationJob = {
  id: UUID;
  created_at: string;
  updated_at: string;
  strategy_version_id: UUID;
  watchlist_id: UUID;
  strategy_slug: string | null;
  strategy_code_version: string | null;
  timeframe: string;
  start_at: string | null;
  end_at: string | null;
  objective_metric: string;
  sort_direction: string;
  total_combinations: number;
  completed_combinations: number;
  started_at: string | null;
  completed_at: string | null;
  search_space_json: Record<string, unknown>;
  execution_assumptions_json: Record<string, unknown>;
  status: OptimizationJobStatus;
  result_summary_json: Record<string, unknown>;
};

export type OptimizationCandidateResult = {
  id: UUID;
  created_at: string;
  updated_at: string;
  optimization_job_id: UUID;
  backtest_run_id: UUID;
  rank: number;
  params_json: Record<string, unknown>;
  objective_value: number;
  metrics_json: Record<string, unknown>;
};

export type OptimizationsListResponse = {
  status: "ok";
  jobs: OptimizationJob[];
};

export type OptimizationGetResponse = {
  status: "ok";
  job: OptimizationJob;
};

export type OptimizationCandidatesResponse = {
  status: "ok";
  candidates: OptimizationCandidateResult[];
};

export type OptimizationPreviewResponse = {
  status: "ok";
  total_combinations: number;
  keys: string[];
};

export type OptimizationCreateRequest = {
  strategy_slug: string;
  watchlist_id: UUID;
  timeframe: string;
  start: string; // ISO
  end: string; // ISO
  objective_metric: string;
  sort_direction: "asc" | "desc";
  selection: Record<string, { mode: "range" | "values"; min?: number; max?: number; step?: number; values?: any[] }>;
  max_combinations?: number;
};

export type OptimizationCreateResponse = {
  status: "ok";
  job_id: UUID;
  total_combinations: number;
};

export type ParameterPreset = {
  id: UUID;
  created_at: string;
  updated_at: string;
  strategy_version_id: UUID;
  name: string;
  values_json: Record<string, unknown>;
};

export type StrategyPresetsResponse = {
  status: "ok";
  presets: ParameterPreset[];
};

export type PresetCreateResponse = {
  status: "ok";
  preset: ParameterPreset;
};
