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
  FeedHealthRecord,
  IndustryCoverage,
  NotebookStatus,
  NotebookTemplate,
  StrategyRecord,
  StrategyTemplate,
  UniverseRecord,
} from "./types";

const sharedCode = `class Strategy(bt.Strategy):
    params = (("fast_period", 5), ("slow_period", 20))

    def __init__(self):
        self.fast = bt.ind.SMA(period=self.params.fast_period)
        self.slow = bt.ind.SMA(period=self.params.slow_period)
        self.crossover = bt.ind.CrossOver(self.fast, self.slow)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()
`;

export const demoStrategies: StrategyRecord[] = [
  {
    id: 1,
    name: "双均线交叉策略",
    description: "利用短长均线的趋势切换管理仓位，适合做稳健的趋势跟随。",
    sourceType: "template",
    templateId: "ma_crossover",
    author: "Qingbin",
    lastRunLabel: "最近一次回测 2026-03-14",
    annualReturn: 0.183,
    code: sharedCode,
    defaultParams: { fast_period: 5, slow_period: 20, stop_loss: "5%" },
    requiredFeeds: ["daily_kline"],
  },
  {
    id: 2,
    name: "连涨突破策略",
    description: "聚焦连续强势后的确认突破，强调节奏与加速段。",
    sourceType: "custom",
    author: "Circle Lab",
    lastRunLabel: "最近一次回测 2026-03-12",
    annualReturn: 0.127,
    code: sharedCode,
    defaultParams: { lookback: 20, breakout_pct: "3%", hold_days: 8 },
    requiredFeeds: ["daily_kline"],
  },
  {
    id: 3,
    name: "资金流向策略",
    description: "把主力净流向和价格趋势叠在一起，适合快速筛选事件性机会。",
    sourceType: "custom",
    author: "Circle Lab",
    lastRunLabel: "最近一次回测 2026-03-10",
    annualReturn: 0.091,
    code: sharedCode,
    defaultParams: { flow_threshold: 5000, hold_days: 5, net_flow_type: "主力净流入" },
    requiredFeeds: ["daily_kline", "moneyflow"],
  },
];

