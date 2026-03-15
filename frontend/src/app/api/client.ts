import type {
  BacktestChartResponse,
  BacktestCreateRequest,
  BacktestCreateResponse,
  BacktestMetricsResponse,
  BacktestRunResponse,
  BacktestTradesResponse,
  BacktestsListResponse,
  HealthResponse,
  Instrument,
  Watchlist,
  StrategyDetailResponse,
  StrategyValidateResponse,
  StrategiesListResponse,
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

async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {})
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  // Some endpoints may return non-JSON on error, but success should be JSON.
  return (await resp.json()) as T;
}

async function apiPatchJson<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {})
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  return (await resp.json()) as T;
}

async function apiDelete(path: string): Promise<void> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
}

export const api = {
  health(): Promise<HealthResponse> {
    return apiGet("/health");
  },

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
  createBacktest(payload: BacktestCreateRequest): Promise<BacktestCreateResponse> {
    return apiPostJson("/backtests", payload);
  },
  tradesCsvUrl(runId: UUID): string {
    return `${API_BASE}/backtests/${runId}/export/trades.csv`;
  },
  metricsCsvUrl(runId: UUID): string {
    return `${API_BASE}/backtests/${runId}/export/metrics.csv`;
  },

  listStrategies(): Promise<StrategiesListResponse> {
    return apiGet("/strategies");
  },
  getStrategy(slug: string): Promise<StrategyDetailResponse> {
    return apiGet(`/strategies/${encodeURIComponent(slug)}`);
  },
  validateStrategy(slug: string, params: Record<string, unknown>): Promise<StrategyValidateResponse> {
    return apiPostJson(`/strategies/${encodeURIComponent(slug)}/validate`, params);
  },

  listWatchlists(): Promise<Watchlist[]> {
    return apiGet("/watchlists");
  },
  getWatchlist(watchlistId: UUID): Promise<Watchlist> {
    return apiGet(`/watchlists/${watchlistId}`);
  },
  createWatchlist(payload: { name: string; description?: string | null }): Promise<Watchlist> {
    return apiPostJson("/watchlists", payload);
  },
  renameWatchlist(watchlistId: UUID, payload: { name: string }): Promise<Watchlist> {
    return apiPatchJson(`/watchlists/${watchlistId}`, payload);
  },
  deleteWatchlist(watchlistId: UUID): Promise<void> {
    return apiDelete(`/watchlists/${watchlistId}`);
  },
  listWatchlistItems(watchlistId: UUID): Promise<Instrument[]> {
    return apiGet(`/watchlists/${watchlistId}/items`);
  },
  addWatchlistItem(watchlistId: UUID, instrumentId: UUID): Promise<void> {
    return apiPostJson(`/watchlists/${watchlistId}/items/${instrumentId}`, {});
  },
  removeWatchlistItem(watchlistId: UUID, instrumentId: UUID): Promise<void> {
    return apiDelete(`/watchlists/${watchlistId}/items/${instrumentId}`);
  },

  listInstruments(q?: string, exchange?: string, limit = 50): Promise<Instrument[]> {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (exchange) p.set("exchange", exchange);
    p.set("limit", String(limit));
    const s = p.toString();
    return apiGet(`/instruments${s ? `?${s}` : ""}`);
  },
  syncInstruments(): Promise<{ status: "ok"; upserted: number }> {
    return apiPostJson("/instruments/sync", {});
  }
};
