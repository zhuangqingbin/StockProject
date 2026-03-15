import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StockDetailView } from "./StockDetailView";


it("renders stock detail metrics, tabs, and kline controls", async () => {
  const user = userEvent.setup();

  render(
    <StockDetailView
      profile={{
        ts_code: "000001.SZ",
        name: "平安银行",
        industry: "银行",
        exchange: "SZSE",
        current_price: 11.7,
        pct_chg: 2.63,
        open: 11.5,
        high: 11.8,
        low: 11.3,
        pre_close: 11.4,
        amount: 5567890,
        vol: 153456,
        turnover_rate: 1.8,
        pe_ttm: 6.2,
        pb: 0.7,
        ps_ttm: 1.1,
        total_mv: 210000000000,
        circ_mv: 180000000000,
        total_share: 19400000000,
        float_share: 16200000000,
      }}
      kline={[{ trade_date: "20260313", open: 11.5, high: 11.8, low: 11.3, close: 11.7, vol: 153456, amount: 5567890, pct_chg: 2.63 }]}
      valuationHistory={[]}
      flowHistory={[]}
      toplistHistory={[]}
      historyRows={[]}
      peerRows={[]}
    />,
  );

  expect(screen.getByText("平安银行")).toBeInTheDocument();
  expect(screen.getByText("Equity Dossier")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "日K" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "周K" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "资金流向" })).toBeInTheDocument();

  await user.click(screen.getByRole("tab", { name: "估值趋势" }));
  expect(screen.getByText("估值区间监控")).toBeInTheDocument();
});
