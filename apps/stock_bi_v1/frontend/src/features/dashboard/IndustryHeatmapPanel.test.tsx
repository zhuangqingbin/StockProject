import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IndustryHeatmapPanel } from "./IndustryHeatmapPanel";


const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));


describe("IndustryHeatmapPanel", () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  it("drills into the selected industry from the heatmap rail", async () => {
    const user = userEvent.setup();

    render(
      <IndustryHeatmapPanel
        rows={[
          { industry: "银行", avg_pct_chg: 1.32, total_amount: 4500000000, up_count: 28, down_count: 5, net_mf_amount: 560000000, stock_count: 33 },
          { industry: "电池", avg_pct_chg: -0.82, total_amount: 5900000000, up_count: 18, down_count: 22, net_mf_amount: -130000000, stock_count: 40 },
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: /银行/ }));

    expect(pushMock).toHaveBeenCalledWith("/industry?name=%E9%93%B6%E8%A1%8C");
  });
});
