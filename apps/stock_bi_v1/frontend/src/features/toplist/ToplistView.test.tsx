import { render, screen } from "@testing-library/react";

import { ToplistView } from "./ToplistView";


it("renders the toplist ledger with stock drilldown links", () => {
  render(
    <ToplistView
      rows={[
        { ts_code: "000001.SZ", name: "平安银行", trade_date: "20260314", close: 11.7, pct_chg: 5.21, reason: "日涨幅偏离值达7%" },
      ]}
    />,
  );

  expect(screen.getByText("Toplist Ledger")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "平安银行" })).toHaveAttribute("href", "/stock/000001.SZ");
});
