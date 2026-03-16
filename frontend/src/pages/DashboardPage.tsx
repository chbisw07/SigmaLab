import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { api } from "../app/api/client";
import { useAsync } from "../app/hooks/useAsync";
import PageHeader from "../app/ui/PageHeader";
import EmptyState from "../app/ui/EmptyState";
import InlineError from "../app/ui/InlineError";
import { fmtDateTimeIso } from "../app/ui/format";
import type { BacktestRun, StrategyMetadata, Watchlist } from "../app/api/types";

type DashboardData = {
  health: { status: "ok" };
  runs: BacktestRun[];
  watchlists: Watchlist[];
  strategies: StrategyMetadata[];
};

export default function DashboardPage() {
  const st = useAsync<DashboardData>(
    async () => {
      const [health, backtests, watchlists, strategies] = await Promise.all([
        api.health(),
        api.listBacktests(),
        api.listWatchlists(),
        api.listStrategies()
      ]);
      return {
        health,
        runs: backtests.runs,
        watchlists,
        strategies: strategies.strategies
      };
    },
    []
  );

  const counts = useMemo(() => {
    if (st.status !== "success") return null;
    const runs = st.data.runs.length;
    const wls = st.data.watchlists.length;
    const strats = st.data.strategies.length;
    return { runs, wls, strats };
  }, [st]);

  if (st.status === "error") {
    return <InlineError title="Dashboard failed to load" error={st.error} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Dashboard"
        subtitle="A research-oriented overview of your watchlists, strategies, and recent runs."
        actions={
          <>
            <Link to="/backtests/new" className="btn primary">
              Run backtest
            </Link>
            <Link to="/watchlists" className="btn">
              Create watchlist
            </Link>
          </>
        }
      />

      {st.status !== "success" ? (
        <div className="panel">
          <div className="subtle">Loading…</div>
        </div>
      ) : (
        <>
          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 650 }}>Workspace</div>
              <span className="pill ok">API: {st.data.health.status}</span>
            </div>
            <div className="kpi-grid">
              <div className="kpi">
                <div className="kpi-label">Watchlists</div>
                <div className="kpi-value">{counts?.wls ?? "—"}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Strategies</div>
                <div className="kpi-value">{counts?.strats ?? "—"}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Runs</div>
                <div className="kpi-value">{counts?.runs ?? "—"}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Next step</div>
                <div className="kpi-value" style={{ fontSize: 14, fontWeight: 600, marginTop: 10 }}>
                  <Link to="/backtests/new" className="btn primary" style={{ padding: "7px 10px" }}>
                    New backtest
                  </Link>
                </div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Instruments</div>
                <div className="kpi-value" style={{ fontSize: 14, fontWeight: 600, marginTop: 10 }}>
                  <Link to="/instruments" className="btn" style={{ padding: "7px 10px" }}>
                    Sync / Search
                  </Link>
                </div>
              </div>
              <div className="kpi">
                <div className="kpi-label">Settings</div>
                <div className="kpi-value" style={{ fontSize: 14, fontWeight: 600, marginTop: 10 }}>
                  <Link to="/settings" className="btn" style={{ padding: "7px 10px" }}>
                    Broker config
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {st.data.watchlists.length === 0 ? (
            <EmptyState
              title="No watchlists yet"
              body={
                <>
                  Create a watchlist first, then add instruments. Watchlists are the universe for backtests.
                </>
              }
              actions={[
                { label: "Create watchlist", to: "/watchlists" },
                { label: "Sync instruments", to: "/instruments" }
              ]}
            />
          ) : null}

          <div className="panel">
            <div className="row" style={{ marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 650 }}>Recent backtests</div>
                <div className="subtle">Open a run to inspect metrics, trades, and annotated charts.</div>
              </div>
              <Link to="/backtests" className="btn">
                View all
              </Link>
            </div>

            {st.data.runs.length === 0 ? (
              <EmptyState
                title="No backtest runs yet"
                body={
                  <>
                    Run a backtest on a watchlist. Results will be persisted so you can revisit and compare later.
                  </>
                }
                actions={[{ label: "Run backtest", to: "/backtests/new" }]}
              />
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Strategy</th>
                    <th>Timeframe</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {st.data.runs.slice(0, 8).map((r) => (
                    <tr key={r.id}>
                      <td>
                        <Link to={`/backtests/${r.id}`} className="mono">
                          {r.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td style={{ fontWeight: 600 }}>{r.strategy_slug ?? "—"}</td>
                      <td className="mono">{r.timeframe}</td>
                      <td>
                        <span className={`pill ${r.status === "success" ? "ok" : r.status === "failed" ? "bad" : ""}`}>
                          {r.status}
                        </span>
                      </td>
                      <td>{fmtDateTimeIso(r.created_at)}</td>
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

