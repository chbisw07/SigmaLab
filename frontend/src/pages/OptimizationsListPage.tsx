import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../app/api/client";
import type { OptimizationJob } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import EmptyState from "../app/ui/EmptyState";
import InlineError from "../app/ui/InlineError";
import { fmtDateTimeIso } from "../app/ui/format";

function statusPill(status: string) {
  const cls = status === "success" ? "pill ok" : status === "failed" ? "pill bad" : "pill";
  return <span className={cls}>{status}</span>;
}

export default function OptimizationsListPage() {
  const [jobs, setJobs] = useState<OptimizationJob[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    setJobs(null);
    try {
      const res = await api.listOptimizations();
      setJobs(res.jobs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (err && jobs === null) {
    return <InlineError title="Optimizations failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Optimization"
        subtitle="Grid-search tunable strategy parameters and rank candidate results."
        actions={
          <>
            <Link to="/optimizations/new" className="btn primary">
              New optimization
            </Link>
            <button className="btn" onClick={() => void load()}>
              Refresh
            </button>
          </>
        }
      />

      <div className="panel">
        {jobs === null ? (
          <div className="subtle">Loading…</div>
        ) : jobs.length === 0 ? (
          <EmptyState
            title="No optimization jobs yet"
            body={
              <>
                Create an optimization to explore parameter combinations. Each candidate links to a real BacktestRun so
                you can inspect trades, charts, and metrics in the existing Results UX.
              </>
            }
            actions={[
              { label: "New optimization", to: "/optimizations/new" },
              { label: "Strategies", to: "/strategies" }
            ]}
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Strategy</th>
                <th>Objective</th>
                <th>Progress</th>
                <th>Status</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td className="mono" style={{ fontWeight: 650 }}>
                    {j.id.slice(0, 8)}
                  </td>
                  <td>
                    <div style={{ fontWeight: 650 }}>{j.strategy_slug ?? "—"}</div>
                    <div className="subtle">v{j.strategy_code_version ?? "—"}</div>
                  </td>
                  <td className="mono">
                    {j.objective_metric} ({j.sort_direction})
                  </td>
                  <td className="mono">
                    {j.completed_combinations}/{j.total_combinations}
                  </td>
                  <td>{statusPill(j.status)}</td>
                  <td>{fmtDateTimeIso(j.created_at)}</td>
                  <td style={{ textAlign: "right" }}>
                    <Link to={`/optimizations/${j.id}`} className="btn">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

