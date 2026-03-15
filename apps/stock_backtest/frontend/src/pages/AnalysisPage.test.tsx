import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { AnalysisPage } from "./AnalysisPage";

const clientMocks = vi.hoisted(() => ({
  getRuns: vi.fn(),
  getAnalysis: vi.fn(),
}));

vi.mock("../services/client", () => ({
  stockBacktestClient: {
    getRuns: clientMocks.getRuns,
    getAnalysis: clientMocks.getAnalysis,
  },
}));

describe("AnalysisPage", () => {
  beforeEach(() => {
    clientMocks.getRuns.mockResolvedValue([
      {
        id: 4,
        strategyId: 6,
        title: "ATR 趋势跟随 #4",
        status: "completed",
        progress: 100,
        range: "2025.01 - 2025.12",
        symbols: ["000001.SZ"],
        annualReturn: 0.11,
        maxDrawdown: -0.08,
        sharpeRatio: 1.2,
      },
    ]);
    clientMocks.getAnalysis.mockResolvedValue({
      runId: 11,
      strategyName: "Run #11",
      metrics: {
        totalReturn: 0.12,
        annualReturn: 0.08,
        maxDrawdown: -0.05,
        sharpeRatio: 1.1,
        winRate: 0.62,
        profitLossRatio: 1.6,
      },
      daily: [
        { tradeDate: "2025-01-02", cumulativeReturn: 0, drawdown: 0, portfolioValue: 1000000 },
        { tradeDate: "2025-01-03", cumulativeReturn: 0.01, drawdown: -0.002, portfolioValue: 1010000 },
      ],
      trades: [{ tradeDate: "2025-01-03", symbol: "000001.SZ", direction: "buy", price: 10.2, size: 100, pnl: 0 }],
      industryExposure: [{ industry: "银行", weight: 0.42 }],
      rollingSharpe: [{ tradeDate: "2025-01-03", value: 1.1 }],
      monthlyReturns: [{ month: "2025-01", value: 0.03 }],
    });
  });

  test("loads analysis for the run id from the url", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/analysis?runId=11"]}>
          <AnalysisPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Run #11" })).toBeInTheDocument();
    expect(clientMocks.getAnalysis).toHaveBeenCalledWith(11);
  });

  test("falls back to the latest available run when the url has no run id", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    clientMocks.getAnalysis.mockResolvedValueOnce({
      runId: 4,
      strategyName: "Run #4",
      metrics: {
        totalReturn: 0.06,
        annualReturn: 0.04,
        maxDrawdown: -0.03,
        sharpeRatio: 0.9,
        winRate: 0.58,
        profitLossRatio: 1.4,
      },
      daily: [
        { tradeDate: "2025-01-02", cumulativeReturn: 0, drawdown: 0, portfolioValue: 1000000 },
        { tradeDate: "2025-01-03", cumulativeReturn: 0.005, drawdown: -0.001, portfolioValue: 1005000 },
      ],
      trades: [{ tradeDate: "2025-01-03", symbol: "000001.SZ", direction: "buy", price: 10.2, size: 100, pnl: 0 }],
      industryExposure: [{ industry: "银行", weight: 0.42 }],
      rollingSharpe: [{ tradeDate: "2025-01-03", value: 0.9 }],
      monthlyReturns: [{ month: "2025-01", value: 0.02 }],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/analysis"]}>
          <AnalysisPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Run #4" })).toBeInTheDocument();
    expect(clientMocks.getAnalysis).toHaveBeenCalledWith(4);
  });
});
