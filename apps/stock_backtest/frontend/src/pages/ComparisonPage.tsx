import { useQuery } from "@tanstack/react-query";

import { ChartSurface } from "../components/ChartSurface";
import { Surface } from "../components/Surface";
import { DataTable } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { demoCompare } from "../services/demoData";
import { useAnalysisStore } from "../stores/analysisStore";

export const ComparisonPage = () => {
  const { comparisonRunIds } = useAnalysisStore();
  const { data: runs = [] } = useQuery({
    queryKey: ["runs"],
    queryFn: stockBacktestClient.getRuns,
  });
  const validRunIds = new Set(runs.map((run) => run.id));
  const selectedRunIds = comparisonRunIds.filter((runId) => validRunIds.has(runId));
  const activeRunIds = selectedRunIds.length > 0 ? selectedRunIds : runs.slice(0, 3).map((run) => run.id);

  const { data } = useQuery({
    queryKey: ["compare", activeRunIds],
    queryFn: () => stockBacktestClient.getCompare(activeRunIds),
    enabled: activeRunIds.length > 0,
    initialData: activeRunIds.length > 0 ? demoCompare : undefined,
  });

  if (activeRunIds.length === 0) {
    return (
      <div className="stack">
        <Surface eyebrow="Overlay View" title="暂无可对比回测">
          <p className="muted-copy">先生成至少一条成功完成的 run，再进入策略对比。</p>
        </Surface>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const curveMap = data.curves as Record<string, { tradeDate: string; cumulativeReturn: number }[]>;
  const baseCurve = curveMap["12"] ?? Object.values(curveMap)[0] ?? [];

  const option = {
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: baseCurve.map((point: { tradeDate: string; cumulativeReturn: number }) => point.tradeDate),
    },
    yAxis: { type: "value" },
    series: data.runs.map((run: (typeof data.runs)[number]) => ({
      type: "line",
      smooth: true,
      name: run.strategyName,
      data: (curveMap[String(run.runId)] ?? baseCurve).map((point: { tradeDate: string; cumulativeReturn: number }) =>
        Number((point.cumulativeReturn * 100).toFixed(2)),
      ),
    })),
  };

  const sweepOption = {
    xAxis: { type: "category", data: data.parameterSweep.map((item) => item.label) },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: data.parameterSweep.map((item) => Number((item.annualReturn * 100).toFixed(1))),
        itemStyle: { color: "#6fd4b1" },
      },
    ],
  };

  return (
    <div className="stack">
      <Surface eyebrow="Overlay View" title="策略对比">
        <ChartSurface option={option} title="策略收益叠加" />
      </Surface>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Rank Sheet" title="指标对比">
          <DataTable<(typeof data.runs)[number]>
            columns={[
              { key: "strategyName", title: "策略", dataIndex: "strategyName" },
              { key: "annualReturn", title: "年化收益", render: (record) => `${(record.annualReturn * 100).toFixed(1)}%` },
              { key: "maxDrawdown", title: "最大回撤", render: (record) => `${(record.maxDrawdown * 100).toFixed(1)}%` },
              { key: "sharpeRatio", title: "夏普", dataIndex: "sharpeRatio" },
              { key: "winRate", title: "胜率", render: (record) => `${(record.winRate * 100).toFixed(1)}%` },
            ]}
            data={data.runs}
            rowKey="runId"
          />
        </Surface>

        <Surface eyebrow="Sensitivity" title="参数敏感性">
          <ChartSurface option={sweepOption} title="参数敏感性" />
        </Surface>
      </div>
    </div>
  );
};
