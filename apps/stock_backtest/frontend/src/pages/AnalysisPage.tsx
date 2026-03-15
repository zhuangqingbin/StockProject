import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import { ChartSurface } from "../components/ChartSurface";
import { MetricBadge } from "../components/MetricBadge";
import { Surface } from "../components/Surface";
import { DataTable, Tabs } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { useAnalysisStore } from "../stores/analysisStore";
import type { TradeRecord } from "../services/types";

export const AnalysisPage = () => {
  const [searchParams] = useSearchParams();
  const { focusedRunId, setFocusedRunId } = useAnalysisStore();
  const { data: runs = [] } = useQuery({
    queryKey: ["runs"],
    queryFn: stockBacktestClient.getRuns,
  });
  const requestedRunId = Number(searchParams.get("runId"));
  const runIds = new Set(runs.map((run) => run.id));
  const hasRequestedRunId = Number.isFinite(requestedRunId) && requestedRunId > 0;
  const activeRunId = hasRequestedRunId ? requestedRunId : runIds.has(focusedRunId) ? focusedRunId : runs[0]?.id;

  useEffect(() => {
    if (activeRunId && activeRunId !== focusedRunId) {
      setFocusedRunId(activeRunId);
    }
  }, [activeRunId, focusedRunId, setFocusedRunId]);

  const { data = undefined } = useQuery({
    queryKey: ["analysis", activeRunId],
    queryFn: () => stockBacktestClient.getAnalysis(activeRunId),
    enabled: Boolean(activeRunId),
  });

  if (!activeRunId) {
    return (
      <div className="stack">
        <Surface eyebrow="Result Atlas" title="暂无可分析回测">
          <p className="muted-copy">先在回测发射台提交一条成功完成的 run，再进入结果分析。</p>
        </Surface>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const returnOption = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.daily.map((point: (typeof data.daily)[number]) => point.tradeDate) },
    yAxis: { type: "value", axisLabel: { formatter: "{value}%" } },
    series: [
      {
        type: "line",
        smooth: true,
        data: data.daily.map((point: (typeof data.daily)[number]) => Number((point.cumulativeReturn * 100).toFixed(2))),
        lineStyle: { color: "#d38a59", width: 3 },
        areaStyle: { color: "rgba(211, 138, 89, 0.18)" },
      },
    ],
  };

  const drawdownOption = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.daily.map((point: (typeof data.daily)[number]) => point.tradeDate) },
    yAxis: { type: "value", axisLabel: { formatter: "{value}%" } },
    series: [
      {
        type: "bar",
        data: data.daily.map((point: (typeof data.daily)[number]) => Number((point.drawdown * 100).toFixed(2))),
        itemStyle: { color: "#d65f5f" },
      },
    ],
  };

  return (
    <div className="stack">
      <Surface eyebrow="Result Atlas" title={data.strategyName}>
        <div className="metric-strip">
          <MetricBadge label="总收益" tone="positive" value={`${(data.metrics.totalReturn * 100).toFixed(1)}%`} />
          <MetricBadge label="年化收益" tone="positive" value={`${(data.metrics.annualReturn * 100).toFixed(1)}%`} />
          <MetricBadge label="最大回撤" tone="warning" value={`${(data.metrics.maxDrawdown * 100).toFixed(1)}%`} />
          <MetricBadge label="夏普比率" value={data.metrics.sharpeRatio.toFixed(2)} />
          <MetricBadge label="胜率" value={`${(data.metrics.winRate * 100).toFixed(1)}%`} />
          <MetricBadge label="盈亏比" value={data.metrics.profitLossRatio.toFixed(2)} />
        </div>
      </Surface>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Equity Curve" title="收益曲线">
          <ChartSurface option={returnOption} title="收益曲线" />
        </Surface>
        <Surface eyebrow="Risk Map" title="回撤轨迹">
          <ChartSurface option={drawdownOption} title="回撤轨迹" />
        </Surface>
      </div>

        <Surface eyebrow="Drill Down" title="交易与归因">
          <Tabs
            defaultActiveKey="trades"
            items={[
              {
                key: "trades",
                label: "交易明细",
                children: (
                  <DataTable<TradeRecord>
                    columns={[
                      { key: "tradeDate", title: "日期", dataIndex: "tradeDate" },
                      { key: "symbol", title: "标的", dataIndex: "symbol" },
                      { key: "direction", title: "方向", dataIndex: "direction" },
                      { key: "price", title: "价格", dataIndex: "price" },
                      { key: "size", title: "数量", dataIndex: "size" },
                      { key: "pnl", title: "盈亏", dataIndex: "pnl" },
                    ]}
                    data={data.trades}
                    rowKey={(record) => `${record.tradeDate}-${record.symbol}-${record.direction}`}
                  />
                ),
            },
            {
              key: "exposure",
              label: "行业暴露",
              children: (
                <div className="pill-row">
                  {data.industryExposure.map((item: (typeof data.industryExposure)[number]) => (
                    <span className="feed-pill" key={item.industry}>
                      {item.industry} {(item.weight * 100).toFixed(0)}%
                    </span>
                  ))}
                </div>
              ),
            },
            {
              key: "rolling",
              label: "滚动指标",
              children: (
                <div className="card-list card-list--compact">
                  {data.rollingSharpe.map((item: (typeof data.rollingSharpe)[number]) => (
                    <div className="micro-card" key={item.tradeDate}>
                      <span>{item.tradeDate}</span>
                      <strong>{item.value.toFixed(2)}</strong>
                    </div>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </Surface>
    </div>
  );
};
