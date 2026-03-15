import {
  demoAnalysis,
  demoBacktestSubmission,
  demoBenchmarks,
  demoDataOverview,
  demoCompare,
  demoFeeds,
  demoNotebookStatus,
  demoNotebookTemplates,
  demoRunDiagnostics,
  demoRuns,
  demoRuntimeSummary,
  demoStrategies,
  demoTemplates,
  demoUniverse,
} from "./demoData";
import type {
  AnalysisSnapshot,
  BenchmarkRecord,
  BacktestLaunchPayload,
  BacktestSubmission,
  BacktestRunDiagnostics,
  BacktestRuntimeSummary,
  BacktestRun,
  CompareSnapshot,
  DataOverview,
  FeedRecord,
  NotebookStatus,
  NotebookTemplate,
  StrategyRecord,
  StrategyTemplate,
  UniverseRecord,
} from "./types";

const API_BASE = import.meta.env.VITE_STOCK_BACKTEST_API_BASE ?? "";

const requestOrFallback = async <RawResponse, MappedResponse>(
  path: string,
  fallback: MappedResponse,
  transform?: (payload: RawResponse) => MappedResponse,
): Promise<MappedResponse> => {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const payload = (await response.json()) as RawResponse;
    return transform ? transform(payload) : (payload as unknown as MappedResponse);
  } catch {
    return fallback;
  }
};

