"use client";

import Link from "next/link";
import { useState } from "react";

import { MetricStrip } from "@/components/terminal/MetricStrip";
import { TerminalPanel } from "@/components/terminal/TerminalPanel";
import { TopBar } from "@/components/terminal/TopBar";
import { exportScreener, queryScreener } from "@/lib/api";
import { changeToneClass, formatAmount, formatPercent, formatPrice } from "@/lib/format";
import type { FilterMeta, ScreenerCondition, ScreenerResultItem } from "@/lib/types";


type ScreenerViewProps = {
  filters: FilterMeta[];
  initialResults: ScreenerResultItem[];
};


export const ScreenerView = ({ filters, initialResults }: ScreenerViewProps) => {
  const [conditions, setConditions] = useState<ScreenerCondition[]>([
    { field: filters[0]?.field ?? "pct_chg", operator: filters[0]?.operators[0] ?? "gt", value: "" },
  ]);
  const [results, setResults] = useState(initialResults);
  const [isLoading, setIsLoading] = useState(false);

  const activeConditionCount = conditions.filter((condition) => String(condition.value).trim().length > 0).length;

  const addCondition = () => {
    setConditions((current) => [
      ...current,
      { field: filters[current.length % filters.length]?.field ?? "pct_chg", operator: "gt", value: "" },
    ]);
  };

  const updateCondition = (index: number, patch: Partial<ScreenerCondition>) => {
    setConditions((current) =>
      current.map((condition, conditionIndex) => (conditionIndex === index ? { ...condition, ...patch } : condition)),
    );
  };

  const buildPayload = () => ({
    conditions: conditions
      .filter((condition) => String(condition.value).trim().length > 0)
      .map((condition) => ({
        field: condition.field,
        operator: condition.operator,
        value:
          condition.operator === "between"
            ? String(condition.value)
                .split(",")
                .map((item) => item.trim())
            : condition.value,
      })),
    sort_by: "pct_chg",
    order: "desc",
    page: 0,
    size: 20,
  });

  const runQuery = async () => {
    setIsLoading(true);
    try {
      const payload = await queryScreener(buildPayload());
      setResults(payload.items);
    } catch {
      setResults(initialResults);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadCsv = async () => {
    try {
      const blob = await exportScreener(buildPayload());
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "stock-bi-v1-screener.csv";
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      // Keep fallback behavior when backend is unavailable.
    }
  };

  return (
    <div className="min-h-screen bg-[var(--terminal-bg)] text-white">
      <TopBar dateLabel="SCREEN" />
      <main className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-5 py-6">
        <section className="grid gap-6 xl:grid-cols-[1.25fr_1fr]">
          <div className="space-y-4">
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Signal Forge</p>
            <h2 className="font-display text-6xl leading-[0.94] tracking-[0.04em] text-white">高级筛选器</h2>
            <p className="max-w-3xl text-base leading-7 text-[var(--terminal-muted)]">
              像搭建交易假设一样拼装规则，快速筛出情绪共振、估值错位和资金偏好的候选池，并直接钻取到个股页。
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {[
              { label: "生效规则", value: String(activeConditionCount) },
              { label: "候选池", value: String(results.length) },
              { label: "默认排序", value: "涨跌幅" },
              { label: "导出格式", value: "CSV" },
            ].map((item) => (
              <div key={item.label} className="rounded-[24px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.04)] p-5 shadow-[0_18px_40px_rgba(0,0,0,0.16)]">
                <p className="text-[10px] uppercase tracking-[0.34em] text-[var(--terminal-muted)]">{item.label}</p>
                <p className="mt-4 font-display text-4xl tracking-[0.05em] text-white">{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="flex flex-wrap gap-2">
          <button type="button" className="terminal-button" onClick={addCondition}>
            添加条件
          </button>
          <button type="button" className="terminal-button" onClick={runQuery}>
            {isLoading ? "执行中..." : "执行筛选"}
          </button>
          <button type="button" className="terminal-button-active" onClick={downloadCsv}>
            导出 CSV
          </button>
        </div>

        <MetricStrip
          items={[
            { label: "生效规则", value: String(activeConditionCount) },
            { label: "候选池", value: String(results.length) },
            { label: "最高涨幅", value: formatPercent(results[0]?.pct_chg ?? 0), tone: (results[0]?.pct_chg ?? 0) >= 0 ? "up" : "down" },
            { label: "最大净流", value: formatAmount(results[0]?.net_mf_amount ?? 0), tone: (results[0]?.net_mf_amount ?? 0) >= 0 ? "up" : "down" },
          ]}
        />

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <TerminalPanel title="规则编排" eyebrow="Rules" actionLabel={`${conditions.length} Slots`}>
            <div className="grid gap-3">
              {conditions.map((condition, index) => (
                <div key={`${condition.field}-${index}`} className="grid gap-3 rounded-[22px] border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-4 lg:grid-cols-[120px_180px_160px_1fr]">
                  <span className="text-[10px] uppercase tracking-[0.3em] text-[var(--terminal-muted)]">条件 {index + 1}</span>
                  <select className="terminal-input" value={condition.field} onChange={(event) => updateCondition(index, { field: event.target.value })}>
                    {filters.map((filter) => (
                      <option key={filter.field} value={filter.field}>
                        {filter.label}
                      </option>
                    ))}
                  </select>
                  <select className="terminal-input" value={condition.operator} onChange={(event) => updateCondition(index, { operator: event.target.value })}>
                    {(filters.find((filter) => filter.field === condition.field)?.operators ?? ["eq"]).map((operator) => (
                      <option key={operator} value={operator}>
                        {operator}
                      </option>
                    ))}
                  </select>
                  <input
                    className="terminal-input"
                    value={String(condition.value)}
                    placeholder="输入阈值或区间"
                    onChange={(event) => updateCondition(index, { value: event.target.value })}
                  />
                </div>
              ))}
            </div>
          </TerminalPanel>

          <TerminalPanel title="候选清单" eyebrow="Candidates" actionLabel={`${results.length} Rows`}>
            <div className="grid grid-cols-[1.2fr_0.8fr_0.65fr_0.7fr_0.7fr_0.9fr] gap-3 border-b border-[var(--terminal-line)] pb-3 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">
              <span>股票</span>
              <span>行业</span>
              <span>现价</span>
              <span>涨跌幅</span>
              <span>PE</span>
              <span>主力净流</span>
            </div>
            <div className="space-y-3 pt-3 text-sm">
              {results.map((item) => (
                <div key={item.ts_code} className="grid grid-cols-[1.2fr_0.8fr_0.65fr_0.7fr_0.7fr_0.9fr] gap-3 border-b border-[var(--terminal-line)] pb-3 last:border-b-0 last:pb-0">
                  <div>
                    <Link href={`/stock/${item.ts_code}`} className="font-display text-2xl leading-none tracking-[0.05em] text-white transition hover:text-[var(--terminal-accent)]">
                      {item.name}
                    </Link>
                    <p className="mt-1 text-[11px] uppercase tracking-[0.26em] text-[var(--terminal-muted)]">
                      {item.ts_code} / {item.market}
                    </p>
                  </div>
                  <span>{item.industry}</span>
                  <span>{formatPrice(item.close)}</span>
                  <span className={changeToneClass(item.pct_chg)}>{formatPercent(item.pct_chg)}</span>
                  <span>{item.pe_ttm.toFixed(2)}</span>
                  <span className={changeToneClass(item.net_mf_amount)}>{formatAmount(item.net_mf_amount)}</span>
                </div>
              ))}
            </div>
          </TerminalPanel>
        </section>
      </main>
    </div>
  );
};
