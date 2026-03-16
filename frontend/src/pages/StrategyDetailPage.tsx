import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { ParameterSpec, StrategyDetailResponse } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";

function paramRow(p: ParameterSpec) {
  return (
    <tr key={p.key}>
      <td className="mono" style={{ fontWeight: 650 }}>
        {p.key}
      </td>
      <td>{p.label}</td>
      <td className="mono">{p.type}</td>
      <td className="mono">{String(p.default ?? "")}</td>
      <td className="mono">{p.min ?? "—"}</td>
      <td className="mono">{p.max ?? "—"}</td>
      <td className="mono">{p.step ?? "—"}</td>
      <td className="subtle">{p.tunable ? "yes" : "no"}</td>
    </tr>
  );
}

export default function StrategyDetailPage() {
  const { slug } = useParams();
  const s = slug ? decodeURIComponent(slug) : null;

  const [detail, setDetail] = useState<StrategyDetailResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!s) return;
    setErr(null);
    setDetail(null);
    (async () => {
      try {
        const d = await api.getStrategy(s);
        setDetail(d);
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [s]);

  const defaults = useMemo(() => {
    if (!detail) return {};
    const out: Record<string, unknown> = {};
    for (const p of detail.parameters) out[p.key] = p.default;
    return out;
  }, [detail]);

  if (!s) {
    return <InlineError title="Missing strategy slug" error="No strategy slug found in route." />;
  }
  if (err) {
    return <InlineError title="Strategy failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title={detail?.metadata.name ?? "Strategy"}
        subtitle={
          <>
            <Link to="/strategies">Strategies</Link> / <span className="mono">{s}</span>
          </>
        }
        actions={
          <Link to={`/backtests/new?strategy=${encodeURIComponent(s)}`} className="btn primary">
            Run backtest
          </Link>
        }
      />

      {!detail ? (
        <div className="panel">
          <div className="subtle">Loading…</div>
        </div>
      ) : (
        <>
          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 650 }}>Metadata</div>
                <div className="subtle">{detail.metadata.description ?? "—"}</div>
              </div>
              <span className="pill">
                {detail.metadata.category} • {detail.metadata.timeframe} • v{detail.metadata.version}
              </span>
            </div>
            <div className="subtle">
              Long-only: <span className="mono">{String(detail.metadata.long_only)}</span>
            </div>
          </div>

          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 650 }}>Parameters</div>
                <div className="subtle">Defaults shown here are used as the initial values in the backtest form.</div>
              </div>
              <Link to={`/backtests/new?strategy=${encodeURIComponent(s)}`} className="btn">
                Use defaults
              </Link>
            </div>

            <table className="table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Label</th>
                  <th>Type</th>
                  <th>Default</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Step</th>
                  <th>Tunable</th>
                </tr>
              </thead>
              <tbody>{detail.parameters.map(paramRow)}</tbody>
            </table>

            <div className="panel" style={{ marginTop: 12, background: "rgba(255,255,255,0.04)" }}>
              <div className="subtle">Default params snapshot</div>
              <pre className="mono" style={{ margin: "10px 0 0 0", whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.78)" }}>
                {JSON.stringify(defaults, null, 2)}
              </pre>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

