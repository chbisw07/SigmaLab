import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { BacktestMetric, BacktestRun, BacktestTrade, UUID } from "../app/api/types";
import { fmtDateTimeIso } from "../app/ui/format";
import MetricCards from "../components/MetricCards";
import EquityChart from "../components/EquityChart";
import DrawdownChart from "../components/DrawdownChart";
import TradesTable from "../components/TradesTable";
import SymbolsTable from "../components/SymbolsTable";
import TradeChart from "../components/TradeChart";
import JsonBlock from "../components/JsonBlock";

type TabKey = "summary" | "equity" | "trades" | "symbols" | "charts" | "config";
const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "summary", label: "Summary" },
  { key: "equity", label: "Equity" },
  { key: "trades", label: "Trades" },
  { key: "symbols", label: "Symbols" },
  { key: "charts", label: "Charts" },
  { key: "config", label: "Config" }
];

export default function BacktestRunDetailPage() {
  const { runId } = useParams();
  const [search, setSearch] = useSearchParams();
  const tab = (search.get("tab") as TabKey | null) ?? "summary";

  const [run, setRun] = useState<BacktestRun | null>(null);
  const [trades, setTrades] = useState<BacktestTrade[] | null>(null);
  const [metrics, setMetrics] = useState<BacktestMetric[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [selectedInstrumentId, setSelectedInstrumentId] = useState<UUID | null>(null);
  const [selectedTradeId, setSelectedTradeId] = useState<UUID | null>(null);

  useEffect(() => {
    if (!runId) return;
    setErr(null);
    setRun(null);
    setTrades(null);
    setMetrics(null);

    (async () => {
      try {
        const [r, t, m] = await Promise.all([
          api.getBacktestRun(runId),
          api.listBacktestTrades(runId),
          api.listBacktestMetrics(runId)
        ]);
        setRun(r.run);
        setTrades(t.trades);
        setMetrics(m.metrics);
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [runId]);

  const overall = useMemo(() => {
    return (metrics ?? []).find((x) => x.symbol === null) ?? null;
  }, [metrics]);

  const perSymbol = useMemo(() => {
    return (metrics ?? []).filter((x) => x.symbol !== null) as BacktestMetric[];
  }, [metrics]);

  const watchlistSymbols = useMemo(() => {
    const items = run?.watchlist_snapshot_json ?? [];
    return items.map((x) => ({ instrument_id: x.instrument_id, symbol: x.symbol, exchange: x.exchange ?? "" }));
  }, [run]);

  const selectedSymbol = useMemo(() => {
    if (!selectedInstrumentId) return null;
    return watchlistSymbols.find((x) => x.instrument_id === selectedInstrumentId)?.symbol ?? null;
  }, [selectedInstrumentId, watchlistSymbols]);

  function setTab(next: TabKey) {
    const p = new URLSearchParams(search);
    p.set("tab", next);
    setSearch(p, { replace: true });
  }

  if (!runId) {
    return (
      <div className="page">
        <div className="panel">Missing run id.</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <div className="subtle">
            <Link to="/backtests">Backtests</Link> / <span className="mono">{runId}</span>
          </div>
          <h1 className="h1" style={{ marginTop: 4 }}>
            {run?.strategy_slug ?? "Backtest Run"}
          </h1>
          <div className="subtle">
            Timeframe <span className="mono">{run?.timeframe ?? "—"}</span> • Status{" "}
            <span className="mono">{run?.status ?? "—"}</span> • Created {fmtDateTimeIso(run?.created_at ?? null)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <a className="btn" href={api.metricsCsvUrl(runId)}>
            Export metrics CSV
          </a>
          <a className="btn primary" href={api.tradesCsvUrl(runId)}>
            Export trades CSV
          </a>
        </div>
      </div>

      {err ? (
        <div className="panel">
          <div style={{ color: "rgba(251,113,133,0.95)", fontWeight: 600 }}>Failed to load run</div>
          <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.72)" }}>
            {err}
          </pre>
        </div>
      ) : !run || !trades || !metrics ? (
        <div className="panel">
          <div className="subtle">Loading…</div>
        </div>
      ) : (
        <>
          <div className="panel">
            <div className="tabs">
              {TABS.map((t) => (
                <div
                  key={t.key}
                  className={`tab ${tab === t.key ? "active" : ""}`}
                  onClick={() => setTab(t.key)}
                  role="button"
                  tabIndex={0}
                >
                  {t.label}
                </div>
              ))}
            </div>
          </div>

          {tab === "summary" ? (
            <div className="panel">
              <MetricCards metrics={overall?.metrics_json ?? {}} />
              <div style={{ marginTop: 12 }} className="subtle">
                Note: entry reason is persisted as whatever PH4 captured (often the generic{" "}
                <span className="mono">signal_entry</span>). Exit reason is shown using{" "}
                <span className="mono">close_reason</span>.
              </div>
            </div>
          ) : null}

          {tab === "equity" ? (
            <div className="panel">
              <div className="row" style={{ marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 650 }}>Portfolio equity</div>
                  <div className="subtle">From persisted backtest metrics artifacts.</div>
                </div>
              </div>
              <EquityChart points={overall?.equity_curve_json ?? []} />
              <div style={{ height: 12 }} />
              <DrawdownChart points={overall?.drawdown_curve_json ?? []} />
            </div>
          ) : null}

          {tab === "trades" ? (
            <div className="panel">
              <TradesTable
                trades={trades}
                onSelectTrade={(t) => {
                  setSelectedTradeId(t.id);
                  setSelectedInstrumentId(t.instrument_id);
                  setTab("charts");
                }}
              />
            </div>
          ) : null}

          {tab === "symbols" ? (
            <div className="panel">
              <SymbolsTable
                metrics={perSymbol}
                symbols={watchlistSymbols}
                onSelectInstrument={(instrumentId) => {
                  setSelectedInstrumentId(instrumentId);
                  setSelectedTradeId(null);
                  setTab("charts");
                }}
              />
            </div>
          ) : null}

          {tab === "charts" ? (
            <div className="panel">
              <div className="row" style={{ marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 650 }}>Annotated chart</div>
                  <div className="subtle">
                    Candles via MarketDataService; markers from persisted trades; overlays computed deterministically from
                    strategy + params.
                  </div>
                </div>

                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <select
                    className="input"
                    style={{ width: 280 }}
                    value={selectedInstrumentId ?? ""}
                    onChange={(e) => {
                      const v = e.target.value || null;
                      setSelectedInstrumentId(v);
                      setSelectedTradeId(null);
                    }}
                  >
                    <option value="">Select symbol…</option>
                    {watchlistSymbols.map((s) => (
                      <option key={s.instrument_id} value={s.instrument_id}>
                        {s.symbol}
                      </option>
                    ))}
                  </select>
                  <div className="subtle mono">{selectedSymbol ?? ""}</div>
                </div>
              </div>

              {selectedInstrumentId ? (
                <TradeChart
                  runId={runId}
                  instrumentId={selectedInstrumentId}
                  selectedTradeId={selectedTradeId}
                />
              ) : (
                <div className="subtle">Pick a symbol to view candles and trade markers.</div>
              )}
            </div>
          ) : null}

          {tab === "config" ? (
            <div className="panel">
              <div className="row" style={{ marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 650 }}>Run configuration</div>
                  <div className="subtle">Reproducibility metadata captured at run time.</div>
                </div>
              </div>

              <div className="panel" style={{ background: "rgba(255,255,255,0.04)" }}>
                <div className="subtle">Params</div>
                <JsonBlock value={run.params_json} />
              </div>
              <div className="panel" style={{ background: "rgba(255,255,255,0.04)" }}>
                <div className="subtle">Execution assumptions</div>
                <JsonBlock value={run.execution_assumptions_json} />
              </div>
              <div className="panel" style={{ background: "rgba(255,255,255,0.04)" }}>
                <div className="subtle">Watchlist snapshot</div>
                <JsonBlock value={run.watchlist_snapshot_json} />
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

