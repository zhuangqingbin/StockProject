import type { EChartsOption } from "echarts";

import type { IndustryRankingItem, RankingItem, SortDirection } from "../../../lib/api/types";

const paletteForChange = (value: number) => {
  if (value >= 3) {
    return "#f05b52";
  }
  if (value >= 1) {
    return "#ff8a5b";
  }
  if (value >= 0) {
    return "#f6c28b";
  }
  if (value <= -3) {
    return "#2667a8";
  }
  if (value <= -1) {
    return "#4a86c5";
  }
  return "#6e8fb7";
};

export const buildIndustryTreemapOption = (
  data: IndustryRankingItem[],
  topN: number,
): EChartsOption => ({
  backgroundColor: "transparent",
  tooltip: {
    formatter: (params: any) => {
      const item = params.data as IndustryRankingItem | undefined;
      if (!item) {
        return "";
      }
      return `${item.name}<br/>当日涨跌: ${item.pct_chg.toFixed(2)}%<br/>近五日力度: ${(item.avg5_pct_chg ?? item.pct_chg).toFixed(2)}%<br/>成交额: ${item.total_amount.toFixed(0)} 亿`;
    },
  } as any,
  series: [
    {
      type: "treemap",
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: (params: any) => {
          const item = params.data as IndustryRankingItem | undefined;
          return item ? `${item.name}\n${item.pct_chg.toFixed(2)}%` : "";
        },
        color: "#fff7ef",
        fontSize: 13,
        lineHeight: 18,
      },
      upperLabel: { show: false },
      data: data.slice(0, topN).map((item) => ({
        ...item,
        name: item.name,
        value: Math.max(Math.abs(item.avg5_pct_chg ?? item.pct_chg), 0.8),
        itemStyle: {
          color: paletteForChange(item.pct_chg),
          borderColor: "rgba(255,255,255,0.16)",
          gapWidth: 3,
          borderWidth: 1,
        },
      })),
    },
  ] as any,
});

export const buildRankingTreemapOption = (
  data: RankingItem[],
  order: SortDirection,
  topN: number,
): EChartsOption => ({
  backgroundColor: "transparent",
  tooltip: {
    formatter: (params: any) => {
      const item = params.data as RankingItem | undefined;
      if (!item) {
        return "";
      }
      return `${item.name ?? item.ts_code}<br/>代码: ${item.ts_code}<br/>涨跌幅: ${item.pct_chg.toFixed(2)}%<br/>成交额: ${(item.amount ?? 0).toFixed(0)} 万`;
    },
  } as any,
  series: [
    {
      type: "treemap",
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: (params: any) => {
          const item = params.data as RankingItem | undefined;
          return item ? `${item.name ?? item.ts_code}\n${item.pct_chg.toFixed(2)}%` : "";
        },
        color: "#fff7ef",
        fontSize: 13,
        lineHeight: 18,
      },
      upperLabel: { show: false },
      data: data.slice(0, topN).map((item) => ({
        ...item,
        name: item.name ?? item.ts_code,
        value: Math.max(Math.abs(item.pct_chg), 0.8),
        itemStyle: {
          color: paletteForChange(order === "desc" ? item.pct_chg : -Math.abs(item.pct_chg)),
          borderColor: "rgba(255,255,255,0.16)",
          gapWidth: 3,
          borderWidth: 1,
        },
      })),
    },
  ] as any,
});
