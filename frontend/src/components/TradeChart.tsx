import React, { useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import { api } from "../app/api/client";
import type { BacktestChartResponse, ChartMarker, UUID } from "../app/api/types";

function markerSeries(markers: ChartMarker[], kind: "entry" | "exit") {
  const pts = markers
    .filter((m) => m.type === kind)
    .map((m) => ({
      name: kind,
      value: m.price,
      trade_id: m.trade_id,
      close_reason: m.close_reason ?? null,
      label_text: m.label ?? null,
      coord: [m.timestamp, m.price]
    }));

  const color = kind === "entry" ? "#34d399" : "#fb7185";
  const rotate = kind === "entry" ? 0 : 180;
  return {
    name: kind === "entry" ? "Entry" : "Exit",
    type: "scatter",
    data: pts,
    symbol: "triangle",
    symbolRotate: rotate,
    symbolSize: 12,
    itemStyle: { color },
    emphasis: { scale: 1.2 }
  };
}

export default function TradeChart({
  runId,
  instrumentId,
  selectedTradeId
}: {
  runId: UUID;
  instrumentId: UUID;
  selectedTradeId: UUID | null;
}) {
  const [data, setData] = useState<BacktestChartResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    setData(null);
    (async () => {
      try {
        const d = await api.getChart(runId, instrumentId);
        setData(d);
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [runId, instrumentId]);

  const option = useMemo(() => {
    if (!data) return null;
    const candles = data.candles ?? [];
    const x = candles.map((c) => c.timestamp);
    const ohlc = candles.map((c) => [c.open, c.close, c.low, c.high]);
    const vol = candles.map((c) => c.volume ?? 0);

    const overlaySeries = Object.entries(data.overlays ?? {}).map(([name, pts]) => ({
      name,
      type: "line",
      data: pts.map((p) => (p.value == null ? null : p.value)),
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 1.6 },
      emphasis: { focus: "series" }
    }));

    // Focus window around the selected trade if present.
    let dzStart = 0;
    let dzEnd = 100;
    if (selectedTradeId) {
      const tMarkers = (data.markers ?? []).filter((m) => m.trade_id === selectedTradeId);
      const entry = tMarkers.find((m) => m.type === "entry")?.timestamp ?? null;
      const exit = tMarkers.find((m) => m.type === "exit")?.timestamp ?? null;
      const idx0 = entry ? x.findIndex((ts) => ts === entry) : -1;
      const idx1 = exit ? x.findIndex((ts) => ts === exit) : -1;
      const a = idx0 >= 0 ? idx0 : idx1;
      const b = idx1 >= 0 ? idx1 : idx0;
      if (a >= 0) {
        const lo = Math.max(0, a - 20);
        const hi = Math.min(x.length - 1, (b >= 0 ? b : a) + 20);
        dzStart = (lo / Math.max(1, x.length - 1)) * 100;
        dzEnd = (hi / Math.max(1, x.length - 1)) * 100;
      }
    }

    return {
      backgroundColor: "transparent",
      legend: {
        textStyle: { color: "rgba(255,255,255,0.70)" },
        top: 6
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        backgroundColor: "rgba(15, 23, 32, 0.92)",
        borderColor: "rgba(255,255,255,0.16)",
        textStyle: { color: "rgba(255,255,255,0.88)" },
        formatter: (params: any) => {
          const ts = params?.[0]?.axisValue ?? "";
          const mks = (data.markers ?? []).filter((m) => m.timestamp === ts);
          const mkLines = mks
            .map((m) => {
              const extra = m.type === "exit" && m.close_reason ? ` (${m.close_reason})` : "";
              return `${m.type.toUpperCase()}: ${m.price}${extra}`;
            })
            .join("<br/>");
          return `${ts}${mkLines ? "<br/><br/>" + mkLines : ""}`;
        }
      },
      grid: [
        { left: 48, right: 18, top: 48, height: 320 },
        { left: 48, right: 18, top: 390, height: 90 }
      ],
      xAxis: [
        {
          type: "category",
          data: x,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: "rgba(255,255,255,0.18)" } },
          axisLabel: { color: "rgba(255,255,255,0.62)" }
        },
        {
          type: "category",
          gridIndex: 1,
          data: x,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: "rgba(255,255,255,0.18)" } },
          axisLabel: { show: false }
        }
      ],
      yAxis: [
        {
          scale: true,
          splitLine: { lineStyle: { color: "rgba(255,255,255,0.10)" } },
          axisLabel: { color: "rgba(255,255,255,0.62)" }
        },
        {
          scale: true,
          gridIndex: 1,
          splitLine: { show: false },
          axisLabel: { color: "rgba(255,255,255,0.62)" }
        }
      ],
      dataZoom: [
        { type: "inside", xAxisIndex: [0, 1], start: dzStart, end: dzEnd },
        {
          type: "slider",
          xAxisIndex: [0, 1],
          start: dzStart,
          end: dzEnd,
          height: 18,
          bottom: 8,
          borderColor: "rgba(255,255,255,0.18)",
          fillerColor: "rgba(56,189,248,0.10)",
          handleStyle: { color: "rgba(255,255,255,0.28)" },
          textStyle: { color: "rgba(255,255,255,0.55)" }
        }
      ],
      series: [
        {
          name: "Price",
          type: "candlestick",
          data: ohlc,
          itemStyle: {
            color: "#34d399",
            color0: "#fb7185",
            borderColor: "#34d399",
            borderColor0: "#fb7185"
          }
        },
        ...overlaySeries,
        markerSeries(data.markers ?? [], "entry"),
        markerSeries(data.markers ?? [], "exit"),
        {
          name: "Volume",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: vol,
          itemStyle: { color: "rgba(255,255,255,0.14)" }
        }
      ]
    };
  }, [data, selectedTradeId]);

  if (err) {
    return (
      <div>
        <div style={{ color: "rgba(251,113,133,0.95)", fontWeight: 600 }}>Failed to load chart data</div>
        <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.72)" }}>
          {err}
        </pre>
        <div className="subtle">
          Tip: if candles are missing from PostgreSQL, SigmaLab may try to backfill via Kite. Ensure Kite creds are set if
          you expect auto-backfill.
        </div>
      </div>
    );
  }

  if (!option) return <div className="subtle">Loading chart…</div>;

  return <ReactECharts option={option} style={{ height: 520, width: "100%" }} notMerge={true} />;
}

