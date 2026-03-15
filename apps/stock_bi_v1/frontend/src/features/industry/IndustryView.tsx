import Link from "next/link";

import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { changeToneClass, formatAmount, formatPercent } from "@/lib/format";
import type { IndustryDetail, ScreenerResultItem } from "@/lib/types";


export const IndustryView = ({ detail, stocks }: { detail: IndustryDetail; stocks: ScreenerResultItem[] }) => {
  const topMovers = [...stocks].sort((left, right) => right.pct_chg - left.pct_chg).slice(0, 4);

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel={detail.trade_date} />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-8">
        <section className="grid gap-6 xl:grid-cols-[1.25fr_0.85fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Industry Drilldown</p>
            <h2 className="font-display text-6xl leading-none tracking-[0.06em] text-white">{detail.industry}</h2>
            <p className="max-w-2xl text-base leading-7 text-[var(--terminal-muted)]">
              查看该行业当日股票表现、估值与资金流。行业卡片来自首页热区，当前页保留继续钻取到单只股票的路径。
            </p>
          </div>

          <div className="terminal-panel">
            <p className="text-[10px] uppercase tracking-[0.32em] text-[var(--terminal-muted)]">行业快照</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">股票数</p>
                <p className="mt-2 font-display text-4xl text-white">{detail.stock_count}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">成交额</p>
                <p className="mt-2 font-display text-4xl text-white">{formatAmount(detail.total_amount)}</p>
              </div>
            </div>
          </div>
        </section>

        <MetricStrip
          items={[
            { label: "平均涨幅", value: formatPercent(detail.avg_pct_chg), tone: detail.avg_pct_chg >= 0 ? "up" : "down" },
            { label: "上涨家数", value: String(detail.up_count), tone: "up" },
            { label: "下跌家数", value: String(detail.down_count), tone: "down" },
            { label: "主力净流入", value: formatAmount(detail.net_mf_amount), tone: detail.net_mf_amount >= 0 ? "up" : "down" },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[1.55fr_0.95fr]">
          <TerminalPanel title="行业股票" eyebrow="Constituents" actionLabel="点击股票进入个股页">
            <div className="grid grid-cols-[1.3fr_0.7fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-[var(--terminal-line)] pb-3 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
              <span>股票</span>
              <span>涨跌幅</span>
              <span>PE</span>
              <span>市值</span>
              <span>净流入</span>
            </div>
            <div className="space-y-3 pt-3 text-sm">
              {stocks.map((item) => (
                <div key={item.ts_code} className="grid grid-cols-[1.3fr_0.7fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-[var(--terminal-line)] pb-3 last:border-b-0 last:pb-0">
                  <div>
                    <Link href={`/stock/${item.ts_code}`} className="font-display text-2xl leading-none tracking-[0.06em] text-white transition hover:text-[var(--terminal-accent)]">
                      {item.name}
                    </Link>
                    <p className="mt-1 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">
                      {item.ts_code} / {item.market}
                    </p>
                  </div>
                  <span className={changeToneClass(item.pct_chg)}>{formatPercent(item.pct_chg)}</span>
                  <span className="text-white">{item.pe_ttm.toFixed(2)}</span>
                  <span className="text-white">{formatAmount(item.total_mv)}</span>
                  <span className={changeToneClass(item.net_mf_amount)}>{formatAmount(item.net_mf_amount)}</span>
                </div>
              ))}
            </div>
          </TerminalPanel>

          <div className="space-y-6">
            <TerminalPanel title="领涨切片" eyebrow="Top Movers">
              <div className="space-y-3">
                {topMovers.map((item) => (
                  <div key={item.ts_code} className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-display text-2xl text-white">{item.name}</span>
                      <span className={changeToneClass(item.pct_chg)}>{formatPercent(item.pct_chg)}</span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm text-[var(--terminal-muted)]">
                      <span>{item.ts_code}</span>
                      <span>净流入 {formatAmount(item.net_mf_amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </TerminalPanel>

            <TerminalPanel title="行业结构" eyebrow="Breadth">
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--terminal-muted)]">上涨占比</span>
                  <span className="text-white">{detail.stock_count > 0 ? `${((detail.up_count / detail.stock_count) * 100).toFixed(1)}%` : "0.0%"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--terminal-muted)]">下跌占比</span>
                  <span className="text-white">{detail.stock_count > 0 ? `${((detail.down_count / detail.stock_count) * 100).toFixed(1)}%` : "0.0%"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--terminal-muted)]">主力方向</span>
                  <span className={changeToneClass(detail.net_mf_amount)}>{detail.net_mf_amount >= 0 ? "净流入" : "净流出"}</span>
                </div>
              </div>
            </TerminalPanel>
          </div>
        </section>
      </main>
    </div>
  );
};
