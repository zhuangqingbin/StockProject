import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HeroBrief } from "../../../features/market-overview/HeroBrief";
import type { SummaryResponse } from "../../../lib/api/types";

const summary: SummaryResponse = {
  trade_date: "20260315",
  trade_date_fmt: "2026-03-15",
  total_stocks: 5200,
  up_count: 3200,
  down_count: 1800,
  flat_count: 200,
  limit_up: 86,
  limit_down: 7,
  total_amount: 18234,
  avg_pct_chg: 1.24,
  north_money: {
    north_total: 1234,
    hgt: 600,
    sgt: 634,
    trade_date: "20260315",
  },
  top_list_summary: {
    count: 24,
    net_buy_amount: 18.8,
    top_reason: "算力链",
  },
  data_consistency: {
    consistent: true,
    primary_date: "20260315",
    warnings: [],
  },
  index_data: [],
  pct_distribution: [],
  industry_ranking: [
    {
      name: "半导体",
      pct_chg: 4.8,
      avg5_pct_chg: 3.6,
      total_amount: 3200,
      stock_count: 48,
      up_count: 38,
      down_count: 6,
      up_ratio: 0.79,
    },
  ],
  top_gainers: [],
  top_losers: [],
  top_amount: [],
  top_turnover: [],
};

describe("HeroBrief", () => {
  it("renders the editorial lead, signal cards, and desk notes", () => {
    render(<HeroBrief summary={summary} />);

    expect(screen.getByText("Morning Lead")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "广度占优，增量资金没有缺席" })).toBeInTheDocument();
    expect(screen.getByText("Breadth")).toBeInTheDocument();
    expect(screen.getAllByText(/61\.5%/)).not.toHaveLength(0);
    expect(screen.getByText("净流入 12.3 亿")).toBeInTheDocument();
    expect(screen.getByText("半导体 4.80%")).toBeInTheDocument();
    expect(screen.getByText("Desk Notes")).toBeInTheDocument();
    expect(screen.getByText("龙虎榜")).toBeInTheDocument();
    expect(screen.getByText("算力链")).toBeInTheDocument();
  });
});
