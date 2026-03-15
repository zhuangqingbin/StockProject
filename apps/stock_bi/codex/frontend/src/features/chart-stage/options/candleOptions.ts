import type { EChartsOption } from "echarts";

export const buildStockCandleOption = (
  labels: string[],
  rows: Array<{ open: number; high: number; low: number; close: number }>,
): EChartsOption => ({
  backgroundColor: "transparent",
  grid: { left: 40, right: 16, top: 28, bottom: 32 },
  xAxis: {
    type: "category",
    data: labels,
    axisLine: { lineStyle: { color: "rgba(255,255,255,0.16)" } },
    axisLabel: { color: "rgba(245,243,239,0.72)" },
  },
  yAxis: {
    scale: true,
    axisLabel: { color: "rgba(245,243,239,0.72)" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
  },
  tooltip: { trigger: "axis" },
  series: [
    {
      type: "candlestick",
      data: rows.map((row) => [row.open, row.close, row.low, row.high]),
      itemStyle: {
        color: "#f05b52",
        color0: "#2f6da5",
        borderColor: "#f05b52",
        borderColor0: "#2f6da5",
      },
    },
  ],
});
