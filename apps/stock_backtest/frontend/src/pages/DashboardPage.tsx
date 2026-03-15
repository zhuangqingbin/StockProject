import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { MetricBadge } from "../components/MetricBadge";
import { Surface } from "../components/Surface";
import { stockBacktestClient } from "../services/client";
import { demoBenchmarks, demoDataOverview, demoRuns, demoRuntimeSummary, demoStrategies } from "../services/demoData";

const workflowCards = [
  {
    title: "数据实验室",
    route: "/data",
    description: "先看 feed 覆盖、基准指数和行业结构，再决定是否发射回测。",
  },
  {
    title: "策略工坊",
    route: "/strategies",
    description: "模板仓、参数区和代码编辑器在同一工作面里协同。",
  },
  {
    title: "回测发射台",
    route: "/runs",
    description: "把标的池、参数、基准和数据源一次性锁死后直接提交。",
  },
];

export const DashboardPage = () => {
  const { data: runtimeSummary = demoRuntimeSummary } = useQuery({
    queryKey: ["backtest-runtime"],
    queryFn: stockBacktestClient.getRuntimeSummary,
    initialData: demoRuntimeSummary,
  });
  const { data: runs = demoRuns } = useQuery({
    queryKey: ["runs"],
    queryFn: stockBacktestClient.getRuns,
    initialData: demoRuns,
  });
  const { data: strategies = demoStrategies } = useQuery({
    queryKey: ["strategies"],
    queryFn: stockBacktestClient.getStrategies,
    initialData: demoStrategies,
  });
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

  const activeRuns = runs.filter((run) => run.status === "running" || run.status === "pending");
  const bestStrategy = [...strategies].sort((left, right) => right.annualReturn - left.annualReturn)[0];

  return (
    <div className="stack">
      <Surface eyebrow="Control Tower" title="平台总览">
        <div className="metric-strip">
          <MetricBadge label="活跃任务" tone="warning" value={`${activeRuns.length}`} />
          <MetricBadge label="策略数量" tone="positive" value={`${strategies.length}`} />
          <MetricBadge label="股票覆盖" value={`${dataOverview.symbolCount}`} />
          <MetricBadge label="基准指数" value={`${benchmarks.length}`} />
        </div>
      </Surface>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Workflow Matrix" title="主工作流">
          <div className="workflow-grid">
            {workflowCards.map((card) => (
              <Link className="workflow-card" key={card.route} to={card.route}>
                <span className="workflow-card__index">{card.route.replace("/", "").toUpperCase()}</span>
                <strong>{card.title}</strong>
                <p>{card.description}</p>
              </Link>
            ))}
          </div>
        </Surface>

        <Surface eyebrow="Desk Snapshot" title="当前状态">
          <div className="card-list">
            <div className="micro-card micro-card--wide">
              <span>执行模式</span>
              <strong>{runtimeSummary.executionMode}</strong>
              <p>缓存命中 {runtimeSummary.cacheHits} 次，活跃 run: {runtimeSummary.activeRunIds.join(", ") || "无"}。</p>
            </div>
            <div className="micro-card micro-card--wide">
              <span>最佳策略</span>
              <strong>{bestStrategy?.name ?? "暂无"}</strong>
              <p>{bestStrategy ? `最近年化 ${(bestStrategy.annualReturn * 100).toFixed(1)}%` : "先建立模板，再做回测发射。"}</p>
            </div>
            <div className="micro-card micro-card--wide">
              <span>行业热区</span>
              <strong>{dataOverview.industryCount} 个行业</strong>
              <p>{dataOverview.topIndustries.slice(0, 3).map((item) => item.industry).join(" / ")}</p>
            </div>
          </div>
        </Surface>
      </div>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Feed Coverage" title="数据底座">
          <div className="feed-health-grid">
            {dataOverview.feedHealth.map((feed) => (
              <div className="feed-health-card" key={feed.feedId}>
                <div className="feed-health-card__header">
                  <strong>{feed.label}</strong>
                  {feed.primary ? <span className="feed-pill">Primary</span> : null}
                </div>
                <p>{feed.description}</p>
                <div className="feed-health-card__meta">
                  <span>{feed.tableName}</span>
                  <span>{feed.symbolCount} symbols</span>
                  <span>{feed.latestTradeDate ?? "无更新"}</span>
                </div>
              </div>
            ))}
          </div>
        </Surface>

        <Surface eyebrow="Benchmark Deck" title="基准指数">
          <div className="card-list">
            {benchmarks.map((benchmark) => (
              <div className="micro-card micro-card--wide" key={benchmark.tsCode}>
                <span>{benchmark.tsCode}</span>
                <strong>{benchmark.name}</strong>
                <p>最新交易日 {benchmark.latestTradeDate ?? "未知"}，可直接作为对照基准。</p>
              </div>
            ))}
          </div>
        </Surface>
      </div>
    </div>
  );
};
