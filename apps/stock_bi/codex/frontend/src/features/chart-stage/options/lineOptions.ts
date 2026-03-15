import type { EChartsOption } from "echarts";

export const buildLineSeriesOption = (
  labels: string[],
  values: number[],
  color: string,
  areaColor?: string,
): EChartsOption => ({
  backgroundColor: "transparent",
  grid: { left: 34, right: 16, top: 24, bottom: 30 },
  xAxis: {
    type: "category",
    data: labels,
    boundaryGap: false,
    axisLabel: { color: "rgba(245,243,239,0.7)" },
    axisLine: { lineStyle: { color: "rgba(255,255,255,0.16)" } },
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "rgba(245,243,239,0.7)" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
  },
  tooltip: { trigger: "axis" },
  series: [
    {
      type: "line",
      smooth: true,
      symbol: "none",
      lineStyle: { color, width: 2 },
      areaStyle: areaColor ? { color: areaColor } : undefined,
      data: values,
    },
  ],
});
