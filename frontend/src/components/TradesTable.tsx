import React, { useDeferredValue, useMemo, useState } from "react";
import type { BacktestTrade } from "../app/api/types";
import { fmtDateTimeIso, fmtDurationSec, fmtNum, fmtPct } from "../app/ui/format";

type SortKey = "entry_ts" | "symbol" | "pnl_pct";

export default function TradesTable({
  trades,
  onSelectTrade
}: {
  trades: BacktestTrade[];
  onSelectTrade: (t: BacktestTrade) => void;
}) {
  const [q, setQ] = useState("");
  const qd = useDeferredValue(q);
  const [sortKey, setSortKey] = useState<SortKey>("entry_ts");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const filtered = useMemo(() => {
    const qq = qd.trim().toUpperCase();
    if (!qq) return trades;
    return trades.filter((t) => t.symbol.toUpperCase().includes(qq));
  }, [qd, trades]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortKey === "symbol") return dir * a.symbol.localeCompare(b.symbol);
      if (sortKey === "entry_ts") return dir * a.entry_ts.localeCompare(b.entry_ts);
      const ap = a.pnl_pct ?? 0;
      const bp = b.pnl_pct ?? 0;
      return dir * (ap - bp);
    });
    return arr;
  }, [filtered, sortDir, sortKey]);

  function setSort(next: SortKey) {
    if (sortKey === next) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(next);
      setSortDir(next === "pnl_pct" ? "desc" : "asc");
    }
  }

  return (
    <div>
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <div style={{ fontWeight: 650 }}>Trades</div>
          <div className="subtle">Click a row to open its symbol context in Charts.</div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input className="input" style={{ width: 260 }} placeholder="Filter by symbol…" value={q} onChange={(e) => setQ(e.target.value)} />
          <span className="subtle mono">{sorted.length}</span>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="subtle">No trades for this run.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th style={{ cursor: "pointer" }} onClick={() => setSort("symbol")}>
                Symbol
              </th>
              <th style={{ cursor: "pointer" }} onClick={() => setSort("entry_ts")}>
                Entry
              </th>
              <th>Entry px</th>
              <th>Exit</th>
              <th>Exit px</th>
              <th style={{ cursor: "pointer" }} onClick={() => setSort("pnl_pct")}>
                PnL
              </th>
              <th>PnL %</th>
              <th>Hold</th>
              <th>Entry reason</th>
              <th>Exit reason</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((t) => {
              const pnl = t.pnl ?? 0;
              const pnlCls = pnl >= 0 ? "pill ok" : "pill bad";
              const exitReason = t.close_reason ?? t.exit_reason ?? "—";
              return (
                <tr key={t.id} style={{ cursor: "pointer" }} onClick={() => onSelectTrade(t)}>
                  <td className="mono">{t.symbol}</td>
                  <td>{fmtDateTimeIso(t.entry_ts)}</td>
                  <td className="mono">{fmtNum(t.entry_price, 2)}</td>
                  <td>{fmtDateTimeIso(t.exit_ts)}</td>
                  <td className="mono">{fmtNum(t.exit_price, 2)}</td>
                  <td>
                    <span className={pnlCls}>{fmtNum(t.pnl, 2)}</span>
                  </td>
                  <td className="mono">{fmtPct(t.pnl_pct, 2)}</td>
                  <td>{fmtDurationSec(t.holding_period_sec)}</td>
                  <td className="mono">{t.entry_reason ?? "—"}</td>
                  <td className="mono">{exitReason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

