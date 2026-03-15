export type StrategyRecord = {
  id: number;
  name: string;
  description: string;
  sourceType: "template" | "custom";
  templateId?: string;
  author: string;
  lastRunLabel: string;
  annualReturn: number;
  code: string;
  defaultParams: Record<string, number | string>;
  requiredFeeds: string[];
};

export type StrategyTemplate = {
  templateId: string;
  name: string;
  description: string;
  requiredFeeds: string[];
  parameters: Record<string, { type: string; default: number | string; min?: number; max?: number }>;
  sourceCode: string;
};

export type BacktestRun = {
  id: number;
  strategyId: number;
  title: string;
  status: "pending" | "completed" | "running" | "failed";
  progress: number;
  range: string;
  symbols: string[];
  annualReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  cacheHit?: boolean;
  reusedFromRunId?: number;
  errorMessage?: string;
  eta?: string;
};

export type BacktestRunEvent = {
  timestamp: string;
  stage: string;
  message: string;
  progress?: number;
};

export type BacktestRunDiagnostics = {
  runId: number;
  status: BacktestRun["status"];
  requestSignature: string;
  cacheHit: boolean;
  reusedFromRunId?: number;
  startedAt?: string;
  finishedAt?: string;
  events: BacktestRunEvent[];
};

export type BacktestRuntimeSummary = {
  executionMode: string;
  maxWorkers: number;
  activeRunIds: number[];
  statusCounts: Record<string, number>;
  cacheHits: number;
};

export type BacktestLaunchPayload = {
  strategyId: number;
  params: Record<string, number | string>;
  symbols: string[];
  startDate: string;
  endDate: string;
  initialCash: number;
  commissionRate: number;
  benchmark: string;
  dataFeeds: string[];
  submittedBy?: string;
};

export type BacktestSubmission = {
  runId: number;
  status: BacktestRun["status"];
  cacheHit: boolean;
  reusedFromRunId?: number;
};

export type DailyPoint = {
  tradeDate: string;
  cumulativeReturn: number;
  drawdown: number;
  portfolioValue: number;
};

export type TradeRecord = {
  tradeDate: string;
  symbol: string;
  direction: "buy" | "sell";
  price: number;
  size: number;
  pnl: number;
};

export type AnalysisSnapshot = {
  runId: number;
  strategyName: string;
  metrics: {
    totalReturn: number;
    annualReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number;
    profitLossRatio: number;
  };
  daily: DailyPoint[];
  trades: TradeRecord[];
  industryExposure: { industry: string; weight: number }[];
  rollingSharpe: { tradeDate: string; value: number }[];
  monthlyReturns: { month: string; value: number }[];
};

export type CompareSnapshot = {
  runs: {
    runId: number;
    strategyName: string;
    annualReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number;
    profitLossRatio: number;
  }[];
  parameterSweep: { label: string; annualReturn: number }[];
  curves: Record<number, { tradeDate: string; cumulativeReturn: number }[]>;
};

export type NotebookTemplate = {
  name: string;
  label: string;
  description: string;
};

export type NotebookStatus = {
  status: "running" | "stopped" | "unavailable";
  url: string | null;
};

export type FeedRecord = {
  feedId: string;
  label: string;
  description: string;
};

export type FeedHealthRecord = FeedRecord & {
  tableName: string;
  recordCount: number;
  symbolCount: number;
  earliestTradeDate?: string;
  latestTradeDate?: string;
  primary?: boolean;
};

export type IndustryCoverage = {
  industry: string;
  symbolCount: number;
};

export type DataOverview = {
  symbolCount: number;
  industryCount: number;
  benchmarkCount: number;
  feedHealth: FeedHealthRecord[];
  topIndustries: IndustryCoverage[];
};

export type BenchmarkRecord = {
  tsCode: string;
  name: string;
  latestTradeDate?: string;
};

export type UniverseRecord = {
  tsCode: string;
  name: string;
  industry?: string;
  market?: string;
};
