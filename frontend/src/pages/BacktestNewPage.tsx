import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { ParameterSpec, StrategyMetadata, UUID, Watchlist } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";
import EmptyState from "../app/ui/EmptyState";

function isoLocalDate(d: Date) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function paramInput(
  p: ParameterSpec,
  value: unknown,
  setValue: (v: unknown) => void
) {
  const id = `param-${p.key}`;
  if (p.type === "bool") {
    return (
      <label key={p.key} style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <input
          id={id}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => setValue(e.target.checked)}
        />
        <div>
          <div style={{ fontWeight: 650 }}>{p.label}</div>
          <div className="subtle mono">{p.key}</div>
        </div>
      </label>
    );
  }

  if (p.type === "enum" && p.enum_values) {
    return (
      <div key={p.key}>
        <div style={{ fontWeight: 650 }}>{p.label}</div>
        <div className="subtle mono">{p.key}</div>
        <select className="input" value={String(value ?? "")} onChange={(e) => setValue(e.target.value)}>
          {p.enum_values.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </div>
    );
  }

  const step = p.step ?? (p.type === "int" ? 1 : 0.01);
  const min = p.min ?? undefined;
  const max = p.max ?? undefined;
  return (
    <div key={p.key}>
      <div style={{ fontWeight: 650 }}>{p.label}</div>
      <div className="subtle mono">{p.key}</div>
      <input
        className="input"
        type="number"
        step={step}
        min={min}
        max={max}
        value={typeof value === "number" || typeof value === "string" ? String(value) : ""}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === "") return setValue("");
          const n = Number(raw);
          setValue(Number.isFinite(n) ? n : raw);
        }}
      />
    </div>
  );
}

export default function BacktestNewPage() {
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

  const [paramsSpec, setParamsSpec] = useState<ParameterSpec[] | null>(null);
  const [params, setParams] = useState<Record<string, unknown>>({});
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
      setParamsSpec(null);
      setParams({});
      setTimeframe("");
      return;
    }
    setRunErr(null);
    setParamsSpec(null);
    (async () => {
      try {
        const d = await api.getStrategy(strategySlug);
        setParamsSpec(d.parameters);
        const initial: Record<string, unknown> = {};
        for (const p of d.parameters) initial[p.key] = p.default;
        setParams(initial);
        setTimeframe(d.metadata.timeframe);
      } catch (e) {
        setRunErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [strategySlug]);

  const canRun = useMemo(() => {
    return Boolean(watchlistId && strategySlug && timeframe && start && end);
  }, [watchlistId, strategySlug, timeframe, start, end]);

  async function run() {
    if (!canRun) return;
    setRunning(true);
    setRunErr(null);
    try {
      const validated = await api.validateStrategy(strategySlug, params);
      const payload = {
        strategy_slug: strategySlug,
        watchlist_id: watchlistId,
        timeframe,
        start: new Date(start + "T00:00:00").toISOString(),
        end: new Date(end + "T00:00:00").toISOString(),
        params: validated.validated
      };
      const res = await api.createBacktest(payload);
      nav(`/backtests/${res.run_id}`);
    } catch (e) {
      setRunErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  if (err) return <InlineError title="Backtest form failed to load" error={err} />;

  return (
    <div className="page">
      <PageHeader
        title="Run Backtest"
        subtitle="Choose a watchlist and strategy, set the date range and params, then run a persisted backtest."
        actions={
          <Link to="/backtests" className="btn">
            View runs
          </Link>
        }
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div style={{ fontWeight: 650 }}>Configuration</div>
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
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            <button className="btn primary" disabled={!canRun || running} onClick={() => void run()}>
              {running ? "Running…" : "Run backtest"}
            </button>
            <Link to="/settings" className="btn">
              Kite setup
            </Link>
          </div>
        </div>
        {runErr ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {runErr}
          </div>
        ) : null}
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Parameters</div>
            <div className="subtle">These are validated using the strategy schema before the backtest runs.</div>
          </div>
          {strategySlug ? (
            <Link to={`/strategies/${encodeURIComponent(strategySlug)}`} className="btn">
              Open strategy
            </Link>
          ) : null}
        </div>

        {!strategySlug ? (
          <EmptyState title="Select a strategy" body={<>Pick a strategy above to configure its parameters.</>} />
        ) : paramsSpec === null ? (
          <div className="subtle">Loading strategy parameters…</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
            {paramsSpec.map((p) =>
              paramInput(p, params[p.key], (v) => setParams((prev) => ({ ...prev, [p.key]: v })))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
