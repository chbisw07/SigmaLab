import React, { useMemo } from "react";
import { fmtNum, fmtPct } from "../app/ui/format";

function pick(metrics: Record<string, unknown>) {
  const m = metrics ?? {};
  return {
    net_return_pct: m["net_return_pct"],
    max_drawdown_pct: m["max_drawdown_pct"],
    profit_factor: m["profit_factor"],
    win_rate: m["win_rate"],
    total_trades: m["total_trades"],
    expectancy_pct: m["expectancy_pct"],
    avg_win_pct: m["avg_win_pct"],
    avg_loss_pct: m["avg_loss_pct"],
    end_equity: m["end_equity"]
  };
}

export default function MetricCards({ metrics }: { metrics: Record<string, unknown> }) {
  const v = useMemo(() => pick(metrics), [metrics]);

  return (
    <div className="kpi-grid">
      <div className="kpi">
        <div className="kpi-label">Net return</div>
        <div className="kpi-value">{fmtPct(v.net_return_pct)}</div>
      </div>
      <div className="kpi">
        <div className="kpi-label">Max drawdown</div>
        <div className="kpi-value">{fmtPct(v.max_drawdown_pct)}</div>
      </div>
      <div className="kpi">
        <div className="kpi-label">Profit factor</div>
        <div className="kpi-value">{fmtNum(v.profit_factor, 2)}</div>
      </div>
      <div className="kpi">
        <div className="kpi-label">Win rate</div>
        <div className="kpi-value">{fmtPct(v.win_rate)}</div>
      </div>
      <div className="kpi">
        <div className="kpi-label">Trades</div>
        <div className="kpi-value">{typeof v.total_trades === "number" ? v.total_trades : "—"}</div>
      </div>
      <div className="kpi">
        <div className="kpi-label">Expectancy</div>
        <div className="kpi-value">{fmtPct(v.expectancy_pct)}</div>
      </div>
    </div>
  );
}

