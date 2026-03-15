import { render, screen } from "@testing-library/react";

import { FlowView } from "./FlowView";


it("renders the northbound ledger with summary metrics", () => {
  render(
    <FlowView
      rows={[
        { trade_date: "20260313", north_money: 1250000000, south_money: 0, hgt: 780000000, sgt: 470000000 },
        { trade_date: "20260314", north_money: 980000000, south_money: 0, hgt: 610000000, sgt: 370000000 },
      ]}
    />,
  );

  expect(screen.getByText("Northbound Ledger")).toBeInTheDocument();
  expect(screen.getAllByText("今日合计").length).toBeGreaterThan(0);
  expect(screen.getAllByText("沪股通").length).toBeGreaterThan(0);
  expect(screen.getAllByText("深股通").length).toBeGreaterThan(0);
});
