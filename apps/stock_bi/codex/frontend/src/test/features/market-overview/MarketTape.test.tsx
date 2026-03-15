import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketTape } from "../../../features/market-overview/MarketTape";
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
  index_data: [
    { ts_code: "000001.SH", close: 3321.45, pct_chg: 1.12, name: "上证指数" },
    { ts_code: "399001.SZ", close: 10456.77, pct_chg: -0.42, name: "深证成指" },
  ],
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

describe("MarketTape", () => {
  it("renders the richer desk tape summaries", () => {
    render(<MarketTape summary={summary} />);

    expect(screen.getAllByText("Breadth")).not.toHaveLength(0);
    expect(screen.getAllByText("61.5% 上涨")).not.toHaveLength(0);
    expect(screen.getAllByText("North Flow")).not.toHaveLength(0);
    expect(screen.getAllByText("净流入 12.3 亿")).not.toHaveLength(0);
    expect(screen.getAllByText("Dragon List")).not.toHaveLength(0);
    expect(screen.getAllByText("24 席 / 算力链")).not.toHaveLength(0);
    expect(screen.getAllByText("上证")).not.toHaveLength(0);
    expect(screen.getAllByText("3321.45 / +1.12%")).not.toHaveLength(0);
  });
});
