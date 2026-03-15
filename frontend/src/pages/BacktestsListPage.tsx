import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../app/api/client";
import type { BacktestRun } from "../app/api/types";
import EmptyState from "../app/ui/EmptyState";
import { fmtDateTimeIso } from "../app/ui/format";

function statusPill(status: string) {
  const cls = status === "success" ? "pill ok" : status === "failed" ? "pill bad" : "pill";
  return <span className={cls}>{status}</span>;
}

export default function BacktestsListPage() {
  const [runs, setRuns] = useState<BacktestRun[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await api.listBacktests();
      setRuns(data.runs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setRuns(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="page">
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <h1 className="h1">Backtests</h1>
          <div className="subtle">Run strategies on watchlists and inspect persisted results.</div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <Link to="/backtests/new" className="btn primary">
            New backtest
          </Link>
          <button className="btn" onClick={() => void load()}>
            Refresh
          </button>
        </div>
      </div>

      <div className="panel">
        {err ? (
          <div>
            <div style={{ color: "rgba(251,113,133,0.95)", fontWeight: 600 }}>Failed to load runs</div>
            <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.72)" }}>
              {err}
            </pre>
          </div>
        ) : !runs ? (
          <div className="subtle">Loading…</div>
        ) : runs.length === 0 ? (
          <EmptyState
            title="No backtest runs found yet"
            body={
              <>
                Create a watchlist, pick a built-in strategy, and run your first backtest. Results will be persisted for
                later inspection and comparison.
              </>
            }
            actions={[
              { label: "Create watchlist", to: "/watchlists" },
              { label: "Run backtest", to: "/backtests/new" }
            ]}
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Run</th>
                <th>Strategy</th>
                <th>Timeframe</th>
                <th>Date range</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to={`/backtests/${r.id}`} className="mono">
                      {r.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{r.strategy_slug ?? "—"}</div>
                    <div className="subtle">v{r.strategy_code_version ?? "—"}</div>
                  </td>
                  <td className="mono">{r.timeframe}</td>
                  <td className="mono">{r.date_range}</td>
                  <td>{statusPill(r.status)}</td>
                  <td>{fmtDateTimeIso(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
