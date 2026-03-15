import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ComparisonPage } from "./ComparisonPage";
import { useAnalysisStore } from "../stores/analysisStore";

const clientMocks = vi.hoisted(() => ({
  getRuns: vi.fn(),
  getCompare: vi.fn(),
}));

vi.mock("../services/client", () => ({
  stockBacktestClient: {
    getRuns: clientMocks.getRuns,
    getCompare: clientMocks.getCompare,
  },
}));

const comparePayload = {
  runs: [
    { runId: 4, strategyName: "Run #4", annualReturn: 0.11, maxDrawdown: -0.08, sharpeRatio: 1.2, winRate: 0.6, profitLossRatio: 1.5 },
    { runId: 3, strategyName: "Run #3", annualReturn: 0.09, maxDrawdown: -0.05, sharpeRatio: 1.1, winRate: 0.58, profitLossRatio: 1.4 },
  ],
  parameterSweep: [{ label: "baseline", annualReturn: 0.1 }],
  curves: {
    4: [{ tradeDate: "2025-01-02", cumulativeReturn: 0 }],
    3: [{ tradeDate: "2025-01-02", cumulativeReturn: 0 }],
  },
};

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ComparisonPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("ComparisonPage", () => {
  beforeEach(() => {
    useAnalysisStore.setState({ focusedRunId: 0, comparisonRunIds: [] });
    clientMocks.getRuns.mockResolvedValue([
      { id: 4, strategyId: 6, title: "ATR #4", status: "completed", progress: 100, range: "", symbols: ["000001.SZ"], annualReturn: 0.11, maxDrawdown: -0.08, sharpeRatio: 1.2 },
      { id: 3, strategyId: 3, title: "Flow #3", status: "completed", progress: 100, range: "", symbols: ["000001.SZ"], annualReturn: 0.09, maxDrawdown: -0.05, sharpeRatio: 1.1 },
      { id: 2, strategyId: 1, title: "MA #2", status: "completed", progress: 100, range: "", symbols: ["000001.SZ"], annualReturn: 0.04, maxDrawdown: -0.03, sharpeRatio: 0.9 },
    ]);
    clientMocks.getCompare.mockResolvedValue(comparePayload);
  });

  test("uses the latest available runs instead of hard-coded demo ids", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "策略对比" })).toBeInTheDocument();
    expect(clientMocks.getCompare).toHaveBeenCalledWith([4, 3, 2]);
  });

  test("uses valid store-selected runs when they exist", async () => {
    useAnalysisStore.setState({ focusedRunId: 0, comparisonRunIds: [3, 2] });

    renderPage();

    expect(await screen.findByRole("heading", { name: "策略对比" })).toBeInTheDocument();
    expect(clientMocks.getCompare).toHaveBeenCalledWith([3, 2]);
  });
});
