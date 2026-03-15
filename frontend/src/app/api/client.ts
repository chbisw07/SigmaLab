import type {
  BacktestChartResponse,
  BacktestMetricsResponse,
  BacktestRunResponse,
  BacktestTradesResponse,
  BacktestsListResponse,
  UUID
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" }
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  listBacktests(): Promise<BacktestsListResponse> {
    return apiGet("/backtests");
  },
  getBacktestRun(runId: UUID): Promise<BacktestRunResponse> {
    return apiGet(`/backtests/${runId}`);
  },
  listBacktestTrades(runId: UUID): Promise<BacktestTradesResponse> {
    return apiGet(`/backtests/${runId}/trades`);
  },
  listBacktestMetrics(runId: UUID): Promise<BacktestMetricsResponse> {
    return apiGet(`/backtests/${runId}/metrics`);
  },
  getChart(runId: UUID, instrumentId: UUID): Promise<BacktestChartResponse> {
    const q = new URLSearchParams({ instrument_id: instrumentId });
    return apiGet(`/backtests/${runId}/chart?${q.toString()}`);
  },
  tradesCsvUrl(runId: UUID): string {
    return `${API_BASE}/backtests/${runId}/export/trades.csv`;
  },
  metricsCsvUrl(runId: UUID): string {
    return `${API_BASE}/backtests/${runId}/export/metrics.csv`;
  }
};

