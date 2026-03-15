import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import App from "../App";

const renderApp = (initialEntry = "/") =>
  render(
    <MemoryRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }} initialEntries={[initialEntry]}>
      <App />
    </MemoryRouter>,
  );

describe("stock backtest app shell", () => {
  test("renders the platform dashboard as the default route", async () => {
    renderApp();

    expect(await screen.findByRole("heading", { name: "平台总览" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "数据实验室" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "策略工坊" })).toBeInTheDocument();
  });

  test("navigates to the data lab and then into the strategy studio editor", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getByRole("link", { name: "数据实验室" }));
    expect(await screen.findByRole("heading", { name: "数据实验室" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "基准指数" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "策略工坊" }));
    await user.click(await screen.findByRole("button", { name: "代码编辑" }));

    expect(await screen.findByLabelText("strategy-code-editor")).toBeInTheDocument();
  });

  test("switches analysis tabs without losing the current panel content", async () => {
    const user = userEvent.setup();
    renderApp("/analysis");

    expect(await screen.findByText("交易明细")).toBeInTheDocument();
    expect((await screen.findAllByText("000001.SZ")).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("tab", { name: "行业暴露" }));
    expect(screen.getByText("银行 42%")).toBeInTheDocument();
    expect(screen.queryByText("000001.SZ")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "滚动指标" }));
    expect(screen.getByText("2025-01-02")).toBeInTheDocument();
    expect(screen.getByText("0.92")).toBeInTheDocument();
  });
});
