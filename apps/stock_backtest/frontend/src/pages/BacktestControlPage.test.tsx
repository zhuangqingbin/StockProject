import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { BacktestControlPage } from "./BacktestControlPage";

const clientMocks = vi.hoisted(() => ({
  getRuns: vi.fn(),
  getStrategies: vi.fn(),
  getFeeds: vi.fn(),
  getBenchmarks: vi.fn(),
  getDataOverview: vi.fn(),
  getRuntimeSummary: vi.fn(),
  getRunDiagnostics: vi.fn(),
  submitBacktest: vi.fn(),
}));

vi.mock("../services/client", () => ({
  stockBacktestClient: {
    getRuns: clientMocks.getRuns,
    getStrategies: clientMocks.getStrategies,
    getFeeds: clientMocks.getFeeds,
    getBenchmarks: clientMocks.getBenchmarks,
    getDataOverview: clientMocks.getDataOverview,
    getRuntimeSummary: clientMocks.getRuntimeSummary,
    getRunDiagnostics: clientMocks.getRunDiagnostics,
    submitBacktest: clientMocks.submitBacktest,
  },
}));

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
      <MemoryRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
        <BacktestControlPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("BacktestControlPage", () => {
  beforeEach(() => {
    clientMocks.getStrategies.mockResolvedValue([
      {
        id: 1,
        name: "双均线交叉策略",
        description: "",
        sourceType: "template",
        author: "Qingbin",
        lastRunLabel: "",
        annualReturn: 0.183,
        code: "",
        defaultParams: {},
        requiredFeeds: ["daily_kline"],
      },
    ]);
    clientMocks.getFeeds.mockResolvedValue([{ feedId: "daily_kline", label: "日线行情", description: "基础 OHLCV" }]);
    clientMocks.getBenchmarks.mockResolvedValue([
      { tsCode: "000300.SH", name: "沪深300", latestTradeDate: "2026-02-12" },
      { tsCode: "000905.SH", name: "中证500", latestTradeDate: "2026-02-12" },
    ]);
    clientMocks.getDataOverview.mockResolvedValue({
      symbolCount: 5400,
      industryCount: 90,
      benchmarkCount: 2,
      feedHealth: [
        {
          feedId: "daily_kline",
          label: "日线行情",
          description: "基础 OHLCV",
          tableName: "daily_kline",
          recordCount: 100,
          symbolCount: 2,
          earliestTradeDate: "2025-01-02",
          latestTradeDate: "2026-02-12",
          primary: true,
        },
      ],
      topIndustries: [{ industry: "银行", symbolCount: 20 }],
    });
    clientMocks.getRuns.mockResolvedValue([
      {
        id: 13,
        strategyId: 1,
        title: "双均线交叉策略 #13",
        status: "completed",
        progress: 100,
        range: "2024.01 - 2025.12",
        symbols: ["000001.SZ", "600519.SH"],
        annualReturn: 0.183,
        maxDrawdown: -0.124,
        sharpeRatio: 1.52,
        cacheHit: true,
        reusedFromRunId: 12,
      },
      {
        id: 11,
        strategyId: 3,
        title: "资金流向策略 #11",
        status: "running",
        progress: 67,
        range: "2024.01 - 2025.12",
        symbols: ["000001.SZ", "300750.SZ"],
        annualReturn: 0.221,
        maxDrawdown: -0.091,
        sharpeRatio: 1.68,
        eta: "预计剩余 45 秒",
      },
    ]);
    clientMocks.getRuntimeSummary.mockResolvedValue({
      executionMode: "inline",
      maxWorkers: 2,
      activeRunIds: [11],
      statusCounts: { completed: 1, running: 1, failed: 0 },
      cacheHits: 4,
    });
    clientMocks.getRunDiagnostics.mockResolvedValue({
      runId: 11,
      status: "running",
      requestSignature: "runtime-sig-11",
      cacheHit: false,
      events: [
        { timestamp: "2026-03-15T09:00:00Z", stage: "submitted", message: "任务已提交", progress: 0 },
        { timestamp: "2026-03-15T09:00:01Z", stage: "running", message: "回测任务已开始执行", progress: 5 },
        { timestamp: "2026-03-15T09:00:03Z", stage: "data_loaded", message: "已装载 2 只股票的日线数据", progress: 24 },
      ],
    });
    clientMocks.submitBacktest.mockResolvedValue({ runId: 99, status: "pending", cacheHit: false });
  });

  test("renders the runtime summary surface from the backend contract", async () => {
    renderPage();

    expect(await screen.findByText("执行流场")).toBeInTheDocument();
    expect(screen.getByText("inline")).toBeInTheDocument();
    expect(screen.getByText("2 workers")).toBeInTheDocument();
    expect(await screen.findByText("4 次")).toBeInTheDocument();
  });

  test("renders the active run diagnostics timeline", async () => {
    renderPage();

    expect(await screen.findByText("运行事件 · 资金流向策略 #11")).toBeInTheDocument();
    expect(screen.getByText("回测任务已开始执行")).toBeInTheDocument();
    expect(screen.getByText("已装载 2 只股票的日线数据")).toBeInTheDocument();
    expect(screen.getByText("签名摘要")).toBeInTheDocument();
    expect(screen.queryByText("runtime-sig-11")).not.toBeInTheDocument();
  });

  test("labels cache-hit runs with the reused source run", async () => {
    renderPage();

    expect(await screen.findByText("双均线交叉策略 #13")).toBeInTheDocument();
    expect(screen.getByText("Cache Hit")).toBeInTheDocument();
    expect(screen.getByText("复用 #12")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /双均线交叉策略 #13/i })).toHaveAttribute("href", "/analysis?runId=13");
  });

  test("submits a real launch request from the launch pad", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.clear(await screen.findByLabelText("symbols-input"));
    await user.type(screen.getByLabelText("symbols-input"), "000001.SZ,600519.SH");
    await user.clear(screen.getByLabelText("initial-cash-input"));
    await user.type(screen.getByLabelText("initial-cash-input"), "500000");
    await user.click(screen.getByRole("button", { name: "提交回测" }));

    const [payload] = clientMocks.submitBacktest.mock.calls[0];
    expect(payload).toEqual(
      expect.objectContaining({
        strategyId: 1,
        symbols: ["000001.SZ", "600519.SH"],
        initialCash: 500000,
        benchmark: "000300.SH",
        startDate: "2025-02-12",
        endDate: "2026-02-12",
      }),
    );
    expect(await screen.findByText("任务已提交 · Run #99")).toBeInTheDocument();
  });

  test("shows the real data coverage window and bounds the date inputs", async () => {
    renderPage();

    expect(await screen.findByText("数据覆盖 2025-01-02 至 2026-02-12")).toBeInTheDocument();
    expect(screen.getByLabelText("start-date-input")).toHaveAttribute("min", "2025-01-02");
    expect(screen.getByLabelText("start-date-input")).toHaveAttribute("max", "2026-02-12");
    expect(screen.getByLabelText("end-date-input")).toHaveAttribute("min", "2025-01-02");
    expect(screen.getByLabelText("end-date-input")).toHaveAttribute("max", "2026-02-12");
  });
});
