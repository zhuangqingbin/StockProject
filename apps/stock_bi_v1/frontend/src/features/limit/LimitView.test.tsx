import { render, screen } from "@testing-library/react";

import { LimitView } from "./LimitView";


it("renders the limit ladder with summary stats and stock links", () => {
  render(
    <LimitView
      limitStats={{ up_count: 12, down_count: 1, broken_count: 3, broken_rate: 0.2, tier_stats: { "1": 8, "2": 3 } }}
      limitList={[{ ts_code: "000001.SZ", name: "平安银行" }]}
    />,
  );

  expect(screen.getByText("Limit Ladder")).toBeInTheDocument();
  expect(screen.getAllByText("炸板率").length).toBeGreaterThan(0);
  expect(screen.getByRole("link", { name: "平安银行" })).toHaveAttribute("href", "/stock/000001.SZ");
});