export const demoTemplates: StrategyTemplate[] = [
  {
    templateId: "ma_crossover",
    name: "均线交叉",
    description: "最适合用来验证行情数据完整性和执行节奏。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      fast_period: { type: "int", default: 5, min: 2, max: 20 },
      slow_period: { type: "int", default: 20, min: 10, max: 120 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "breakout",
    name: "突破策略",
    description: "适合偏主动的趋势加速阶段。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      lookback: { type: "int", default: 20, min: 5, max: 80 },
      exit_period: { type: "int", default: 10, min: 3, max: 40 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "mean_reversion",
    name: "均值回归",
    description: "低位反弹的回撤修复器。",
    requiredFeeds: ["daily_kline", "daily_basic"],
    parameters: {
      period: { type: "int", default: 20, min: 5, max: 60 },
      devfactor: { type: "float", default: 2, min: 1, max: 4 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "rsi_rotation",
    name: "RSI 反转",
    description: "RSI 跌入超卖区后低吸，反弹到强势区间离场。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      rsi_period: { type: "int", default: 14, min: 5, max: 40 },
      lower_band: { type: "float", default: 30, min: 10, max: 45 },
      upper_band: { type: "float", default: 58, min: 40, max: 85 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "bollinger_reversion",
    name: "布林回补",
    description: "跌破下轨后等待价格回到中轨，适合回撤修复型行情。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      period: { type: "int", default: 18, min: 5, max: 60 },
      devfactor: { type: "float", default: 2.2, min: 1, max: 4 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "volume_breakout",
    name: "放量突破",
    description: "量价共振时入场，偏趋势延续。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      lookback: { type: "int", default: 30, min: 5, max: 120 },
      volume_period: { type: "int", default: 10, min: 3, max: 40 },
      volume_multiplier: { type: "float", default: 1.8, min: 1, max: 5 },
    },
    sourceCode: sharedCode,
  },
  {
    templateId: "atr_trend_following",
    name: "ATR 趋势跟随",
    description: "趋势跟随 + 波动止损，适合把回撤纪律写进模板。",
    requiredFeeds: ["daily_kline"],
    parameters: {
      trend_period: { type: "int", default: 30, min: 5, max: 120 },
      atr_period: { type: "int", default: 14, min: 5, max: 40 },
      atr_multiplier: { type: "float", default: 2.5, min: 1, max: 6 },
    },
    sourceCode: sharedCode,
  },
];

export const demoRuns: BacktestRun[] = [
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
    id: 12,
    strategyId: 1,
    title: "双均线交叉策略 #12",
    status: "completed",
    progress: 100,
    range: "2024.01 - 2025.12",
    symbols: ["000001.SZ", "600519.SH"],
    annualReturn: 0.183,
    maxDrawdown: -0.124,
    sharpeRatio: 1.52,
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
  {
    id: 10,
    strategyId: 2,
    title: "连涨突破策略 #10",
    status: "completed",
    progress: 100,
    range: "2023.01 - 2025.12",
    symbols: ["002594.SZ", "300308.SZ"],
    annualReturn: 0.127,
    maxDrawdown: -0.142,
    sharpeRatio: 1.1,
  },
  {
    id: 9,
    strategyId: 1,
    title: "双均线交叉策略 #9",
    status: "failed",
    progress: 100,
    range: "2019.01 - 2025.12",
    symbols: ["000688.SH"],
    annualReturn: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    errorMessage: "数据不足：000688.SH 在 2019 年无可用日线。",
  },
];

const curve = [
  { tradeDate: "2025-01-02", cumulativeReturn: 0.0, drawdown: 0.0, portfolioValue: 1000000 },
  { tradeDate: "2025-01-09", cumulativeReturn: 0.028, drawdown: -0.012, portfolioValue: 1028000 },
  { tradeDate: "2025-01-16", cumulativeReturn: 0.045, drawdown: -0.01, portfolioValue: 1045000 },
  { tradeDate: "2025-01-23", cumulativeReturn: 0.072, drawdown: -0.021, portfolioValue: 1072000 },
  { tradeDate: "2025-01-30", cumulativeReturn: 0.094, drawdown: -0.018, portfolioValue: 1094000 },
  { tradeDate: "2025-02-06", cumulativeReturn: 0.131, drawdown: -0.026, portfolioValue: 1131000 },
  { tradeDate: "2025-02-13", cumulativeReturn: 0.163, drawdown: -0.015, portfolioValue: 1163000 },
  { tradeDate: "2025-02-20", cumulativeReturn: 0.183, drawdown: -0.009, portfolioValue: 1183000 },
];

export const demoAnalysis: AnalysisSnapshot = {
  runId: 12,
  strategyName: "双均线交叉策略",
  metrics: {
    totalReturn: 0.367,
    annualReturn: 0.183,
    maxDrawdown: -0.124,
    sharpeRatio: 1.52,
    winRate: 0.625,
    profitLossRatio: 1.88,
  },
  daily: curve,
  trades: [
    { tradeDate: "2025-01-08", symbol: "000001.SZ", direction: "buy", price: 10.26, size: 1200, pnl: 0 },
    { tradeDate: "2025-01-29", symbol: "000001.SZ", direction: "sell", price: 11.84, size: 1200, pnl: 1896 },
    { tradeDate: "2025-02-03", symbol: "600519.SH", direction: "buy", price: 1458.5, size: 100, pnl: 0 },
    { tradeDate: "2025-02-19", symbol: "600519.SH", direction: "sell", price: 1528.9, size: 100, pnl: 7040 },
  ],
  industryExposure: [
    { industry: "银行", weight: 0.42 },
    { industry: "白酒", weight: 0.33 },
    { industry: "新能源", weight: 0.25 },
  ],
  rollingSharpe: curve.map((point, index) => ({
    tradeDate: point.tradeDate,
    value: Number((0.92 + index * 0.08).toFixed(2)),
  })),
  monthlyReturns: [
    { month: "2025-01", value: 0.094 },
    { month: "2025-02", value: 0.081 },
    { month: "2025-03", value: 0.054 },
  ],
};

export const demoRuntimeSummary: BacktestRuntimeSummary = {
  executionMode: "inline",
  maxWorkers: 2,
  activeRunIds: [11],
  statusCounts: {
    completed: 3,
    running: 1,
    failed: 1,
  },
  cacheHits: 7,
};

export const demoBenchmarks: BenchmarkRecord[] = [
  { tsCode: "000300.SH", name: "沪深300", latestTradeDate: "2025-02-10" },
  { tsCode: "000905.SH", name: "中证500", latestTradeDate: "2025-02-10" },
  { tsCode: "399006.SZ", name: "创业板指", latestTradeDate: "2025-02-10" },
];

export const demoFeedHealth: FeedHealthRecord[] = [
  {
    feedId: "daily_kline",
    label: "日线行情",
    description: "基础 OHLCV 日线行情",
    tableName: "daily_kline",
    recordCount: 1805234,
    symbolCount: 5321,
    earliestTradeDate: "2024-02-10",
    latestTradeDate: "2025-02-10",
    primary: true,
  },
  {
    feedId: "daily_basic",
    label: "基本面",
    description: "估值和换手率日频指标",
    tableName: "daily_basic",
    recordCount: 1744021,
    symbolCount: 5308,
    earliestTradeDate: "2024-02-10",
    latestTradeDate: "2025-02-10",
  },
  {
    feedId: "moneyflow",
    label: "资金流",
    description: "主力资金净流入等信号",
    tableName: "moneyflow",
    recordCount: 1563002,
    symbolCount: 5012,
    earliestTradeDate: "2024-02-10",
    latestTradeDate: "2025-02-10",
  },
];

export const demoTopIndustries: IndustryCoverage[] = [
  { industry: "银行", symbolCount: 46 },
  { industry: "白酒", symbolCount: 22 },
  { industry: "新能源", symbolCount: 131 },
  { industry: "算力", symbolCount: 88 },
  { industry: "半导体", symbolCount: 109 },
  { industry: "医药", symbolCount: 142 },
];

export const demoDataOverview: DataOverview = {
  symbolCount: 5321,
  industryCount: 94,
  benchmarkCount: 3,
  feedHealth: demoFeedHealth,
  topIndustries: demoTopIndustries,
};

export const demoUniverse: UniverseRecord[] = [
  { tsCode: "000001.SZ", name: "平安银行", industry: "银行", market: "主板" },
  { tsCode: "600519.SH", name: "贵州茅台", industry: "白酒", market: "主板" },
  { tsCode: "300750.SZ", name: "宁德时代", industry: "新能源", market: "创业板" },
  { tsCode: "002594.SZ", name: "比亚迪", industry: "新能源", market: "主板" },
];

export const demoBacktestSubmission: BacktestSubmission = {
  runId: 99,
  status: "pending",
  cacheHit: false,
};

export const demoRunDiagnostics: Record<number, BacktestRunDiagnostics> = {
  11: {
    runId: 11,
    status: "running",
    requestSignature: "demo-runtime-sig-11",
    cacheHit: false,
    startedAt: "2026-03-15T09:00:01Z",
    events: [
      { timestamp: "2026-03-15T09:00:00Z", stage: "submitted", message: "任务已提交", progress: 0 },
      { timestamp: "2026-03-15T09:00:01Z", stage: "running", message: "回测任务已开始执行", progress: 5 },
      { timestamp: "2026-03-15T09:00:03Z", stage: "data_loaded", message: "已装载 2 只股票的日线数据", progress: 24 },
      { timestamp: "2026-03-15T09:00:11Z", stage: "running", message: "组合指标正在滚动计算", progress: 67 },
    ],
  },
  13: {
    runId: 13,
    status: "completed",
    requestSignature: "demo-runtime-sig-13",
    cacheHit: true,
    reusedFromRunId: 12,
    startedAt: "2026-03-15T08:30:00Z",
    finishedAt: "2026-03-15T08:30:01Z",
    events: [
      { timestamp: "2026-03-15T08:30:00Z", stage: "submitted", message: "任务已提交", progress: 0 },
      { timestamp: "2026-03-15T08:30:01Z", stage: "cache_hit", message: "检测到相同参数，直接复用已完成结果", progress: 100 },
      { timestamp: "2026-03-15T08:30:01Z", stage: "completed", message: "结果复用完成，可直接进入分析", progress: 100 },
    ],
  },
};

export const demoCompare: CompareSnapshot = {
  runs: [
    { runId: 12, strategyName: "双均线交叉", annualReturn: 0.183, maxDrawdown: -0.124, sharpeRatio: 1.52, winRate: 0.625, profitLossRatio: 1.88 },
    { runId: 10, strategyName: "连涨突破", annualReturn: 0.127, maxDrawdown: -0.142, sharpeRatio: 1.1, winRate: 0.57, profitLossRatio: 1.43 },
    { runId: 11, strategyName: "资金流向", annualReturn: 0.221, maxDrawdown: -0.091, sharpeRatio: 1.68, winRate: 0.61, profitLossRatio: 1.95 },
  ],
  parameterSweep: [
    { label: "3 日", annualReturn: 0.112 },
    { label: "5 日", annualReturn: 0.183 },
    { label: "8 日", annualReturn: 0.206 },
    { label: "10 日", annualReturn: 0.171 },
    { label: "15 日", annualReturn: 0.129 },
  ],
  curves: {
    12: curve.map((point) => ({ tradeDate: point.tradeDate, cumulativeReturn: point.cumulativeReturn })),
    10: curve.map((point, index) => ({ tradeDate: point.tradeDate, cumulativeReturn: point.cumulativeReturn * (0.72 + index * 0.01) })),
    11: curve.map((point, index) => ({ tradeDate: point.tradeDate, cumulativeReturn: point.cumulativeReturn * (1.06 + index * 0.012) })),
  },
};

export const demoNotebookTemplates: NotebookTemplate[] = [
  { name: "strategy_dev_template.ipynb", label: "策略开发模板", description: "内置行情接入、策略草稿和快速可视化单元。" },
  { name: "data_explore_template.ipynb", label: "数据探索模板", description: "检查字段、回溯缺口和做数据可信度抽样。" },
  { name: "result_analysis_template.ipynb", label: "结果分析模板", description: "把单次回测拉进 Notebook 做深挖和复盘。" },
];

export const demoNotebookStatus: NotebookStatus = {
  status: "stopped",
  url: null,
};

export const demoFeeds: FeedRecord[] = [
  { feedId: "daily_kline", label: "日线行情", description: "OHLCV 与成交额主序列" },
  { feedId: "daily_basic", label: "基本面", description: "换手率、估值和基础派生指标" },
  { feedId: "moneyflow", label: "资金流", description: "主力和超大单净流向" },
  { feedId: "top_list", label: "龙虎榜", description: "异常活跃标的的席位摘要" },
];
