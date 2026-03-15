import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";

export default function DrawdownChart({ points }: { points: Array<{ timestamp: string; drawdown: number }> }) {
  const opt = useMemo(() => {
    const x = points.map((p) => p.timestamp);
    const y = points.map((p) => p.drawdown);
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
        axisLabel: {
          color: "rgba(255,255,255,0.65)",
          formatter: (v: number) => `${(v * 100).toFixed(1)}%`
        },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.10)" } }
      },
      series: [
        {
          name: "Drawdown",
          type: "line",
          data: y,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2, color: "#fb7185" },
          areaStyle: { color: "rgba(251,113,133,0.10)" }
        }
      ]
    };
  }, [points]);

  return <ReactECharts option={opt} style={{ height: 260, width: "100%" }} />;
}

