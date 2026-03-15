export type UUID = string;

export type BacktestRunStatus = "pending" | "running" | "success" | "failed";

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

