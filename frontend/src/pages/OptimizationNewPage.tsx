import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { ParameterSpec, StrategyDetailResponse, StrategyMetadata, UUID, Watchlist } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";
import EmptyState from "../app/ui/EmptyState";

type Selection = Record<
  string,
  { mode: "range"; min: number; max: number; step: number } | { mode: "values"; values: any[] }
>;

function isoLocalDate(d: Date) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function estimateCount(selection: Selection): number {
  let n = 1;
  for (const k of Object.keys(selection)) {
    const cfg: any = selection[k];
    if (cfg.mode === "values") {
      n *= Array.isArray(cfg.values) ? cfg.values.length : 0;
    } else {
      const step = Number(cfg.step);
      if (!(step > 0)) return 0;
      const span = Number(cfg.max) - Number(cfg.min);
      const cnt = Math.floor(span / step) + 1;
      n *= Math.max(0, cnt);
    }
  }
  return n;
}

function defaultSelectionForParam(p: ParameterSpec): Selection[string] | null {
  if (!p.tunable) return null;
  if (p.grid_values && p.grid_values.length) {
    return { mode: "values", values: p.grid_values };
  }
  if (p.type === "enum" && p.enum_values) return { mode: "values", values: p.enum_values };
  if (p.type === "bool") return { mode: "values", values: [true, false] };
  if (p.type === "int" || p.type === "float") {
    const min = p.min ?? (typeof p.default === "number" ? p.default : 0);
    const max = p.max ?? (typeof p.default === "number" ? p.default : min);
    const step = p.step ?? (p.type === "int" ? 1 : 0.5);
    return { mode: "range", min: Number(min), max: Number(max), step: Number(step) };
  }
  return null;
}

