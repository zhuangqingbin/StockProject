"use client";

import Link from "next/link";
import { useState } from "react";

import { TerminalChart } from "@/components/charts/TerminalChart";
import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { changeToneClass, formatAmount, formatPercent, formatPrice } from "@/lib/format";
import type { FlowItem, KlineItem, PeerItem, StockProfile, TopListItem } from "@/lib/types";


type StockDetailViewProps = {
  profile: StockProfile;
  kline: KlineItem[];
  valuationHistory: Array<{ trade_date: string; pe_ttm: number; pb: number; ps_ttm: number }>;
  flowHistory: FlowItem[];
  toplistHistory: TopListItem[];
  historyRows: KlineItem[];
  peerRows: PeerItem[];
};


const tabs = ["资金流向", "估值趋势", "大单明细", "龙虎榜记录", "历史行情"] as const;

const statCardClass = "rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4";


export const StockDetailView = ({
  profile,
  kline,
  valuationHistory,
  flowHistory,
  toplistHistory,
  historyRows,
  peerRows,
}: StockDetailViewProps) => {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("资金流向");
  const [activePeriod, setActivePeriod] = useState("日K");
  const latestFlow = flowHistory.at(-1);
  const latestToplist = toplistHistory.at(-1);
  const focusPeers = peerRows.slice(0, 4);

  const groupedKline = (() => {
    if (activePeriod === "日K") {
      return kline;
    }

    const bucketed = new Map<string, KlineItem[]>();
    for (const item of kline) {
      const bucket = activePeriod === "周K" ? item.trade_date.slice(0, 6) : item.trade_date.slice(0, 4);
      bucketed.set(bucket, [...(bucketed.get(bucket) ?? []), item]);
    }

    return Array.from(bucketed.values()).map((bucketRows) => ({
      trade_date: bucketRows.at(-1)?.trade_date ?? "",
      open: bucketRows[0]?.open ?? 0,
      high: Math.max(...bucketRows.map((row) => row.high)),
      low: Math.min(...bucketRows.map((row) => row.low)),
      close: bucketRows.at(-1)?.close ?? 0,
      vol: bucketRows.reduce((sum, row) => sum + row.vol, 0),
      amount: bucketRows.reduce((sum, row) => sum + row.amount, 0),
      pct_chg: bucketRows.at(-1)?.pct_chg ?? 0,
    }));
  })();

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel={kline.at(-1)?.trade_date ?? "LIVE"} />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-6">
        <section className="grid gap-6 xl:grid-cols-[1.3fr_0.95fr]">
          <div className="space-y-5">
            <div>
              <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Equity Dossier</p>
              <h2 className="font-display text-6xl leading-[0.94] tracking-[0.04em] text-white">{profile.name}</h2>
              <p className="mt-3 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
                {profile.ts_code} / {profile.exchange}
                {profile.market ? ` / ${profile.market}` : ""}
              </p>
            </div>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              从价格、估值、资金和异动记录四个层面快速读懂这只股票。顶部看当前 session，下面看轨迹、同业和历史上下文。
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href={`/industry?name=${encodeURIComponent(profile.industry)}`}
                className="rounded-full border border-[rgba(224,174,116,0.45)] bg-[rgba(224,174,116,0.08)] px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-accent)] transition hover:bg-[rgba(224,174,116,0.14)]"
              >
                {profile.industry}
              </Link>
              <span className="rounded-full border border-[var(--terminal-line)] px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
                换手 {formatPercent(profile.turnover_rate)}
              </span>
              <span className="rounded-full border border-[var(--terminal-line)] px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
                总市值 {formatAmount(profile.total_mv)}
              </span>
              {latestToplist ? (
                <span className="rounded-full border border-[var(--terminal-line)] px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">
                  最近上榜 {latestToplist.trade_date}
                </span>
              ) : null}
            </div>
          </div>

          <aside className="rounded-[30px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.04)] p-6 shadow-[0_22px_48px_rgba(0,0,0,0.18)]">
            <p className="text-[10px] uppercase tracking-[0.36em] text-[var(--terminal-muted)]">Session Mark</p>
            <div className="mt-4 flex items-end justify-between gap-4">
              <p className="font-display text-7xl leading-none text-white">{formatPrice(profile.current_price)}</p>
              <p className={["text-2xl font-semibold", changeToneClass(profile.pct_chg)].join(" ")}>{formatPercent(profile.pct_chg)}</p>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className={statCardClass}>
                <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">成交额</p>
                <p className="mt-2 text-white">{formatAmount(profile.amount)}</p>
              </div>
              <div className={statCardClass}>
                <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">成交量</p>
                <p className="mt-2 text-white">{formatAmount(profile.vol)}</p>
              </div>
              <div className={statCardClass}>
                <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">振幅区间</p>
                <p className="mt-2 text-white">
                  {formatPrice(profile.low)} - {formatPrice(profile.high)}
                </p>
              </div>
              <div className={statCardClass}>
                <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">主力净流</p>
                <p className={["mt-2", changeToneClass(latestFlow?.net_mf_amount ?? 0)].join(" ")}>{formatAmount(latestFlow?.net_mf_amount ?? 0)}</p>
              </div>
            </div>
          </aside>
        </section>

        <MetricStrip
          items={[
            { label: "开盘", value: formatPrice(profile.open) },
            { label: "最高", value: formatPrice(profile.high), tone: "up" },
            { label: "最低", value: formatPrice(profile.low), tone: "down" },
            { label: "昨收", value: formatPrice(profile.pre_close) },
            { label: "PE(TTM)", value: profile.pe_ttm.toFixed(2) },
            { label: "PB", value: profile.pb.toFixed(2) },
            { label: "总市值", value: formatAmount(profile.total_mv) },
            { label: "流通市值", value: formatAmount(profile.circ_mv) },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[1.55fr_0.95fr]">
          <TerminalPanel title="价格轨迹" eyebrow="Tape & Candles" actionLabel={activePeriod}>
            <div className="mb-4 flex gap-2">
              {["日K", "周K", "月K"].map((period) => (
                <button
                  key={period}
                  type="button"
                  className={period === activePeriod ? "terminal-button-active" : "terminal-button"}
                  onClick={() => setActivePeriod(period)}
                >
                  {period}
                </button>
              ))}
            </div>
            <TerminalChart
              option={{
                backgroundColor: "transparent",
                tooltip: { trigger: "axis" },
                xAxis: { type: "category", data: groupedKline.map((item) => item.trade_date.slice(4)), axisLabel: { color: "#9aa7b8" } },
                yAxis: { type: "value", axisLabel: { color: "#9aa7b8" }, splitLine: { lineStyle: { color: "rgba(224,174,116,0.12)" } } },
                series: [
                  {
                    type: "candlestick",
                    data: groupedKline.map((item) => [item.open, item.close, item.low, item.high]),
                    itemStyle: { color: "#ff7a66", color0: "#6fd0b3", borderColor: "#ff7a66", borderColor0: "#6fd0b3" },
                  },
                ],
              }}
              height={360}
            />
          </TerminalPanel>

          <div className="space-y-6">
            <TerminalPanel title="估值锚点" eyebrow="Valuation">
              <div className="grid grid-cols-2 gap-3">
                <div className={statCardClass}>
                  <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">PB</p>
                  <p className="mt-2 text-white">{profile.pb.toFixed(2)}</p>
                </div>
                <div className={statCardClass}>
                  <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">PS(TTM)</p>
                  <p className="mt-2 text-white">{profile.ps_ttm.toFixed(2)}</p>
                </div>
                <div className={statCardClass}>
                  <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">总股本</p>
                  <p className="mt-2 text-white">{formatAmount(profile.total_share)}</p>
                </div>
                <div className={statCardClass}>
                  <p className="text-[10px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">流通股本</p>
                  <p className="mt-2 text-white">{formatAmount(profile.float_share)}</p>
                </div>
              </div>
            </TerminalPanel>

            <TerminalPanel title="同行切片" eyebrow="Peers">
              {focusPeers.length > 0 ? (
                <div className="space-y-3">
                  {focusPeers.map((peer) => (
                    <div key={peer.ts_code} className="rounded-[20px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                      <div className="flex items-center justify-between gap-3">
                        <Link href={`/stock/${peer.ts_code}`} className="font-display text-2xl tracking-[0.05em] text-white transition hover:text-[var(--terminal-accent)]">
                          {peer.name}
                        </Link>
                        <span className={changeToneClass(peer.pct_chg)}>{formatPercent(peer.pct_chg)}</span>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-sm text-[var(--terminal-muted)]">
                        <span>{peer.ts_code}</span>
                        <span>市值 {formatAmount(peer.total_mv)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-[var(--terminal-muted)]">暂无同业对比数据。</p>
              )}
            </TerminalPanel>
          </div>
        </section>

        <div className="flex flex-wrap gap-2 border-b border-[var(--terminal-line)] pb-2">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={tab === activeTab}
              className={tab === activeTab ? "terminal-tab-active" : "terminal-tab"}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "资金流向" ? (
          <TerminalPanel title="主力净流入" eyebrow="Capital Flow">
            <TerminalChart
              option={{
                backgroundColor: "transparent",
                tooltip: { trigger: "axis" },
                xAxis: { type: "category", data: flowHistory.map((item) => item.trade_date.slice(4)), axisLabel: { color: "#9aa7b8" } },
                yAxis: { type: "value", axisLabel: { color: "#9aa7b8" }, splitLine: { lineStyle: { color: "rgba(224,174,116,0.12)" } } },
                series: [{ type: "bar", data: flowHistory.map((item) => item.net_mf_amount ?? 0), itemStyle: { color: "#e0ae74" } }],
              }}
              height={280}
            />
          </TerminalPanel>
        ) : null}

        {activeTab === "估值趋势" ? (
          <TerminalPanel title="估值区间监控" eyebrow="Valuation Trend">
            <TerminalChart
              option={{
                backgroundColor: "transparent",
                tooltip: { trigger: "axis" },
                legend: { textStyle: { color: "#9aa7b8" } },
                xAxis: { type: "category", data: valuationHistory.map((item) => item.trade_date.slice(4)), axisLabel: { color: "#9aa7b8" } },
                yAxis: { type: "value", axisLabel: { color: "#9aa7b8" }, splitLine: { lineStyle: { color: "rgba(224,174,116,0.12)" } } },
                series: [
                  { type: "line", smooth: true, name: "PE", data: valuationHistory.map((item) => item.pe_ttm), lineStyle: { color: "#e0ae74", width: 3 } },
                  { type: "line", smooth: true, name: "PB", data: valuationHistory.map((item) => item.pb), lineStyle: { color: "#ff7a66", width: 3 } },
                ],
              }}
              height={280}
            />
          </TerminalPanel>
        ) : null}

        {activeTab === "大单明细" ? (
          <TerminalPanel title="大单结构" eyebrow="Large Order">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {[
                { key: "buy_elg_amount", label: "超大单买入" },
                { key: "sell_elg_amount", label: "超大单卖出" },
                { key: "buy_lg_amount", label: "大单买入" },
                { key: "sell_lg_amount", label: "大单卖出" },
              ].map((item) => (
                <div key={item.key} className={statCardClass}>
                  <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--terminal-muted)]">{item.label}</p>
                  <p className="mt-2 font-display text-2xl text-white">{formatAmount(Number(latestFlow?.[item.key as keyof FlowItem] ?? 0))}</p>
                </div>
              ))}
            </div>
          </TerminalPanel>
        ) : null}

        {activeTab === "龙虎榜记录" ? (
          <TerminalPanel title="上榜记录" eyebrow="Top List">
            {toplistHistory.length > 0 ? (
              <div className="space-y-3">
                {toplistHistory.map((item) => (
                  <div key={`${item.ts_code}-${item.trade_date}`} className="rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-display text-2xl text-white">{item.trade_date}</span>
                      <span className={changeToneClass(item.pct_chg)}>{formatPercent(item.pct_chg)}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[var(--terminal-muted)]">{item.reason ?? "无上榜原因说明"}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm leading-6 text-[var(--terminal-muted)]">暂无龙虎榜记录。</p>
            )}
          </TerminalPanel>
        ) : null}

        {activeTab === "历史行情" ? (
          <TerminalPanel title="历史行情表" eyebrow="Tape">
            {historyRows.length > 0 ? (
              <>
                <div className="grid grid-cols-5 gap-3 border-b border-[var(--terminal-line)] pb-3 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">
                  <span>日期</span>
                  <span>开盘</span>
                  <span>最高</span>
                  <span>最低</span>
                  <span>收盘</span>
                </div>
                <div className="space-y-2 pt-3 text-sm">
                  {historyRows.map((row) => (
                    <div key={row.trade_date} className="grid grid-cols-5 gap-3 border-b border-[var(--terminal-line)] pb-2 last:border-b-0">
                      <span>{row.trade_date}</span>
                      <span>{formatPrice(row.open)}</span>
                      <span>{formatPrice(row.high)}</span>
                      <span>{formatPrice(row.low)}</span>
                      <span>{formatPrice(row.close)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm leading-6 text-[var(--terminal-muted)]">暂无历史行情数据。</p>
            )}
          </TerminalPanel>
        ) : null}
      </main>
    </div>
  );
};
