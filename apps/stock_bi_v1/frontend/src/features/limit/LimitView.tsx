import Link from "next/link";

import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { formatPercent } from "@/lib/format";


export const LimitView = ({
  limitStats,
  limitList,
}: {
  limitStats: { up_count: number; down_count: number; broken_count: number; broken_rate: number; tier_stats: Record<string, number> };
  limitList: Array<{ ts_code: string; name: string }>;
}) => {
  const tierRows = Object.entries(limitStats.tier_stats).sort((left, right) => Number(right[0]) - Number(left[0]));

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel="LIMIT UP" />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-6">
        <section className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Momentum Stack</p>
            <h2 className="font-display text-6xl leading-[0.94] tracking-[0.04em] text-white">Limit Ladder</h2>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              聚焦涨停梯队、炸板率与当日领涨名单，快速识别市场高度、情绪强弱和是否存在接力断层。
            </p>
          </div>

          <div className="rounded-[28px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.04)] p-6 shadow-[0_22px_48px_rgba(0,0,0,0.18)]">
            <p className="text-[10px] uppercase tracking-[0.36em] text-[var(--terminal-muted)]">Session Pulse</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">最高连板</p>
                <p className="mt-2 font-display text-4xl text-white">{tierRows[0]?.[0] ?? "0"}</p>
              </div>
              <div className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">炸板率</p>
                <p className="mt-2 font-display text-4xl text-white">{formatPercent(limitStats.broken_rate * 100)}</p>
              </div>
            </div>
          </div>
        </section>

        <MetricStrip
          items={[
            { label: "涨停家数", value: String(limitStats.up_count), tone: "up" },
            { label: "跌停家数", value: String(limitStats.down_count), tone: "down" },
            { label: "炸板数", value: String(limitStats.broken_count), tone: limitStats.broken_count > 0 ? "down" : undefined },
            { label: "炸板率", value: formatPercent(limitStats.broken_rate * 100), tone: limitStats.broken_rate > 0 ? "down" : undefined },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[1fr_1.25fr]">
          <TerminalPanel title="连板梯队" eyebrow="Tier Map">
            <div className="grid gap-3">
              {tierRows.map(([tier, count]) => (
                <div key={tier} className="rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-display text-3xl tracking-[0.08em] text-white">{tier} 连板</span>
                    <span className="text-xl text-[var(--terminal-accent)]">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </TerminalPanel>

          <TerminalPanel title="涨停名单" eyebrow="Leaders" actionLabel="点击股票进入个股页">
            <div className="space-y-3">
              {limitList.map((row) => (
                <div key={row.ts_code} className="flex items-center justify-between gap-4 rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-5 py-4">
                  <div>
                    <Link href={`/stock/${row.ts_code}`} className="font-display text-2xl tracking-[0.08em] text-white transition hover:text-[var(--terminal-accent)]">
                      {row.name}
                    </Link>
                    <p className="mt-1 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">{row.ts_code}</p>
                  </div>
                  <span className="text-[var(--terminal-accent)]">查看个股</span>
                </div>
              ))}
            </div>
          </TerminalPanel>
        </section>
      </main>
    </div>
  );
};
