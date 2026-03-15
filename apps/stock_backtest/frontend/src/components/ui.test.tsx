import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button, DataTable, ProgressBar, Tabs } from "./ui";

describe("lightweight ui primitives", () => {
  test("switches tabs and keeps only the active panel visible", async () => {
    const user = userEvent.setup();

    render(
      <Tabs
        items={[
          { key: "summary", label: "概览", children: <div>summary-panel</div> },
          { key: "risk", label: "风险", children: <div>risk-panel</div> },
        ]}
      />,
    );

    expect(screen.getByText("summary-panel")).toBeInTheDocument();
    expect(screen.queryByText("risk-panel")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "风险" }));
    expect(screen.getByText("risk-panel")).toBeInTheDocument();
    expect(screen.queryByText("summary-panel")).not.toBeInTheDocument();
  });

  test("renders semantic button, progress bar, and table content", () => {
    render(
      <div>
        <Button>开始回测</Button>
        <ProgressBar value={67} />
        <DataTable
          columns={[
            { key: "strategy", title: "策略", render: (record) => record.strategy },
            { key: "annualReturn", title: "年化收益", render: (record) => `${record.annualReturn}%` },
          ]}
          data={[
            { id: "ma", strategy: "双均线交叉", annualReturn: "18.3" },
            { id: "flow", strategy: "资金流向", annualReturn: "22.1" },
          ]}
          rowKey={(record) => record.id}
        />
      </div>,
    );

    expect(screen.getByRole("button", { name: "开始回测" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "67");
    expect(screen.getByRole("columnheader", { name: "策略" })).toBeInTheDocument();
    expect(screen.getByText("资金流向")).toBeInTheDocument();
  });
});
