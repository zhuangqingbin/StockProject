import Link from "next/link";

import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { changeToneClass, formatAmount, formatPercent, formatPrice } from "@/lib/format";
import type { TopListItem } from "@/lib/types";


export const ToplistView = ({ rows }: { rows: TopListItem[] }) => {
  const strongest = rows.reduce<TopListItem | null>((current, item) => {
    if (!current || item.pct_chg > current.pct_chg) {
      return item;
    }
    return current;
  }, null);
  const risingCount = rows.filter((row) => row.pct_chg > 0).length;

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel={rows[0]?.trade_date ?? "TOP LIST"} />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-6">
        <section className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Signal Desk</p>
            <h2 className="font-display text-6xl leading-[0.94] tracking-[0.04em] text-white">Toplist Ledger</h2>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              汇总当日龙虎榜异动席位，把高弹性个股、上榜原因和成交额放在一个视图里，便于快速判断情绪驱动还是资金驱动。
            </p>
          </div>

          <div className="rounded-[28px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.04)] p-6 shadow-[0_22px_48px_rgba(0,0,0,0.18)]">
            <p className="text-[10px] uppercase tracking-[0.36em] text-[var(--terminal-muted)]">Strongest Ticket</p>
            <p className="mt-4 font-display text-4xl tracking-[0.05em] text-white">{strongest?.name ?? "暂无"}</p>
            <p className={["mt-3 text-xl font-semibold", changeToneClass(strongest?.pct_chg ?? 0)].join(" ")}>{formatPercent(strongest?.pct_chg ?? 0)}</p>
            <p className="mt-4 text-sm leading-6 text-[var(--terminal-muted)]">{strongest?.reason ?? "暂无上榜原因说明。"}</p>
          </div>
        </section>

        <MetricStrip
          items={[
            { label: "上榜家数", value: String(rows.length) },
            { label: "上涨占比", value: rows.length ? `${Math.round((risingCount / rows.length) * 100)}%` : "0%" },
            { label: "最强涨幅", value: formatPercent(strongest?.pct_chg ?? 0), tone: (strongest?.pct_chg ?? 0) >= 0 ? "up" : "down" },
            { label: "最新日期", value: rows[0]?.trade_date ?? "--" },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
          <TerminalPanel title="异动席位" eyebrow="Signal Feed" actionLabel={`${rows.length} Events`}>
            <div className="space-y-3">
              {rows.map((row) => (
                <div key={`${row.ts_code}-${row.trade_date}`} className="rounded-[24px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-5 py-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <Link href={`/stock/${row.ts_code}`} className="font-display text-3xl tracking-[0.06em] text-white transition hover:text-[var(--terminal-accent)]">
                        {row.name}
                      </Link>
                      <p className="mt-2 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">
                        {row.ts_code} / {row.trade_date}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={["text-lg font-semibold", changeToneClass(row.pct_chg)].join(" ")}>{formatPercent(row.pct_chg)}</p>
                      <p className="mt-2 text-sm text-[var(--terminal-muted)]">{formatPrice(row.close)}</p>
                    </div>
                  </div>
                  <p className="mt-4 text-sm leading-6 text-[var(--terminal-muted)]">{row.reason ?? "无上榜原因说明"}</p>
                  <div className="mt-4 flex flex-wrap gap-4 text-xs uppercase tracking-[0.24em] text-[var(--terminal-muted)]">
                    {row.amount ? <span>成交额 {formatAmount(row.amount)}</span> : null}
                    {row.net_amount ? <span>净额 {formatAmount(row.net_amount)}</span> : null}
                    {row.turnover_rate ? <span>换手 {row.turnover_rate.toFixed(2)}%</span> : null}
                  </div>
                </div>
              ))}
            </div>
          </TerminalPanel>

          <TerminalPanel title="信号拆解" eyebrow="Reading Notes">
            <div className="space-y-3 text-sm">
              <div className="rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">最强表现</p>
                <p className="mt-2 font-display text-2xl text-white">{strongest?.name ?? "暂无"}</p>
                <p className={["mt-2", changeToneClass(strongest?.pct_chg ?? 0)].join(" ")}>{formatPercent(strongest?.pct_chg ?? 0)}</p>
              </div>
              <div className="rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">情绪倾向</p>
                <p className="mt-2 text-white">{risingCount >= Math.ceil(rows.length / 2) ? "偏强" : "偏弱"}</p>
              </div>
            </div>
          </TerminalPanel>
        </section>
      </main>
    </div>
  );
};
