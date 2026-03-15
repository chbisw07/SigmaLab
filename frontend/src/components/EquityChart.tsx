import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";

export default function EquityChart({ points }: { points: Array<{ timestamp: string; equity: number }> }) {
  const opt = useMemo(() => {
    const x = points.map((p) => p.timestamp);
    const y = points.map((p) => p.equity);
    return {
      backgroundColor: "transparent",
      grid: { left: 40, right: 18, top: 20, bottom: 30 },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        data: x,
        axisLabel: { color: "rgba(255,255,255,0.65)" },
        axisLine: { lineStyle: { color: "rgba(255,255,255,0.16)" } }
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "rgba(255,255,255,0.65)" },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.10)" } }
      },
      series: [
        {
          name: "Equity",
          type: "line",
          data: y,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2, color: "#2dd4bf" },
          areaStyle: { color: "rgba(45,212,191,0.10)" }
        }
      ]
    };
  }, [points]);

  return <ReactECharts option={opt} style={{ height: 320, width: "100%" }} />;
}

