import { lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchAmountTrend, fetchNorthMoneyTrend, fetchRanking } from "../../lib/api/marketApi";
import type { SummaryResponse } from "../../lib/api/types";
import { useDashboardStore } from "../../lib/state/dashboardStore";
import { useScrollActivatedVisibility } from "../../lib/viewport/useScrollActivatedVisibility";
import { EmptyState, LoadingBlock, SegmentedControl, SelectField, Surface } from "../../ui";
const DistributionChart = lazy(() =>
  import("./DistributionChart").then((module) => ({ default: module.DistributionChart })),
);
const IndustryTreemap = lazy(() =>
  import("./IndustryTreemap").then((module) => ({ default: module.IndustryTreemap })),
);
const RankingTreemap = lazy(() =>
  import("./RankingTreemap").then((module) => ({ default: module.RankingTreemap })),
);

const NorthTrendChart = lazy(() =>
  import("./NorthTrendChart").then((module) => ({ default: module.NorthTrendChart })),
);
const AmountTrendChart = lazy(() =>
  import("./AmountTrendChart").then((module) => ({ default: module.AmountTrendChart })),
);

const TrendFallback = () => (
  <Surface className="trend-card">
    <LoadingBlock rows={5} />
  </Surface>
);

const StageFallback = () => <LoadingBlock rows={8} />;

interface ChartStageProps {
  summary: SummaryResponse;
}

export const ChartStage = ({ summary }: ChartStageProps) => {
  const view = useDashboardStore((state) => state.view);
  const topN = useDashboardStore((state) => state.topN);
  const order = useDashboardStore((state) => state.order);
  const rankingSortBy = useDashboardStore((state) => state.rankingSortBy);
  const setView = useDashboardStore((state) => state.setView);
  const setTopN = useDashboardStore((state) => state.setTopN);
  const setOrder = useDashboardStore((state) => state.setOrder);
  const setRankingSortBy = useDashboardStore((state) => state.setRankingSortBy);
  const setActiveStock = useDashboardStore((state) => state.setActiveStock);
  const setActiveIndustry = useDashboardStore((state) => state.setActiveIndustry);
  const { containerRef, trendReady } = useScrollActivatedVisibility<HTMLDivElement>();

  const rankingQuery = useQuery({
    queryKey: ["market", "ranking", rankingSortBy, order, topN],
    queryFn: () => fetchRanking({ sortBy: rankingSortBy, order, top: topN }),
    enabled: view === "ranking",
  });
  const northTrendQuery = useQuery({
    queryKey: ["market", "north-trend"],
    queryFn: fetchNorthMoneyTrend,
    enabled: trendReady,
  });
  const amountTrendQuery = useQuery({
    queryKey: ["market", "amount-trend"],
    queryFn: fetchAmountTrend,
    enabled: trendReady,
  });

  const rankingStocks =
    rankingQuery.data?.stocks ??
    (order === "desc" ? summary.top_gainers.slice(0, topN) : summary.top_losers.slice(0, topN));

  return (
    <section className="chart-stage" data-testid="chart-stage">
      <Surface className="chart-stage__main">
        <div className="chart-stage__header">
          <div className="chart-stage__heading">
            <span className="section-kicker">Signal Atlas</span>
            <h2 className="chart-stage__title">Visual Briefing</h2>
            <p className="chart-stage__summary">在广度、行业热力和排行榜之间切换，快速定位今天的结构变化。</p>
          </div>
          <div className="chart-stage__controls">
            <SegmentedControl
              value={view}
              onChange={setView}
              options={[
                { label: "涨跌分布", value: "distribution" },
                { label: "行业热力", value: "industry" },
                { label: "排行热力", value: "ranking" },
              ]}
            />
            <SelectField
              value={topN}
              onChange={setTopN}
              minWidth={110}
              options={[10, 15, 20, 30].map((value) => ({ label: `Top ${value}`, value }))}
            />
            {view === "ranking" ? (
              <>
                <SelectField
                  value={rankingSortBy}
                  onChange={setRankingSortBy}
                  minWidth={130}
                  options={[
                    { label: "涨跌幅", value: "pct_chg" },
                    { label: "成交额", value: "amount" },
                    { label: "换手率", value: "turnover" },
                  ]}
                />
                <SegmentedControl
                  value={order}
                  onChange={setOrder}
                  options={[
                    { label: "强势", value: "desc" },
                    { label: "回撤", value: "asc" },
                  ]}
                />
              </>
            ) : null}
          </div>
        </div>
        {view === "distribution" ? (
          summary.pct_distribution.length ? (
            <Suspense fallback={<StageFallback />}>
              <DistributionChart data={summary.pct_distribution} />
            </Suspense>
          ) : (
            <EmptyState description="暂无涨跌分布数据" />
          )
        ) : null}
        {view === "industry" ? (
          summary.industry_ranking.length ? (
            <Suspense fallback={<StageFallback />}>
              <IndustryTreemap
                data={summary.industry_ranking}
                topN={topN}
                onSelectIndustry={setActiveIndustry}
              />
            </Suspense>
          ) : (
            <EmptyState description="暂无行业热力数据" />
          )
        ) : null}
        {view === "ranking" ? (
          rankingStocks.length ? (
            <Suspense fallback={<StageFallback />}>
              <RankingTreemap
                data={rankingStocks}
                order={order}
                topN={topN}
                onSelectStock={setActiveStock}
              />
            </Suspense>
          ) : (
            <EmptyState description="暂无排行热力数据" />
          )
        ) : null}
      </Surface>
      <div ref={containerRef} className="chart-stage__side">
        {trendReady ? (
          <>
            {northTrendQuery.isLoading || amountTrendQuery.isLoading ? (
              <>
                <TrendFallback />
                <TrendFallback />
              </>
            ) : (
              <>
                <Suspense fallback={<TrendFallback />}>
                  <NorthTrendChart data={northTrendQuery.data ?? []} />
                </Suspense>
                <Suspense fallback={<TrendFallback />}>
                  <AmountTrendChart data={amountTrendQuery.data ?? []} />
                </Suspense>
              </>
            )}
          </>
        ) : (
          <Surface className="trend-teaser">
            <span className="section-kicker">Deferred Charts</span>
            <h3 className="trend-card__title">滚动到这里再加载趋势图</h3>
            <p className="trend-teaser__body">
              北向资金与成交额趋势会在你滚动到这个区域后再请求并渲染。
            </p>
          </Surface>
        )}
      </div>
    </section>
  );
};
