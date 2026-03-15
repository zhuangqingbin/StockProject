import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DashboardView } from "./DashboardView";


vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));


const overview = {
  trade_date: "20260315",
  indices: [
    { ts_code: "000001.SH", name: "上证指数", close: 3350.12, pct_chg: 1.1 },
    { ts_code: "399001.SZ", name: "深证成指", close: 10820.55, pct_chg: 0.8 },
  ],
  distribution: { "-3~0": 1200, "0~3": 1800 },
  top_gainers: [{ ts_code: "000001.SZ", name: "平安银行", pct_chg: 5.21, close: 12.31 }],
  top_losers: [{ ts_code: "600000.SH", name: "浦发银行", pct_chg: -2.11, close: 9.88 }],
  top_amount: [{ ts_code: "000001.SZ", name: "平安银行", pct_chg: 5.21, close: 12.31, amount: 100000000 }],
  top_turnover: [{ ts_code: "300750.SZ", name: "宁德时代", pct_chg: 2.31, close: 212.9, turnover_rate: 6.8 }],
  limit_stats: { up_count: 12, down_count: 1, broken_count: 3, broken_rate: 0.2, tier_stats: { "1": 8, "2": 3 } },
};


it("renders the terminal dashboard shell with major modules", () => {
  render(
    <DashboardView
      overview={overview}
      northFlow={[]}
      topList={[]}
      heatmapRows={[
        { industry: "银行", avg_pct_chg: 1.32, total_amount: 4500000000, up_count: 28, down_count: 5, net_mf_amount: 560000000, stock_count: 33 },
      ]}
    />,
  );

  expect(screen.getByText("STOCK BI")).toBeInTheDocument();
  expect(screen.getByText("Market Atlas")).toBeInTheDocument();
  expect(screen.getByText("今日市场导航")).toBeInTheDocument();
  expect(screen.getByText("行业热区")).toBeInTheDocument();
  expect(screen.getByText("异动雷达")).toBeInTheDocument();
  expect(screen.getByText("涨停梯队")).toBeInTheDocument();
  expect(screen.getAllByText("平安银行").length).toBeGreaterThan(0);
});
