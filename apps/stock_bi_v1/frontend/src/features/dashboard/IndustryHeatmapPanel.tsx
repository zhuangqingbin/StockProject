"use client";

import { useRouter } from "next/navigation";

import { TerminalChart } from "@/components/charts/TerminalChart";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { changeToneClass, formatAmount, formatPercent } from "@/lib/format";
import type { IndustryHeatmapItem } from "@/lib/types";


type IndustryHeatmapPanelProps = {
  rows: IndustryHeatmapItem[];
};

type ChartParamLike = {
  name?: string | number;
};


const toneColor = (value: number) => {
  if (value > 0) {
    return "#ff7a66";
  }
  if (value < 0) {
    return "#6fd0b3";
  }
  return "#e0ae74";
};

const chartParamName = (params: unknown) => {
  const candidate = Array.isArray(params) ? params[0] : params;
  if (!candidate || typeof candidate !== "object") {
    return "";
  }
  const name = (candidate as ChartParamLike).name;
  return typeof name === "string" || typeof name === "number" ? String(name) : "";
};


export const IndustryHeatmapPanel = ({ rows }: IndustryHeatmapPanelProps) => {
  const router = useRouter();
  const rankedRows = [...rows]
    .sort((left, right) => Math.abs(right.total_amount) - Math.abs(left.total_amount))
    .slice(0, 8);

  const goToIndustry = (industry: string) => {
    router.push(`/industry?name=${encodeURIComponent(industry)}`);
  };

  return (
    <TerminalPanel title="行业热区" eyebrow="Sector Map" actionLabel="点击色块进入行业股票页">
      <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <TerminalChart
            option={{
              backgroundColor: "transparent",
              tooltip: {
                trigger: "item",
                formatter: (params) => {
                  const name = chartParamName(params);
                  const row = rows.find((item) => item.industry === name);
                  if (!row) {
                    return name;
                  }
                  return [
                    `<strong>${row.industry}</strong>`,
                    `平均涨幅 ${formatPercent(row.avg_pct_chg)}`,
                    `成交额 ${formatAmount(row.total_amount)}`,
                    `上涨 ${row.up_count} / 下跌 ${row.down_count}`,
                  ].join("<br/>");
                },
              },
              series: [
                {
                  type: "treemap",
                  roam: false,
                  nodeClick: false,
                  breadcrumb: { show: false },
                  label: {
                    show: true,
                    formatter: ({ name, data }) => {
                      const pct = Number((data as { pct?: number } | undefined)?.pct ?? 0);
                      return `${name}\n${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
                    },
                    color: "#f7f1e8",
                    fontSize: 14,
                    lineHeight: 18,
                  },
                  upperLabel: { show: false },
                  itemStyle: {
                    borderColor: "rgba(255,255,255,0.08)",
                    borderWidth: 2,
                    gapWidth: 2,
                    borderRadius: 18,
                  },
                  levels: [
                    {
                      itemStyle: {
                        borderColor: "rgba(255,255,255,0.08)",
                        borderWidth: 2,
                        gapWidth: 2,
                        borderRadius: 18,
                      },
                    },
                  ],
                  data: rows.map((item) => ({
                    name: item.industry,
                    value: Math.max(Math.abs(item.total_amount), item.stock_count * 1000000, 1),
                    pct: item.avg_pct_chg,
                    itemStyle: {
                      color: toneColor(item.avg_pct_chg),
                    },
                  })),
                },
              ],
            }}
            height={360}
            onChartClick={(params) => {
              if (typeof params?.name === "string") {
                goToIndustry(params.name);
              }
            }}
          />
          <p className="text-sm leading-6 text-[var(--terminal-muted)]">
            热力图按行业成交额和涨跌幅共同编码。点击任意色块可直接查看该行业当日股票列表、估值与资金情况。
          </p>
        </div>

        <div className="grid gap-3">
          {rankedRows.map((row) => (
            <button
              key={row.industry}
              type="button"
              className="group rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:border-[rgba(224,174,116,0.65)] hover:bg-[rgba(224,174,116,0.08)]"
              onClick={() => goToIndustry(row.industry)}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-display text-2xl tracking-[0.08em] text-white">{row.industry}</p>
                  <p className="mt-1 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
                    {row.stock_count} Stocks
                  </p>
                </div>
                <span className={["text-sm font-semibold", changeToneClass(row.avg_pct_chg)].join(" ")}>{formatPercent(row.avg_pct_chg)}</span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">成交额</p>
                  <p className="mt-1 text-white">{formatAmount(row.total_amount)}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">主力净流</p>
                  <p className={["mt-1", changeToneClass(row.net_mf_amount)].join(" ")}>{formatAmount(row.net_mf_amount)}</p>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-[var(--terminal-muted)]">
                <span>上涨 {row.up_count}</span>
                <span>下跌 {row.down_count}</span>
                <span className="text-[var(--terminal-accent)] transition group-hover:translate-x-0.5">查看股票 →</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </TerminalPanel>
  );
};