export const stockBacktestClient = {
  getStrategies: () =>
    requestOrFallback<any[], StrategyRecord[]>("/api/strategies", demoStrategies, (payload) =>
      payload.map((item) => ({
        id: item.id,
        name: item.name,
        description: item.description,
        sourceType: item.source_type,
        templateId: item.template_id ?? undefined,
        author: item.author,
        lastRunLabel: "最近一次回测 已同步到平台",
        annualReturn: 0,
        code: item.code ?? "",
        defaultParams: item.default_params ?? {},
        requiredFeeds: item.required_feeds ?? [],
      })),
    ),
  getTemplates: () =>
    requestOrFallback<any[], StrategyTemplate[]>("/api/strategies/templates", demoTemplates, (payload) =>
      payload.map((item) => ({
        templateId: item.template_id,
        name: item.name,
        description: item.description,
        requiredFeeds: item.required_feeds,
        parameters: item.parameters,
        sourceCode: item.source_code,
      })),
    ),
  getRuns: () =>
    requestOrFallback<any[], BacktestRun[]>("/api/backtest/runs", demoRuns, (payload) =>
      payload.map((item) => ({
        id: item.id,
        strategyId: item.strategy_id,
        title: `策略 #${item.strategy_id} · Run #${item.id}`,
        status: item.status,
        progress: item.progress,
        range: `${item.start_date} → ${item.end_date}`,
        symbols: item.symbols ?? [],
        annualReturn: item.annual_return ?? 0,
        maxDrawdown: item.max_drawdown ?? 0,
        sharpeRatio: item.sharpe_ratio ?? 0,
        cacheHit: item.cache_hit ?? false,
        reusedFromRunId: item.reused_from_run_id ?? undefined,
        errorMessage: item.error_message ?? undefined,
      })),
    ),
  submitBacktest: async (payload: BacktestLaunchPayload) => {
    try {
      const response = await fetch(`${API_BASE}/api/backtest/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          strategy_id: payload.strategyId,
          params: payload.params,
          symbols: payload.symbols,
          start_date: payload.startDate,
          end_date: payload.endDate,
          initial_cash: payload.initialCash,
          commission_rate: payload.commissionRate,
          benchmark: payload.benchmark,
          data_feeds: payload.dataFeeds,
          submitted_by: payload.submittedBy ?? "codex-ui",
        }),
      });
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      const submission = await response.json();
      return {
        runId: submission.run_id,
        status: submission.status,
        cacheHit: submission.cache_hit,
        reusedFromRunId: submission.reused_from_run_id ?? undefined,
      } satisfies BacktestSubmission;
    } catch {
      return demoBacktestSubmission;
    }
  },
  getRuntimeSummary: () =>
    requestOrFallback<any, BacktestRuntimeSummary>("/api/backtest/runtime", demoRuntimeSummary, (payload) => ({
      executionMode: payload.execution_mode,
      maxWorkers: payload.max_workers,
      activeRunIds: payload.active_run_ids ?? [],
      statusCounts: payload.status_counts ?? {},
      cacheHits: payload.cache_hits ?? 0,
    })),
  getRunDiagnostics: (runId: number) =>
    requestOrFallback<any, BacktestRunDiagnostics>(`/api/backtest/runs/${runId}/diagnostics`, demoRunDiagnostics[runId] ?? demoRunDiagnostics[11], (payload) => ({
      runId: payload.run_id,
      status: payload.status,
      requestSignature: payload.request_signature,
      cacheHit: payload.cache_hit,
      reusedFromRunId: payload.reused_from_run_id ?? undefined,
      startedAt: payload.started_at ?? undefined,
      finishedAt: payload.finished_at ?? undefined,
      events: (payload.events ?? []).map((event: any) => ({
        timestamp: event.timestamp,
        stage: event.stage,
        message: event.message,
        progress: event.progress ?? undefined,
      })),
    })),
  getAnalysis: async (runId: number) => {
    try {
      const [run, daily, trades, exposure, rolling, monthly] = await Promise.all([
        fetch(`${API_BASE}/api/backtest/runs/${runId}`).then((response) => response.json()),
        fetch(`${API_BASE}/api/analysis/${runId}/daily`).then((response) => response.json()),
        fetch(`${API_BASE}/api/analysis/${runId}/trades`).then((response) => response.json()),
        fetch(`${API_BASE}/api/analysis/${runId}/industry-exposure`).then((response) => response.json()),
        fetch(`${API_BASE}/api/analysis/${runId}/rolling?metric=sharpe&window=20`).then((response) => response.json()),
        fetch(`${API_BASE}/api/analysis/${runId}/monthly-returns`).then((response) => response.json()),
      ]);

      return {
        runId,
        strategyName: `Run #${run.id}`,
        metrics: {
          totalReturn: run.total_return ?? 0,
          annualReturn: run.annual_return ?? 0,
          maxDrawdown: run.max_drawdown ?? 0,
          sharpeRatio: run.sharpe_ratio ?? 0,
          winRate: run.win_rate ?? 0,
          profitLossRatio: run.profit_loss_ratio ?? 0,
        },
        daily: daily.map((point: any) => ({
          tradeDate: point.trade_date,
          cumulativeReturn: point.cumulative_return,
          drawdown: point.drawdown,
          portfolioValue: point.portfolio_value,
        })),
        trades: trades.map((trade: any) => ({
          tradeDate: trade.trade_date,
          symbol: trade.symbol,
          direction: trade.direction,
          price: trade.price,
          size: trade.size,
          pnl: trade.pnl,
        })),
        industryExposure: exposure.map((item: any) => ({ industry: item.industry, weight: item.weight })),
        rollingSharpe: rolling.map((item: any) => ({ tradeDate: item.trade_date, value: item.value })),
        monthlyReturns: monthly.map((item: any) => ({ month: item.month, value: item.return })),
      } satisfies AnalysisSnapshot;
    } catch {
      return demoAnalysis;
    }
  },
  getCompare: async (runIds: number[]) => {
    if (runIds.length === 0) {
      return demoCompare;
    }
    try {
      const response = await fetch(`${API_BASE}/api/analysis/compare?run_ids=${runIds.join(",")}`);
      const payload = await response.json();
      return {
        runs: payload.runs.map((run: any) => ({
          runId: run.run_id,
          strategyName: `Run #${run.run_id}`,
          annualReturn: run.annual_return,
          maxDrawdown: run.max_drawdown,
          sharpeRatio: run.sharpe_ratio,
          winRate: run.win_rate,
          profitLossRatio: run.profit_loss_ratio,
        })),
        parameterSweep: demoCompare.parameterSweep,
        curves: Object.fromEntries(
          Object.entries(payload.daily_curves).map(([runId, points]) => [
            Number(runId),
            (points as any[]).map((point) => ({
              tradeDate: point.trade_date,
              cumulativeReturn: point.cumulative_return,
            })),
          ]),
        ),
      } satisfies CompareSnapshot;
    } catch {
      return demoCompare;
    }
  },
  getNotebookTemplates: () =>
    requestOrFallback<any[], NotebookTemplate[]>("/api/notebook/templates", demoNotebookTemplates, (payload) =>
      payload.map((template) => ({
        name: template.name,
        label: template.label ?? template.name,
        description: template.description ?? "平台内置模板",
      })),
    ),
  getNotebookStatus: () =>
    requestOrFallback<any, NotebookStatus>("/api/notebook/status", demoNotebookStatus, (payload) => ({
      status: payload.status,
      url: payload.url,
    })),
  startNotebook: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/notebook/start`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      const payload = await response.json();
      return {
        status: payload.status,
        url: payload.url,
      } satisfies NotebookStatus;
    } catch {
      return demoNotebookStatus;
    }
  },
  stopNotebook: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/notebook/stop`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      const payload = await response.json();
      return {
        status: payload.status,
        url: payload.url,
      } satisfies NotebookStatus;
    } catch {
      return demoNotebookStatus;
    }
  },
  getFeeds: () =>
    requestOrFallback<any[], FeedRecord[]>("/api/data/feeds", demoFeeds, (payload) =>
      payload.map((feed) => ({
        feedId: feed.feed_id,
        label: feed.label,
        description: feed.description,
      })),
    ),
  getDataOverview: () =>
    requestOrFallback<any, DataOverview>("/api/data/overview", demoDataOverview, (payload) => ({
      symbolCount: payload.symbol_count,
      industryCount: payload.industry_count,
      benchmarkCount: payload.benchmark_count,
      feedHealth: (payload.feed_health ?? []).map((feed: any) => ({
        feedId: feed.feed_id,
        label: feed.label,
        description: feed.description,
        tableName: feed.table_name,
        recordCount: feed.record_count,
        symbolCount: feed.symbol_count,
        earliestTradeDate: feed.earliest_trade_date ?? undefined,
        latestTradeDate: feed.latest_trade_date ?? undefined,
        primary: feed.primary,
      })),
      topIndustries: (payload.top_industries ?? []).map((item: any) => ({
        industry: item.industry,
        symbolCount: item.symbol_count,
      })),
    })),
  getBenchmarks: () =>
    requestOrFallback<any[], BenchmarkRecord[]>("/api/data/benchmarks", demoBenchmarks, (payload) =>
      payload.map((item) => ({
        tsCode: item.ts_code,
        name: item.name,
        latestTradeDate: item.latest_trade_date ?? undefined,
      })),
    ),
  searchUniverse: (params?: { keyword?: string; industry?: string }) => {
    const search = new URLSearchParams();
    if (params?.keyword) {
      search.set("keyword", params.keyword);
    }
    if (params?.industry) {
      search.set("industry", params.industry);
    }
    const suffix = search.size > 0 ? `?${search.toString()}` : "";
    return requestOrFallback<any[], UniverseRecord[]>(`/api/data/symbols${suffix}`, demoUniverse, (payload) =>
      payload.map((item) => ({
        tsCode: item.ts_code,
        name: item.name,
        industry: item.industry ?? undefined,
        market: item.market ?? undefined,
      })),
    );
  },
};
