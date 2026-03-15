import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Surface } from "../components/Surface";
import { Button, ProgressBar, StatusTag } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { demoBenchmarks, demoDataOverview, demoFeeds, demoRunDiagnostics, demoRuns, demoRuntimeSummary, demoStrategies } from "../services/demoData";

const statusToneMap = {
  pending: "neutral",
  completed: "positive",
  running: "warning",
  failed: "negative",
} as const;

const runtimeToneMap = {
  pending: "neutral",
  completed: "positive",
  running: "warning",
  failed: "negative",
} as const;

const formatEventTime = (value: string) => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

const summarizeSignature = (value: string) => {
  if (value.length <= 12) {
    return value;
  }
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
};

const parseDateValue = (value?: string) => {
  if (!value) {
    return null;
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
};

const deriveDateWindow = (earliestTradeDate?: string, latestTradeDate?: string) => {
  const earliest = parseDateValue(earliestTradeDate);
  const latest = parseDateValue(latestTradeDate);

  if (!latest) {
    return { startDate: "2024-01-01", endDate: "2025-12-31" };
  }

  const start = new Date(latest);
  start.setUTCFullYear(latest.getUTCFullYear() - 1);
  const clampedStart = earliest && start < earliest ? earliest : start;

  return {
    startDate: clampedStart.toISOString().slice(0, 10),
    endDate: latest.toISOString().slice(0, 10),
  };
};

export const BacktestControlPage = () => {
  const queryClient = useQueryClient();
  const [selectedStrategyId, setSelectedStrategyId] = useState(0);
  const [symbolsInput, setSymbolsInput] = useState("000001.SZ,600519.SH");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [datesTouched, setDatesTouched] = useState(false);
  const [benchmark, setBenchmark] = useState("");
  const [initialCashInput, setInitialCashInput] = useState("1000000");
  const [commissionRateInput, setCommissionRateInput] = useState("0.0003");
  const [selectedFeeds, setSelectedFeeds] = useState<string[]>([]);
  const [launchMessage, setLaunchMessage] = useState("");

  const { data: runs = [] } = useQuery({ queryKey: ["runs"], queryFn: stockBacktestClient.getRuns, initialData: demoRuns });
  const { data: strategies = [] } = useQuery({
    queryKey: ["strategies"],
    queryFn: stockBacktestClient.getStrategies,
    initialData: demoStrategies,
  });
  const { data: feeds = [] } = useQuery({ queryKey: ["feeds"], queryFn: stockBacktestClient.getFeeds, initialData: demoFeeds });
  const { data: dataOverview = demoDataOverview } = useQuery({
    queryKey: ["data-overview"],
    queryFn: stockBacktestClient.getDataOverview,
    initialData: demoDataOverview,
  });
  const { data: benchmarks = demoBenchmarks } = useQuery({
    queryKey: ["benchmarks"],
    queryFn: stockBacktestClient.getBenchmarks,
    initialData: demoBenchmarks,
  });
  const { data: runtimeSummary = demoRuntimeSummary } = useQuery({
    queryKey: ["backtest-runtime"],
    queryFn: stockBacktestClient.getRuntimeSummary,
    initialData: demoRuntimeSummary,
  });
  const featuredRun = runs.find((run) => run.status === "running") ?? runs[0];
  const { data: featuredDiagnostics } = useQuery({
    queryKey: ["run-diagnostics", featuredRun?.id],
    queryFn: () => stockBacktestClient.getRunDiagnostics(featuredRun!.id),
    enabled: Boolean(featuredRun),
    initialData: featuredRun ? (demoRunDiagnostics[featuredRun.id] ?? demoRunDiagnostics[11]) : undefined,
  });

  const selectedStrategy = strategies.find((strategy) => strategy.id === selectedStrategyId) ?? strategies[0];
  const activeBenchmark = benchmark || benchmarks[0]?.tsCode || "";
  const activeFeeds = selectedFeeds.length > 0 ? selectedFeeds : selectedStrategy?.requiredFeeds ?? [];
  const primaryDailyFeed = dataOverview.feedHealth.find((feed) => feed.feedId === "daily_kline");
  const coverageStartDate = primaryDailyFeed?.earliestTradeDate;
  const coverageEndDate = primaryDailyFeed?.latestTradeDate ?? benchmarks[0]?.latestTradeDate;
  const coverageCopy =
    coverageStartDate && coverageEndDate ? `数据覆盖 ${coverageStartDate} 至 ${coverageEndDate}` : "当前未检测到完整的日线覆盖范围";

  useEffect(() => {
    if (selectedStrategyId !== 0 || strategies.length === 0) {
      return;
    }
    const preferredStrategy = strategies.find((strategy) => strategy.templateId === "ma_crossover") ?? strategies[0];
    setSelectedStrategyId(preferredStrategy.id);
  }, [selectedStrategyId, strategies]);

  useEffect(() => {
    if (datesTouched) {
      return;
    }
    const window = deriveDateWindow(coverageStartDate, coverageEndDate);
    setStartDate(window.startDate);
    setEndDate(window.endDate);
  }, [coverageEndDate, coverageStartDate, datesTouched]);

  const launchMutation = useMutation({
    mutationFn: stockBacktestClient.submitBacktest,
    onSuccess: async (result) => {
      setLaunchMessage(`任务已提交 · Run #${result.runId}`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["runs"] }),
        queryClient.invalidateQueries({ queryKey: ["backtest-runtime"] }),
      ]);
    },
  });

  const toggleFeed = (feedId: string) => {
    setSelectedFeeds((current) => (current.includes(feedId) ? current.filter((item) => item !== feedId) : [...current, feedId]));
  };

  const handleSubmit = async () => {
    if (!selectedStrategy) {
      return;
    }

    if (startDate > endDate) {
      setLaunchMessage("开始日期不能晚于结束日期。");
      return;
    }
    if (coverageStartDate && startDate < coverageStartDate) {
      setLaunchMessage(`回测开始日期超出可用范围，请调整到 ${coverageStartDate} 之后。`);
      return;
    }
    if (coverageEndDate && endDate > coverageEndDate) {
      setLaunchMessage(`回测结束日期超出可用范围，请调整到 ${coverageEndDate} 之前。`);
      return;
    }

    const parsedSymbols = symbolsInput
      .split(/[,\s]+/)
      .map((symbol) => symbol.trim())
      .filter(Boolean);

    await launchMutation.mutateAsync({
      strategyId: selectedStrategy.id,
      params: selectedStrategy.defaultParams,
      symbols: parsedSymbols,
      startDate,
      endDate,
      initialCash: Number(initialCashInput),
      commissionRate: Number(commissionRateInput),
      benchmark: activeBenchmark,
      dataFeeds: activeFeeds,
      submittedBy: "codex-ui",
    });
  };

  return (
    <div className="stack">
      <Surface eyebrow="Runtime Pulse" title="执行流场">
        <div className="metric-strip">
          <div className="micro-card">
            <span>执行模式</span>
            <strong>{runtimeSummary.executionMode}</strong>
            <p>inline 优先首响应，process 适合重负载隔离。</p>
          </div>
          <div className="micro-card">
            <span>并发上限</span>
            <strong>{runtimeSummary.maxWorkers} workers</strong>
            <p>当前活跃 run: {runtimeSummary.activeRunIds.join(", ") || "无"}</p>
          </div>
          <div className="micro-card">
            <span>缓存命中</span>
            <strong>{runtimeSummary.cacheHits} 次</strong>
            <p>相同参数请求直接复用已完成结果。</p>
          </div>
          <div className="micro-card">
            <span>队列状态</span>
            <strong>{runtimeSummary.statusCounts.running ?? 0} 运行中</strong>
            <p>
              完成 {runtimeSummary.statusCounts.completed ?? 0} · 失败 {runtimeSummary.statusCounts.failed ?? 0}
            </p>
          </div>
        </div>
      </Surface>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Execution Launch" title="回测配置">
          <div className="control-grid">
            <label className="control-field" htmlFor="strategy-select">
              <span>选择策略</span>
              <select className="control-input" id="strategy-select" onChange={(event) => setSelectedStrategyId(Number(event.target.value))} value={selectedStrategy?.id ?? ""}>
                {strategies.map((strategy) => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="control-field" htmlFor="benchmark-select">
              <span>基准指数</span>
              <select className="control-input" id="benchmark-select" onChange={(event) => setBenchmark(event.target.value)} value={activeBenchmark}>
                {benchmarks.map((item) => (
                  <option key={item.tsCode} value={item.tsCode}>
                    {item.name} · {item.tsCode}
                  </option>
                ))}
              </select>
            </label>
            <label className="control-field" htmlFor="start-date-input">
              <span>开始日期</span>
              <input
                aria-label="start-date-input"
                className="control-input"
                id="start-date-input"
                max={coverageEndDate}
                min={coverageStartDate}
                onChange={(event) => {
                  setDatesTouched(true);
                  setStartDate(event.target.value);
                }}
                type="date"
                value={startDate}
              />
            </label>
            <label className="control-field" htmlFor="end-date-input">
              <span>结束日期</span>
              <input
                aria-label="end-date-input"
                className="control-input"
                id="end-date-input"
                max={coverageEndDate}
                min={coverageStartDate}
                onChange={(event) => {
                  setDatesTouched(true);
                  setEndDate(event.target.value);
                }}
                type="date"
                value={endDate}
              />
            </label>
            <div className="control-band control-field--wide">
              <div className="control-band__eyebrow">Market Coverage</div>
              <strong>{coverageCopy}</strong>
              <p>默认回测窗口会锚定到最新交易日，并限制在真实数据覆盖带内。</p>
            </div>
            <label className="control-field control-field--wide" htmlFor="symbols-input">
              <span>标的池</span>
              <textarea
                aria-label="symbols-input"
                className="control-textarea"
                id="symbols-input"
                onChange={(event) => setSymbolsInput(event.target.value)}
                rows={3}
                value={symbolsInput}
              />
            </label>
            <div className="control-field control-field--wide">
              <span>数据源</span>
              <div className="selection-grid">
                {feeds.map((feed) => {
                  const checked = activeFeeds.includes(feed.feedId);
                  return (
                    <label className={`selection-chip${checked ? " selection-chip--active" : ""}`} key={feed.feedId}>
                      <input checked={checked} onChange={() => toggleFeed(feed.feedId)} type="checkbox" />
                      <strong>{feed.label}</strong>
                      <small>{feed.description}</small>
                    </label>
                  );
                })}
              </div>
            </div>
            <label className="control-field" htmlFor="initial-cash-input">
              <span>初始资金</span>
              <input
                aria-label="initial-cash-input"
                className="control-input"
                id="initial-cash-input"
                inputMode="numeric"
                onChange={(event) => setInitialCashInput(event.target.value)}
                value={initialCashInput}
              />
            </label>
            <label className="control-field" htmlFor="commission-rate-input">
              <span>手续费率</span>
              <input
                className="control-input"
                id="commission-rate-input"
                onChange={(event) => setCommissionRateInput(event.target.value)}
                value={commissionRateInput}
              />
            </label>
          </div>
          <div className="launch-row launch-row--form">
            <div>
              <span className="muted-copy">当前模板</span>
              <strong>{selectedStrategy?.templateId ?? "custom"}</strong>
            </div>
            <div>
              <span className="muted-copy">激活 feeds</span>
              <strong>{activeFeeds.join(", ") || "none"}</strong>
            </div>
            <Button onClick={() => void handleSubmit()} size="large">
              提交回测
            </Button>
          </div>
          {launchMessage ? <p className="launch-message">{launchMessage}</p> : null}
        </Surface>

        <Surface eyebrow="Latest Telemetry" title={`运行事件 · ${featuredRun?.title ?? "暂无任务"}`}>
          {featuredDiagnostics ? (
            <div className="diagnostics-panel">
              <div className="runtime-panel">
                <StatusTag tone={runtimeToneMap[featuredDiagnostics.status]}>{featuredDiagnostics.status}</StatusTag>
                {featuredDiagnostics.cacheHit ? <StatusTag tone="accent">Cache Hit</StatusTag> : null}
                {featuredDiagnostics.reusedFromRunId ? <StatusTag tone="neutral">复用 #{featuredDiagnostics.reusedFromRunId}</StatusTag> : null}
              </div>
              <div className="micro-card micro-card--wide">
                <span>签名摘要</span>
                <strong title={featuredDiagnostics.requestSignature}>{summarizeSignature(featuredDiagnostics.requestSignature)}</strong>
                <p>内部去重用的摘要键，不再把完整哈希直接铺在主界面上。</p>
              </div>
              <div className="diagnostics-list">
                {featuredDiagnostics.events.map((event) => (
                  <div className="diagnostics-event" key={`${event.timestamp}-${event.stage}`}>
                    <div className="diagnostics-event__time">{formatEventTime(event.timestamp)}</div>
                    <div className="diagnostics-event__body">
                      <div className="diagnostics-event__meta">
                        <StatusTag tone="neutral">{event.stage}</StatusTag>
                        {typeof event.progress === "number" ? <span>{event.progress}%</span> : null}
                      </div>
                      <strong>{event.message}</strong>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="muted-copy">当前没有可展示的运行诊断事件。</p>
          )}
        </Surface>
      </div>

      <Surface eyebrow="Run Queue" title="回测记录">
        <div className="card-list">
          {runs.map((run) => (
            <Link className="run-card" key={run.id} to={`/analysis?runId=${run.id}`}>
              <div className="run-card__header">
                <strong>{run.title}</strong>
                <div className="run-card__status-row">
                  <StatusTag tone={statusToneMap[run.status]}>{run.status}</StatusTag>
                  {run.cacheHit ? <StatusTag tone="accent">Cache Hit</StatusTag> : null}
                </div>
              </div>
              <p>
                {run.range} · {run.symbols.length} 只股票
              </p>
              {run.reusedFromRunId ? <span className="run-card__cache-copy">复用 #{run.reusedFromRunId}</span> : null}
              {run.status === "running" ? <ProgressBar value={run.progress} /> : null}
              <div className="run-card__footer">
                <span>{run.errorMessage ?? run.eta ?? "执行完成，可进入归因分析"}</span>
                <span>{(run.annualReturn * 100).toFixed(1)}%</span>
              </div>
            </Link>
          ))}
        </div>
      </Surface>
    </div>
  );
};
