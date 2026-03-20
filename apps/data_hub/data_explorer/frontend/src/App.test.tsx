import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";
import { useNavigationStore } from "./stores/navigationStore";

const mockApi = vi.hoisted(() => ({
  fetchCategories: vi.fn(),
  fetchTablesByCategory: vi.fn(),
  fetchTableDetail: vi.fn(),
  fetchTablePreview: vi.fn(),
  fetchMonitorOverview: vi.fn(),
  fetchMonitorTables: vi.fn(),
  fetchMonitorJobs: vi.fn(),
  fetchMonitorRuns: vi.fn(),
  fetchDatabaseOverview: vi.fn(),
  fetchTableMetadata: vi.fn(),
}));

vi.mock("./api", () => mockApi);

const renderApp = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: "#1053ff",
            borderRadius: 14,
          },
        }}
      >
        <App />
      </ConfigProvider>
    </QueryClientProvider>,
  );
};

describe("data_explorer app shell", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    useNavigationStore.setState({
      currentPage: "directory",
      selectedCategory: "basic_data",
      selectedTable: null,
      directorySearch: "",
      monitorStatusFilter: "all",
      monitorView: "overview",
      tableDetailTab: "structure",
    });

    mockApi.fetchCategories.mockResolvedValue([
      { key: "basic_data", label: "Basic Data", table_count: 2 },
      { key: "stock_market_data", label: "Stock Market Data", table_count: 1 },
      { key: "runtime", label: "Runtime", table_count: 1 },
    ]);
    mockApi.fetchTablesByCategory.mockImplementation(async (categoryKey: string) => {
      if (categoryKey === "basic_data") {
        return [
          {
            table_name: "stock_basic",
            category: "basic_data",
            description: "A股基础信息",
            api_url: "https://tushare.pro/document/2?doc_id=25",
            row_count: 5400,
            earliest_data_date: "19910403",
            latest_data_date: "20260317",
            last_updated: "2026-03-17T09:25:00",
            status: "normal",
          },
          {
            table_name: "trade_cal",
            category: "basic_data",
            description: "交易日历",
            api_url: "https://tushare.pro/document/2?doc_id=26",
            row_count: 18000,
            earliest_data_date: "19901219",
            latest_data_date: "20260318",
            last_updated: "2026-03-18T08:00:00",
            status: "normal",
          },
        ];
      }

      return [
        {
          table_name: "stock_daily",
          category: "stock_market_data",
          description: "A股日线行情",
          api_url: "https://tushare.pro/document/2?doc_id=27",
          row_count: 5230000,
          earliest_data_date: "19901219",
          latest_data_date: "20260317",
          last_updated: "2026-03-17T18:05:00",
          status: "delayed",
        },
      ];
    });
    mockApi.fetchTableDetail.mockResolvedValue({
      table_name: "stock_basic",
      category: "basic_data",
      description: "A股基础信息",
      api_url: "https://tushare.pro/document/2?doc_id=25",
      job_name: "stock_basic",
      trigger_profile: "reference_calendar_nightly",
      summary: {
        row_count: 5400,
        earliest_data_date: "19910403",
        latest_data_date: "20260317",
        last_updated: "2026-03-17T09:25:00",
        status: "normal",
      },
      structure: {
        columns: [
          {
            name: "ts_code",
            label: "股票代码",
            type: "VARCHAR(16)",
            nullable: false,
            default: null,
            comment: "股票代码",
          },
        ],
        indexes: [{ name: "PRIMARY", columns: ["ts_code"], unique: true, primary: true }],
        constraints: [{ name: "pk_stock_basic", type: "PRIMARY KEY", columns: ["ts_code"] }],
        ddl: "CREATE TABLE `stock_basic` (...)",
      },
      recent_runs: [
        {
          run_id: "run-001",
          run_mode: "once",
          trigger_profile: "reference_calendar_nightly",
          job_name: "stock_basic",
          result: "success",
          effective_date: "20260317",
          executed_at: "2026-03-17 09:25:00",
          duration_seconds: 1.2,
          rows_written: 5400,
          error: null,
        },
      ],
    });
    mockApi.fetchTablePreview.mockResolvedValue({
      table_name: "stock_basic",
      page: 1,
      page_size: 5400,
      total: 5400,
      all_rows: true,
      displayed_rows: 5400,
      truncated: false,
      truncated_limit: 10000,
      columns: ["ts_code", "name", "list_date"],
      data: [{ ts_code: "000001.SZ", name: "平安银行", list_date: "19910403" }],
      filters: {},
    });
    mockApi.fetchMonitorOverview.mockResolvedValue({
      dataset_count: 4,
      fresh_datasets: 2,
      delayed_datasets: 1,
      error_datasets: 0,
      manual_datasets: 1,
      no_data_datasets: 0,
      recent_failed_jobs: 1,
      recent_runs: 2,
      latest_run: {
        run_id: "run-001",
        run_mode: "once",
        status: "partial_failed",
        trigger_profiles: ["trade_day_post_close_core"],
        job_count: 2,
        failed_jobs: 1,
        successful_jobs: 1,
        table_count: 2,
        effective_window: "20260317",
        started_at: "2026-03-17 18:00:00",
        ended_at: "2026-03-17 18:05:00",
      },
    });
    mockApi.fetchMonitorTables.mockResolvedValue([
      {
        table_name: "stock_daily",
        category: "stock_market_data",
        latest_data_date: "20260317",
        last_updated: "2026-03-17T18:05:00",
        freshness: "delayed",
        trigger_profile: "trade_day_post_close_core",
        last_run_result: "failed",
        last_run_id: "run-001",
      },
    ]);
    mockApi.fetchMonitorJobs.mockResolvedValue([
      {
        run_id: "run-001",
        run_mode: "once",
        trigger_profile: "trade_day_post_close_core",
        job_name: "stock_daily",
        table_name: "stock_daily",
        result: "success",
        effective_date: "20260317",
        executed_at: "2026-03-17T18:05:00",
        duration_seconds: 12.3,
        rows_written: 5230000,
        error: null,
      },
    ]);
    mockApi.fetchMonitorRuns.mockResolvedValue([
      {
        run_id: "run-001",
        run_mode: "once",
        status: "partial_failed",
        trigger_profiles: ["trade_day_post_close_core"],
        job_count: 2,
        failed_jobs: 1,
        successful_jobs: 1,
        table_count: 2,
        effective_window: "20260317",
        started_at: "2026-03-17 18:00:00",
        ended_at: "2026-03-17 18:05:00",
      },
    ]);
    mockApi.fetchDatabaseOverview.mockResolvedValue({
      schema_name: "stock_database_v1",
      table_count: 4,
      runtime_table_count: 1,
      category_counts: {
        basic_data: 2,
        stock_market_data: 1,
        runtime: 1,
      },
    });
    mockApi.fetchTableMetadata.mockResolvedValue({
      table_name: "stock_basic",
      columns: [{ name: "ts_code", type: "VARCHAR(16)" }],
      indexes: [{ name: "PRIMARY", columns: ["ts_code"] }],
      constraints: [{ name: "pk_stock_basic", type: "PRIMARY KEY" }],
      ddl: "CREATE TABLE `stock_basic` (...)",
    });
  });

  test("shows the configured site name in the top bar", async () => {
    renderApp();

    expect(await screen.findByRole("heading", { name: "Jimmy发发发" })).toBeInTheDocument();
  });

  test("loads the current category table list, filters within the category, and opens table detail", async () => {
    const user = userEvent.setup();

    renderApp();

    expect(await screen.findByRole("heading", { name: "数据目录" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Basic Data/i })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "最早数据日期" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "查看 stock_basic API 文档" })).toHaveAttribute(
      "href",
      "https://tushare.pro/document/2?doc_id=25",
    );
    expect(screen.getByRole("cell", { name: "19910403" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "查看 trade_cal API 文档" })).toHaveAttribute(
      "href",
      "https://tushare.pro/document/2?doc_id=26",
    );

    await user.type(screen.getByPlaceholderText("搜索当前分类表名或说明"), "基础");

    expect(screen.getByRole("link", { name: "查看 stock_basic API 文档" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "查看 trade_cal API 文档" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("cell", { name: "A股基础信息" }));

    expect(await screen.findByRole("heading", { name: "stock_basic" })).toBeInTheDocument();
    expect(screen.getByText("A股基础信息")).toBeInTheDocument();
    expect(screen.getByText("最早数据日期")).toBeInTheDocument();
    expect(screen.getAllByText("19910403").length).toBeGreaterThan(0);
    expect(screen.getAllByText("触发 Profile").length).toBeGreaterThan(0);
    expect(screen.getAllByText("reference_calendar_nightly").length).toBeGreaterThan(0);
    expect(screen.getByText("Profile 是这张表绑定的数据触发节奏与执行场景。")).toBeInTheDocument();
    expect(screen.getByText("夜间参考数据刷新链路")).toBeInTheDocument();
    expect(screen.getByText("字段结构")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "中文名" })).toBeInTheDocument();
    expect(screen.getAllByRole("cell", { name: "股票代码" }).length).toBeGreaterThan(0);
    expect(screen.getByText("约束信息")).toBeInTheDocument();
  });

  test("shows the full-table mode by default after switching to the all data tab", async () => {
    const user = userEvent.setup();

    renderApp();

    await user.click(await screen.findByRole("cell", { name: "A股基础信息" }));
    await user.click(screen.getByRole("tab", { name: "数据预览" }));

    expect(await screen.findByText("000001.SZ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "显示全部" })).toHaveClass("ant-btn-primary");
    expect(screen.getByText("当前已显示整张表，共 5400 行、3 个字段。")).toBeInTheDocument();
    expect(mockApi.fetchTablePreview).toHaveBeenCalledWith("stock_basic", {
      page: 1,
      pageSize: 50,
      filters: {},
      allRows: true,
    });
  });

  test("shows a truncation notice when the full-table mode is capped at the first 10000 rows", async () => {
    const user = userEvent.setup();

    mockApi.fetchTablePreview.mockResolvedValueOnce({
      table_name: "stock_basic",
      page: 1,
      page_size: 10000,
      total: 12000,
      all_rows: true,
      displayed_rows: 10000,
      truncated: true,
      truncated_limit: 10000,
      columns: ["ts_code", "name", "list_date"],
      data: [{ ts_code: "000001.SZ", name: "平安银行", list_date: "19910403" }],
      filters: {},
    });

    renderApp();

    await user.click(await screen.findByRole("cell", { name: "A股基础信息" }));
    await user.click(screen.getByRole("tab", { name: "数据预览" }));

    expect(
      await screen.findByText("当前表共 12000 行，已截断显示前 10000 行、3 个字段。"),
    ).toBeInTheDocument();
  });

  test("defaults the monitor page to overview and supports drilling into datasets, jobs, and runs", async () => {
    const user = userEvent.setup();

    renderApp();

    await user.click(screen.getByRole("button", { name: "运维监控" }));

    expect(await screen.findByRole("tab", { name: "总览" })).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText("run-001")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "数据资产" }));
    expect(await screen.findByRole("cell", { name: "stock_daily" })).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "任务执行" }));
    expect((await screen.findAllByRole("cell", { name: "stock_daily" })).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("tab", { name: "批次 Runs" }));
    expect(await screen.findByRole("cell", { name: "partial_failed" })).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "数据资产" }));
    await user.click((await screen.findAllByRole("cell", { name: "stock_daily" }))[0]);

    expect(await screen.findByRole("heading", { name: "stock_basic" })).toBeInTheDocument();
  });

  test("renders the database metadata overview and per-table metadata drill-down", async () => {
    const user = userEvent.setup();

    renderApp();

    await user.click(screen.getByRole("button", { name: "数据库元信息" }));

    expect(await screen.findByText("stock_database_v1")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("分类数")).toBeInTheDocument();
    expect(screen.getByText("当前分类表数")).toBeInTheDocument();
    expect(screen.getByText("分类分布")).toBeInTheDocument();
    expect(screen.getByText("表画像")).toBeInTheDocument();
    expect(screen.getByText("字段数")).toBeInTheDocument();
    expect(screen.getByText("索引数")).toBeInTheDocument();
    expect(screen.getByText("约束数")).toBeInTheDocument();

    const metadataPanel = screen.getByRole("region", { name: "metadata-overview" });
    await user.click(within(metadataPanel).getByRole("button", { name: "stock_basic" }));

    expect(await screen.findByText("CREATE TABLE `stock_basic` (...)")).toBeInTheDocument();
    expect(screen.getByText("pk_stock_basic")).toBeInTheDocument();
    expect(screen.getByText("A股基础信息")).toBeInTheDocument();
    expect(screen.queryByText("latest_data_date")).not.toBeInTheDocument();
  });
});
