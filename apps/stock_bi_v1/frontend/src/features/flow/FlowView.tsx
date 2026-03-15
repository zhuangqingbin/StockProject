import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalChart } from "@/components/charts/TerminalChart";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { changeToneClass, formatAmount } from "@/lib/format";
import type { NorthMoneyItem } from "@/lib/types";


export const FlowView = ({ rows }: { rows: NorthMoneyItem[] }) => {
  const latest = rows.at(-1);
  const previous = rows.at(-2);
  const latestTotal = latest ? latest.north_money : 0;
  const latestDelta = previous ? latestTotal - previous.north_money : latestTotal;
  const tapeRows = [...rows].reverse();

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel={latest?.trade_date ?? "NORTHBOUND"} />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-6">
        <section className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Capital Current</p>
            <h2 className="font-display text-6xl leading-[0.94] tracking-[0.04em] text-white">Northbound Ledger</h2>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              以北向资金为主线，快速判断外资风险偏好、跨市场资金强弱与当日回流节奏。主图看趋势，右侧流水看节拍。
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {[
              { label: "今日合计", value: formatAmount(latestTotal), tone: latestTotal },
              { label: "沪股通", value: formatAmount(latest?.hgt ?? 0), tone: latest?.hgt ?? 0 },
              { label: "深股通", value: formatAmount(latest?.sgt ?? 0), tone: latest?.sgt ?? 0 },
              { label: "较前日", value: formatAmount(latestDelta), tone: latestDelta },
            ].map((item) => (
              <div key={item.label} className="rounded-[26px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.04)] p-5 shadow-[0_22px_48px_rgba(0,0,0,0.18)]">
                <p className="text-[10px] uppercase tracking-[0.34em] text-[var(--terminal-muted)]">{item.label}</p>
                <p className={["mt-4 font-display text-4xl tracking-[0.05em]", changeToneClass(item.tone)].join(" ")}>{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <MetricStrip
          items={[
            { label: "今日合计", value: formatAmount(latestTotal), tone: latestTotal >= 0 ? "up" : "down" },
            { label: "沪股通", value: formatAmount(latest?.hgt ?? 0), tone: (latest?.hgt ?? 0) >= 0 ? "up" : "down" },
            { label: "深股通", value: formatAmount(latest?.sgt ?? 0), tone: (latest?.sgt ?? 0) >= 0 ? "up" : "down" },
            { label: "较前日", value: formatAmount(latestDelta), tone: latestDelta >= 0 ? "up" : "down" },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[1.55fr_0.95fr]">
          <TerminalPanel title="北向净流轨迹" eyebrow="Cross Border" actionLabel={`${rows.length} Sessions`}>
            <TerminalChart
              option={{
                backgroundColor: "transparent",
                tooltip: { trigger: "axis" },
                legend: { textStyle: { color: "#9aa7b8" } },
                xAxis: { type: "category", data: rows.map((item) => item.trade_date.slice(4)), axisLabel: { color: "#9aa7b8" } },
                yAxis: { type: "value", axisLabel: { color: "#9aa7b8" }, splitLine: { lineStyle: { color: "rgba(224,174,116,0.12)" } } },
                series: [
                  { type: "line", smooth: true, name: "HGT", data: rows.map((item) => item.hgt), lineStyle: { color: "#e0ae74", width: 3 } },
                  { type: "line", smooth: true, name: "SGT", data: rows.map((item) => item.sgt), lineStyle: { color: "#ff7a66", width: 3 } },
                ],
              }}
              height={340}
            />
          </TerminalPanel>

          <TerminalPanel title="日度流水" eyebrow="Tape">
            <div className="space-y-3 text-sm">
              {tapeRows.map((row) => (
                <div key={row.trade_date} className="rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-display text-2xl tracking-[0.08em] text-white">{row.trade_date}</span>
                    <span className={changeToneClass(row.north_money)}>{formatAmount(row.north_money)}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-[12px] uppercase tracking-[0.24em] text-[var(--terminal-muted)]">
                    <span>沪股通 {formatAmount(row.hgt)}</span>
                    <span>深股通 {formatAmount(row.sgt)}</span>
                  </div>
                </div>
              ))}
            </div>
          </TerminalPanel>
        </section>
      </main>
    </div>
  );
};
