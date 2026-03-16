import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { OptimizationCandidateResult, OptimizationJob, UUID } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";
import { fmtDateTimeIso } from "../app/ui/format";

function fmtNum(v: unknown, digits = 3) {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export default function OptimizationDetailPage() {
  const { jobId } = useParams();
  const id = jobId as UUID | undefined;

  const [job, setJob] = useState<OptimizationJob | null>(null);
  const [candidates, setCandidates] = useState<OptimizationCandidateResult[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  async function load() {
    if (!id) return;
    setErr(null);
    try {
      const [j, c] = await Promise.all([api.getOptimization(id), api.listOptimizationCandidates(id)]);
      setJob(j.job);
      setCandidates(c.candidates);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!job) return;
    if (job.status !== "running" && job.status !== "pending") return;
    const t = window.setInterval(() => void load(), 1500);
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.status, id]);

  const progress = useMemo(() => {
    if (!job) return null;
    const total = job.total_combinations || 0;
    const done = job.completed_combinations || 0;
    const pct = total ? Math.round((done / total) * 100) : 0;
    return { total, done, pct };
  }, [job]);

  if (!id) return <InlineError title="Missing optimization id" error="No optimization id found in route." />;
  if (err && !job) return <InlineError title="Optimization failed to load" error={err} />;

  async function savePreset(c: OptimizationCandidateResult) {
    if (!job) return;
    const name = window.prompt("Preset name?", `opt_${job.strategy_slug ?? "strategy"}_${c.rank}`);
    if (!name) return;
    setSaving(c.id);
    setSaveErr(null);
    try {
      await api.savePresetFromOptimization(job.id, { candidate_id: c.id, name });
      alert("Preset saved.");
    } catch (e) {
      setSaveErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="page">
      <PageHeader
        title="Optimization Detail"
        subtitle={
          <>
            <Link to="/optimizations">Optimization</Link> / <span className="mono">{id}</span>
          </>
        }
        actions={
          <>
            <Link to="/optimizations/new" className="btn primary">
              New
            </Link>
            <button className="btn" onClick={() => void load()}>
              Refresh
            </button>
          </>
        }
      />

      {!job || candidates === null ? (
        <div className="panel">
          <div className="subtle">Loading…</div>
        </div>
      ) : (
        <>
          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 650 }}>{job.strategy_slug ?? "—"}</div>
              <div className="mono">
                {job.objective_metric} ({job.sort_direction})
              </div>
            </div>
            <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
              <div className="kpi">
                <div className="kpi-label">Status</div>
                <div className="kpi-value">{job.status}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Progress</div>
                <div className="kpi-value">
                  {progress?.done}/{progress?.total} ({progress?.pct}%)
                </div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Timeframe</div>
                <div className="kpi-value mono">{job.timeframe}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Created</div>
                <div className="kpi-value">{fmtDateTimeIso(job.created_at)}</div>
              </div>
            </div>
            <div className="subtle" style={{ marginTop: 10 }}>
              Range: <span className="mono">{job.start_at ?? "—"}</span> → <span className="mono">{job.end_at ?? "—"}</span>
            </div>
          </div>

          {err ? (
            <div className="panel">
              <div style={{ color: "rgba(251,113,133,0.95)", fontWeight: 600 }}>Load error</div>
              <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.72)" }}>
                {err}
              </pre>
            </div>
          ) : null}

          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 650 }}>Ranked candidates</div>
                <div className="subtle">
                  Each row links to a persisted BacktestRun. Use the existing Results page to inspect trades/charts.
                </div>
              </div>
              <div className="subtle mono">{candidates.length} candidates</div>
            </div>

            {saveErr ? (
              <div className="subtle" style={{ marginBottom: 10, color: "rgba(251,113,133,0.92)" }}>
                {saveErr}
              </div>
            ) : null}

            {candidates.length === 0 ? (
              <div className="subtle">No candidates yet. If the job is running, this will populate when complete.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Objective</th>
                    <th>Return</th>
                    <th>Drawdown</th>
                    <th>PF</th>
                    <th>Trades</th>
                    <th>Win</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c) => (
                    <tr key={c.id}>
                      <td className="mono" style={{ fontWeight: 650 }}>
                        {c.rank}
                      </td>
                      <td className="mono">{fmtNum(c.objective_value, 4)}</td>
                      <td className="mono">{fmtNum((c.metrics_json as any).net_return_pct, 4)}</td>
                      <td className="mono">{fmtNum((c.metrics_json as any).max_drawdown_pct, 4)}</td>
                      <td className="mono">{fmtNum((c.metrics_json as any).profit_factor, 3)}</td>
                      <td className="mono">{String((c.metrics_json as any).total_trades ?? "—")}</td>
                      <td className="mono">{fmtNum((c.metrics_json as any).win_rate, 3)}</td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", flexWrap: "wrap" }}>
                          <Link to={`/backtests/${c.backtest_run_id}`} className="btn primary">
                            Open run
                          </Link>
                          <button className="btn" disabled={saving === c.id} onClick={() => void savePreset(c)}>
                            {saving === c.id ? "Saving…" : "Save preset"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}

