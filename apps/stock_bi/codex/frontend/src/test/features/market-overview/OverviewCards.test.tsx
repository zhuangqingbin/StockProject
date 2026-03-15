import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OverviewCards } from "../../../features/market-overview/OverviewCards";
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
  industry_ranking: [],
  top_gainers: [],
  top_losers: [],
  top_amount: [],
  top_turnover: [],
};

describe("OverviewCards", () => {
  it("adds contextual hints beneath the ledger metrics", () => {
    render(<OverviewCards summary={summary} />);

    expect(screen.getByText("上涨家数")).toBeInTheDocument();
    expect(screen.getByText("占比 61.5%")).toBeInTheDocument();
    expect(screen.getByText("下跌家数")).toBeInTheDocument();
    expect(screen.getByText("占比 34.6%")).toBeInTheDocument();
    expect(screen.getByText("成交额")).toBeInTheDocument();
    expect(screen.getByText("平均涨跌 +1.24%")).toBeInTheDocument();
    expect(screen.getByText("涨停数")).toBeInTheDocument();
    expect(screen.getByText("跌停仅 7 家")).toBeInTheDocument();
    expect(screen.getByText("北向资金")).toBeInTheDocument();
    expect(screen.getByText("沪股通 600 / 深股通 634")).toBeInTheDocument();
  });
});
