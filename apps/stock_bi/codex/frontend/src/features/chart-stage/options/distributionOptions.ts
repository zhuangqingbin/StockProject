import type { EChartsOption } from "echarts";

import type { DistributionBucket } from "../../../lib/api/types";

export const buildDistributionOption = (data: DistributionBucket[]): EChartsOption => ({
  backgroundColor: "transparent",
  grid: { left: 40, right: 16, top: 40, bottom: 48 },
  xAxis: {
    type: "category",
    data: data.map((item) => `${item.range_start}% ~ ${item.range_end}%`),
    axisLine: { lineStyle: { color: "rgba(255,255,255,0.18)" } },
    axisLabel: { color: "rgba(245,243,239,0.72)", rotate: 22 },
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "rgba(245,243,239,0.72)" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
  },
  tooltip: {
    trigger: "axis",
    valueFormatter: (value) => `${value ?? 0} 只`,
  },
  series: [
    {
      type: "bar",
      barMaxWidth: 42,
      data: data.map((item) => ({
        value: item.count,
        itemStyle: {
          color: item.range_start >= 0 ? "#f05b52" : "#2f6da5",
          borderRadius: [10, 10, 0, 0],
        },
      })),
    },
  ],
});
