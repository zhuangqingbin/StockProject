import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ScreenerView } from "./ScreenerView";


it("supports multi-condition screener workflows", async () => {
  const user = userEvent.setup();

  render(
    <ScreenerView
      filters={[
        { field: "pct_chg", label: "涨跌幅", category: "行情", operators: ["gt", "lt", "between"] },
        { field: "pe_ttm", label: "PE(TTM)", category: "估值", operators: ["gt", "lt", "between"] },
      ]}
      initialResults={[
        { ts_code: "000001.SZ", name: "平安银行", industry: "银行", market: "主板", close: 11.7, pct_chg: 2.63, pe_ttm: 6.2, pb: 0.7, amount: 5567890, turnover_rate: 1.8, ps_ttm: 1.1, total_mv: 210000000000, net_mf_amount: 950 },
      ]}
    />,
  );

  expect(screen.getByText("高级筛选器")).toBeInTheDocument();
  expect(screen.getByText("Signal Forge")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "平安银行" })).toHaveAttribute("href", "/stock/000001.SZ");

  await user.click(screen.getByRole("button", { name: "添加条件" }));
  expect(screen.getAllByText(/条件/).length).toBeGreaterThan(1);
  expect(screen.getByRole("button", { name: "导出 CSV" })).toBeInTheDocument();
});
