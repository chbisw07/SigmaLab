import React, { useMemo } from "react";
import type { BacktestMetric, UUID } from "../app/api/types";
import { fmtNum, fmtPct } from "../app/ui/format";

export default function SymbolsTable({
  metrics,
  symbols,
  onSelectInstrument
}: {
  metrics: BacktestMetric[];
  symbols: Array<{ instrument_id: UUID; symbol: string; exchange: string }>;
  onSelectInstrument: (instrumentId: UUID) => void;
}) {
  const bySymbol = useMemo(() => {
    const m = new Map<string, BacktestMetric>();
    for (const r of metrics) {
      if (r.symbol) m.set(r.symbol, r);
    }
    return m;
  }, [metrics]);

  const rows = useMemo(() => {
    return symbols
      .map((s) => ({ ...s, metric: bySymbol.get(s.symbol) ?? null }))
      .filter((x) => x.metric != null);
  }, [symbols, bySymbol]);

  return (
    <div>
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <div style={{ fontWeight: 650 }}>Symbols</div>
          <div className="subtle">Per-symbol metrics persisted by PH4.</div>
        </div>
        <div className="subtle mono">{rows.length}</div>
      </div>

      {rows.length === 0 ? (
        <div className="subtle">No per-symbol metrics rows found for this run.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Net return</th>
              <th>Max drawdown</th>
              <th>Trades</th>
              <th>Win rate</th>
              <th>Profit factor</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const mj = r.metric?.metrics_json ?? {};
              return (
                <tr key={r.instrument_id} style={{ cursor: "pointer" }} onClick={() => onSelectInstrument(r.instrument_id)}>
                  <td className="mono">{r.symbol}</td>
                  <td className="mono">{fmtPct(mj["net_return_pct"])}</td>
                  <td className="mono">{fmtPct(mj["max_drawdown_pct"])}</td>
                  <td className="mono">{typeof mj["total_trades"] === "number" ? mj["total_trades"] : "—"}</td>
                  <td className="mono">{fmtPct(mj["win_rate"])}</td>
                  <td className="mono">{fmtNum(mj["profit_factor"], 2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

