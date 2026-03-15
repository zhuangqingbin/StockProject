"use client";

import { useEffect, useState } from "react";

import { searchStocks } from "@/lib/api";


type TopBarProps = {
  dateLabel: string;
};


export const TopBar = ({ dateLabel }: TopBarProps) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Array<{ ts_code: string; name: string }>>([]);
  const visibleSuggestions = query.trim().length < 2 ? [] : suggestions;

  useEffect(() => {
    if (query.trim().length < 2) {
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        setSuggestions(await searchStocks(query.trim()));
      } catch {
        setSuggestions([]);
      }
    }, 220);

    return () => window.clearTimeout(timer);
  }, [query]);

  const goToStock = (value: string) => {
    if (typeof window !== "undefined") {
      window.location.href = `/stock/${value}`;
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }

    try {
      const matches = await searchStocks(query.trim());
      goToStock(matches[0]?.ts_code ?? query.trim().toUpperCase());
    } catch {
      goToStock(query.trim().toUpperCase());
    }
  };

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--terminal-line)] bg-[rgba(8,16,25,0.82)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1600px] items-center gap-4 px-5 py-4">
        <div className="flex min-w-[240px] items-center gap-3">
          <span className="rounded-full border border-[rgba(224,174,116,0.35)] bg-[rgba(224,174,116,0.08)] px-2 py-1 text-sm uppercase tracking-[0.32em] text-[var(--terminal-accent)]">
            BI
          </span>
          <div>
            <p className="text-[10px] uppercase tracking-[0.45em] text-[var(--terminal-muted)]">Editorial Market Desk</p>
            <h1 className="font-display text-[2rem] tracking-[0.18em] text-white">STOCK BI</h1>
          </div>
        </div>
        <div className="relative flex-1">
          <form onSubmit={handleSubmit}>
            <input
              aria-label="全局股票搜索"
              className="terminal-input"
              placeholder="搜索股票代码、简称或行业线索"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </form>
          {visibleSuggestions.length > 0 ? (
            <div className="absolute inset-x-0 top-[calc(100%+8px)] z-30 overflow-hidden rounded-[24px] border border-[var(--terminal-line)] bg-[var(--terminal-panel)] shadow-2xl">
              {visibleSuggestions.slice(0, 6).map((item) => (
                <button
                  key={item.ts_code}
                  type="button"
                  className="flex w-full items-center justify-between border-b border-[var(--terminal-line)] px-4 py-3 text-left text-sm last:border-b-0 hover:bg-[rgba(224,174,116,0.08)]"
                  onClick={() => goToStock(item.ts_code)}
                >
                  <span className="text-white">{item.name}</span>
                  <span className="text-[var(--terminal-muted)]">{item.ts_code}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <div className="min-w-[200px] rounded-full border border-[var(--terminal-line)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-right">
          <p className="text-[10px] uppercase tracking-[0.42em] text-[var(--terminal-muted)]">Trade Date</p>
          <p className="mt-1 font-display text-xl uppercase tracking-[0.18em] text-white">{dateLabel}</p>
        </div>
      </div>
    </header>
  );
};
