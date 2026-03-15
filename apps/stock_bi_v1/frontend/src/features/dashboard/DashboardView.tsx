import { IndustryHeatmapPanel } from "@/features/dashboard/IndustryHeatmapPanel";

import { TerminalChart } from "@/components/charts/TerminalChart";
import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { changeToneClass, formatPercent, formatPrice } from "@/lib/format";
import type { IndustryHeatmapItem, MarketOverview, NorthMoneyItem, TopListItem } from "@/lib/types";


type DashboardViewProps = {
  overview: MarketOverview;
  northFlow: NorthMoneyItem[];
  topList: TopListItem[];
  heatmapRows?: IndustryHeatmapItem[];
};


const rankingRows = (title: string, items: MarketOverview["top_gainers"]) => (
  <TerminalPanel title={title} eyebrow="Market Leaders">
    <div className="space-y-3">
      {items.map((item) => (
        <div key={`${title}-${item.ts_code}`} className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-display text-2xl leading-none text-white">{item.name}</p>
              <p className="mt-1 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">{item.ts_code}</p>
            </div>
            <span className={["text-base font-semibold", changeToneClass(item.pct_chg)].join(" ")}>{formatPercent(item.pct_chg)}</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-sm text-[var(--terminal-muted)]">
            <span>收盘 {formatPrice(item.close)}</span>
            <span>{item.amount ? `成交 ${item.amount.toLocaleString()}` : "热度观察"}</span>
          </div>
        </div>
      ))}
    </div>
  </TerminalPanel>
);


export const DashboardView = ({ overview, northFlow, topList, heatmapRows = [] }: DashboardViewProps) => {
  const distributionEntries = Object.entries(overview.distribution);
  const maxDistribution = Math.max(...distributionEntries.map(([, value]) => value), 1);
  const tierCount = Object.keys(overview.limit_stats.tier_stats).length;
  const brokenRate = `${(overview.limit_stats.broken_rate * 100).toFixed(1)}%`;

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel={overview.trade_date} />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-8">
        <section className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Daily Narrative</p>
            <h2 className="font-display text-7xl leading-[0.92] tracking-[0.04em] text-white">Market Atlas</h2>
            <p className="text-2xl font-medium text-[var(--terminal-accent)]">今日市场导航</p>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              不是模拟终端，而是一张能直接带你进入市场主线的编辑桌面。先看指数与风险，再看行业热区，最后落到个股与异动名单。
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="rounded-[28px] border border-[var(--terminal-line)] bg-[linear-gradient(180deg,rgba(224,174,116,0.18),rgba(255,255,255,0.02))] px-5 py-5">
              <p className="text-[10px] uppercase tracking-[0.32em] text-[var(--terminal-muted)]">Precompute Snapshot</p>
              <p className="mt-3 font-display text-4xl text-white">{overview.trade_date}</p>
            </div>
            <div className="rounded-[28px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-5 py-5">
              <p className="text-[10px] uppercase tracking-[0.32em] text-[var(--terminal-muted)]">Limit Ladder</p>
              <p className="mt-3 font-display text-4xl text-[var(--terminal-accent)]">{tierCount} Tiers Live</p>
            </div>
            <div className="rounded-[28px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-5 py-5">
              <p className="text-[10px] uppercase tracking-[0.32em] text-[var(--terminal-muted)]">Broken Rate</p>
              <p className="mt-3 font-display text-4xl text-white">{brokenRate}</p>
            </div>
          </div>
        </section>

        <MetricStrip
          items={overview.indices.map((item) => ({
            label: item.name,
            value: `${formatPrice(item.close)} ${formatPercent(item.pct_chg)}`,
            tone: item.pct_chg > 0 ? "up" : item.pct_chg < 0 ? "down" : "neutral",
          }))}
        />

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.55fr_0.95fr]">
          <TerminalPanel title="市场温度" eyebrow="Breadth">
            <div className="space-y-4">
              {distributionEntries.map(([label, value]) => (
                <div key={label} className="grid grid-cols-[72px_1fr_auto] items-center gap-3 text-sm">
                  <span className="text-[var(--terminal-muted)]">{label}</span>
                  <div className="h-3 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,var(--terminal-accent),rgba(255,122,102,0.9))]"
                      style={{ width: `${(value / maxDistribution) * 100}%` }}
                    />
                  </div>
                  <span className="text-white">{value}</span>
                </div>
              ))}
            </div>
          </TerminalPanel>

          <IndustryHeatmapPanel rows={heatmapRows} />

          <TerminalPanel title="北向脉冲" eyebrow="Cross Border">
            <div className="space-y-4">
              <TerminalChart
                option={{
                  backgroundColor: "transparent",
                  tooltip: { trigger: "axis" },
                  xAxis: {
                    type: "category",
                    data: northFlow.map((item) => item.trade_date.slice(4)),
                    axisLabel: { color: "#9aa7b8" },
                    axisLine: { lineStyle: { color: "rgba(224,174,116,0.22)" } },
                  },
                  yAxis: {
                    type: "value",
                    axisLabel: { color: "#9aa7b8" },
                    splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
                  },
                  series: [
                    {
                      type: "line",
                      smooth: true,
                      data: northFlow.map((item) => item.north_money),
                      lineStyle: { color: "#e0ae74", width: 3 },
                      areaStyle: { color: "rgba(224,174,116,0.18)" },
                    },
                  ],
                }}
                height={360}
              />
              <div className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">Latest North Flow</p>
                <p className="mt-2 font-display text-4xl text-white">{northFlow.at(-1)?.north_money ?? 0}</p>
              </div>
            </div>
          </TerminalPanel>
        </section>

        <section className="grid gap-6 xl:grid-cols-4">
          {rankingRows("领涨席位", overview.top_gainers)}
          {rankingRows("承压名单", overview.top_losers)}
          <TerminalPanel title="异动雷达" eyebrow="Top List">
            <div className="space-y-3">
              {topList.map((item) => (
                <div key={item.ts_code} className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-display text-2xl text-white">{item.name}</p>
                      <p className="mt-1 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">{item.ts_code}</p>
                    </div>
                    <span className={["text-sm font-semibold", changeToneClass(item.pct_chg)].join(" ")}>{formatPercent(item.pct_chg)}</span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[var(--terminal-muted)]">{item.reason}</p>
                </div>
              ))}
            </div>
          </TerminalPanel>
          <TerminalPanel title="涨停梯队" eyebrow="Limit Up">
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                  <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--terminal-muted)]">涨停</p>
                  <p className="mt-2 font-display text-4xl text-[var(--terminal-up)]">{overview.limit_stats.up_count}</p>
                </div>
                <div className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                  <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--terminal-muted)]">炸板</p>
                  <p className="mt-2 font-display text-4xl text-[var(--terminal-accent)]">{overview.limit_stats.broken_count}</p>
                </div>
              </div>
              <div className="space-y-2">
                {Object.entries(overview.limit_stats.tier_stats).map(([tier, count]) => (
                  <div key={tier} className="flex items-center justify-between rounded-full border border-[var(--terminal-line)] px-4 py-3 text-sm">
                    <span className="text-[var(--terminal-muted)]">{tier} 连板</span>
                    <span className="text-white">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </TerminalPanel>
        </section>
      </main>
    </div>
  );
};
