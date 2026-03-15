import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../app/api/client";
import type { StrategyMetadata } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";

export default function StrategiesPage() {
  const [rows, setRows] = useState<StrategyMetadata[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");

  async function load() {
    setErr(null);
    try {
      const data = await api.listStrategies();
      setRows(data.strategies);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setRows(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const filtered = useMemo(() => {
    if (!rows) return null;
    const qq = q.trim().toLowerCase();
    if (!qq) return rows;
    return rows.filter((s) => (s.name + " " + s.slug).toLowerCase().includes(qq));
  }, [q, rows]);

  if (err && rows === null) {
    return <InlineError title="Strategies failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Strategies"
        subtitle="Built-in signal-generating strategies (PH3). Select one to inspect parameters and run backtests."
        actions={
          <>
            <input className="input" style={{ width: 240 }} placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
            <button className="btn" onClick={() => void load()}>
              Refresh
            </button>
          </>
        }
      />

      <div className="panel">
        {filtered === null ? (
          <div className="subtle">Loading…</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Category</th>
                <th>Timeframe</th>
                <th>Version</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.slug}>
                  <td>
                    <div style={{ fontWeight: 650 }}>
                      <Link to={`/strategies/${encodeURIComponent(s.slug)}`}>{s.name}</Link>
                    </div>
                    <div className="subtle">{s.description ?? "—"}</div>
                  </td>
                  <td className="mono">{s.category}</td>
                  <td className="mono">{s.timeframe}</td>
                  <td className="mono">{s.version}</td>
                  <td style={{ textAlign: "right" }}>
                    <Link to={`/backtests/new?strategy=${encodeURIComponent(s.slug)}`} className="btn primary">
                      Run backtest
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {err ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {err}
          </div>
        ) : null}
      </div>
    </div>
  );
}