export default function OptimizationNewPage() {
  const nav = useNavigate();
  const [sp] = useSearchParams();

  const [watchlists, setWatchlists] = useState<Watchlist[] | null>(null);
  const [strategies, setStrategies] = useState<StrategyMetadata[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [watchlistId, setWatchlistId] = useState<UUID>(sp.get("watchlist") ?? "");
  const [strategySlug, setStrategySlug] = useState<string>(sp.get("strategy") ?? "");
  const [timeframe, setTimeframe] = useState<string>("");

  const today = new Date();
  const [start, setStart] = useState<string>(isoLocalDate(new Date(today.getFullYear(), today.getMonth() - 2, today.getDate())));
  const [end, setEnd] = useState<string>(isoLocalDate(today));

  const [objective, setObjective] = useState<string>("net_return_pct");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const [maxCombos, setMaxCombos] = useState<number>(250);

  const [detail, setDetail] = useState<StrategyDetailResponse | null>(null);
  const [selection, setSelection] = useState<Selection>({});
  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [previewErr, setPreviewErr] = useState<string | null>(null);

  const [running, setRunning] = useState(false);
  const [runErr, setRunErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    (async () => {
      try {
        const [wls, strats] = await Promise.all([api.listWatchlists(), api.listStrategies()]);
        setWatchlists(wls);
        setStrategies(strats.strategies);
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, []);

  useEffect(() => {
    if (!strategySlug) {
      setDetail(null);
      setSelection({});
      setTimeframe("");
      return;
    }
    setRunErr(null);
    setPreviewErr(null);
    setPreviewCount(null);
    (async () => {
      try {
        const d = await api.getStrategy(strategySlug);
        setDetail(d);
        setTimeframe(d.metadata.timeframe);
        // Preselect up to 2 tunable params to reduce “blank page” feeling.
        const tunables = d.parameters.filter((p) => p.tunable);
        const initial: Selection = {};
        for (const p of tunables.slice(0, 2)) {
          const cfg = defaultSelectionForParam(p);
          if (cfg) initial[p.key] = cfg as any;
        }
        setSelection(initial);
      } catch (e) {
        setRunErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [strategySlug]);

  const selectedKeys = useMemo(() => Object.keys(selection).sort(), [selection]);
  const estimated = useMemo(() => estimateCount(selection), [selection]);
  const tooLarge = estimated > maxCombos;

  async function preview() {
    if (!strategySlug) return;
    setPreviewErr(null);
    try {
      const res = await api.previewOptimization({ strategy_slug: strategySlug, selection });
      setPreviewCount(res.total_combinations);
    } catch (e) {
      setPreviewErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function create() {
    if (!strategySlug || !watchlistId || !timeframe || !start || !end) return;
    setRunning(true);
    setRunErr(null);
    try {
      const payload = {
        strategy_slug: strategySlug,
        watchlist_id: watchlistId,
        timeframe,
        start: new Date(start + "T00:00:00").toISOString(),
        end: new Date(end + "T00:00:00").toISOString(),
        objective_metric: objective,
        sort_direction: direction,
        selection,
        max_combinations: maxCombos
      };
      const res = await api.createOptimization(payload);
      nav(`/optimizations/${res.job_id}`);
    } catch (e) {
      setRunErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  if (err) return <InlineError title="Optimization form failed to load" error={err} />;

  const canCreate = Boolean(strategySlug && watchlistId && timeframe && start && end && selectedKeys.length > 0 && !tooLarge);

  return (
    <div className="page">
      <PageHeader
        title="New Optimization"
        subtitle="Define a deterministic grid search over tunable parameters. Each candidate links to a persisted BacktestRun."
        actions={
          <Link to="/optimizations" className="btn">
            View jobs
          </Link>
        }
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div style={{ fontWeight: 650 }}>Configuration</div>
          <div className="subtle mono">Estimated combos: {estimated}{previewCount !== null ? ` (server: ${previewCount})` : ""}</div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          <div>
            <div className="subtle">Watchlist</div>
            <select className="input" value={watchlistId} onChange={(e) => setWatchlistId(e.target.value)}>
              <option value="">Select watchlist…</option>
              {(watchlists ?? []).map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
            {!watchlists || watchlists.length === 0 ? (
              <div className="subtle" style={{ marginTop: 8 }}>
                No watchlists yet. <Link to="/watchlists">Create one</Link>.
              </div>
            ) : null}
          </div>

          <div>
            <div className="subtle">Strategy</div>
            <select className="input" value={strategySlug} onChange={(e) => setStrategySlug(e.target.value)}>
              <option value="">Select strategy…</option>
              {(strategies ?? []).map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.name} ({s.slug})
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="subtle">Timeframe</div>
            <input className="input mono" value={timeframe} onChange={(e) => setTimeframe(e.target.value)} placeholder="e.g. 1D, 15m" />
            <div className="subtle" style={{ marginTop: 6 }}>
              Default is taken from strategy metadata; you can override.
            </div>
          </div>

          <div>
            <div className="subtle">Start date</div>
            <input className="input mono" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </div>
          <div>
            <div className="subtle">End date</div>
            <input className="input mono" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
          <div>
            <div className="subtle">Objective</div>
            <select className="input" value={objective} onChange={(e) => setObjective(e.target.value)}>
              <option value="net_return_pct">net_return_pct</option>
              <option value="profit_factor">profit_factor</option>
              <option value="max_drawdown_pct">max_drawdown_pct</option>
              <option value="expectancy_pct">expectancy_pct</option>
              <option value="win_rate">win_rate</option>
              <option value="total_trades">total_trades</option>
            </select>
            <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
              <button className={`btn ${direction === "desc" ? "primary" : ""}`} onClick={() => setDirection("desc")}>
                Desc
              </button>
              <button className={`btn ${direction === "asc" ? "primary" : ""}`} onClick={() => setDirection("asc")}>
                Asc
              </button>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 12, flexWrap: "wrap" }}>
          <div className="subtle">
            Selected params: <span className="mono">{selectedKeys.join(", ") || "—"}</span>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div className="subtle">Max combos</div>
            <input className="input mono" style={{ width: 120 }} type="number" value={maxCombos} onChange={(e) => setMaxCombos(Number(e.target.value || "0"))} />
          </div>
          <button className="btn" disabled={!strategySlug || selectedKeys.length === 0} onClick={() => void preview()}>
            Preview
          </button>
          <button className="btn primary" disabled={!canCreate || running} onClick={() => void create()}>
            {running ? "Starting…" : "Start optimization"}
          </button>
          <Link to="/settings" className="btn">
            Kite setup
          </Link>
        </div>

        {tooLarge ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            Estimated {estimated} combinations exceeds max {maxCombos}. Reduce ranges/params or increase step.
          </div>
        ) : null}
        {previewErr ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {previewErr}
          </div>
        ) : null}
        {runErr ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {runErr}
          </div>
        ) : null}
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Parameter grid</div>
            <div className="subtle">Only tunable parameters are eligible. Select 1–4 params to avoid combinatoric blowups.</div>
          </div>
          {strategySlug ? (
            <Link to={`/strategies/${encodeURIComponent(strategySlug)}`} className="btn">
              Open strategy
            </Link>
          ) : null}
        </div>

        {!strategySlug ? (
          <EmptyState title="Select a strategy" body={<>Pick a strategy above to configure its tunable parameters.</>} />
        ) : detail === null ? (
          <div className="subtle">Loading strategy parameters…</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>Param</th>
                <th>Type</th>
                <th>Grid</th>
              </tr>
            </thead>
            <tbody>
              {detail.parameters.filter((p) => p.tunable).map((p) => {
                const cfg = selection[p.key] as any;
                const enabled = Boolean(cfg);
                const onToggle = () => {
                  setPreviewCount(null);
                  setPreviewErr(null);
                  setSelection((prev) => {
                    const next = { ...prev };
                    if (next[p.key]) {
                      delete next[p.key];
                      return next;
                    }
                    const def = defaultSelectionForParam(p);
                    if (def) next[p.key] = def as any;
                    return next;
                  });
                };

                return (
                  <tr key={p.key}>
                    <td style={{ width: 40 }}>
                      <input type="checkbox" checked={enabled} onChange={onToggle} />
                    </td>
                    <td>
                      <div style={{ fontWeight: 650 }}>{p.label}</div>
                      <div className="subtle mono">{p.key}</div>
                    </td>
                    <td className="mono">{p.type}</td>
                    <td>
                      {!enabled ? (
                        <span className="subtle">—</span>
                      ) : cfg.mode === "values" ? (
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                          <div className="subtle">values</div>
                          <input
                            className="input mono"
                            style={{ width: 520, maxWidth: "100%" }}
                            value={Array.isArray(cfg.values) ? cfg.values.join(",") : ""}
                            onChange={(e) => {
                              const raw = e.target.value;
                              const parts = raw
                                .split(",")
                                .map((x) => x.trim())
                                .filter(Boolean);
                              let values: any[] = parts;
                              if (p.type === "int") values = parts.map((x) => Number(x));
                              if (p.type === "float") values = parts.map((x) => Number(x));
                              if (p.type === "bool") values = parts.map((x) => x === "true" || x === "1" || x === "yes");
                              setSelection((prev) => ({ ...prev, [p.key]: { mode: "values", values } as any }));
                            }}
                          />
                          <div className="subtle">(comma-separated)</div>
                        </div>
                      ) : (
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                          <div className="subtle">min</div>
                          <input
                            className="input mono"
                            style={{ width: 120 }}
                            type="number"
                            value={cfg.min}
                            onChange={(e) => setSelection((prev) => ({ ...prev, [p.key]: { ...cfg, min: Number(e.target.value) } }))}
                          />
                          <div className="subtle">max</div>
                          <input
                            className="input mono"
                            style={{ width: 120 }}
                            type="number"
                            value={cfg.max}
                            onChange={(e) => setSelection((prev) => ({ ...prev, [p.key]: { ...cfg, max: Number(e.target.value) } }))}
                          />
                          <div className="subtle">step</div>
                          <input
                            className="input mono"
                            style={{ width: 120 }}
                            type="number"
                            value={cfg.step}
                            onChange={(e) => setSelection((prev) => ({ ...prev, [p.key]: { ...cfg, step: Number(e.target.value) } }))}
                          />
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

