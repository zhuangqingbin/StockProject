import { lazy, Suspense } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchSummary } from "../../lib/api/marketApi";
import { useDashboardStore } from "../../lib/state/dashboardStore";
import { useMarketSocket } from "../../lib/ws/useMarketSocket";
import { AlertBanner, LoadingBlock, Surface } from "../../ui";
import { ChartStage } from "../chart-stage/ChartStage";
import { ChatConsole } from "../chat-console/ChatConsole";
import { ConsistencyBanner } from "./ConsistencyBanner";
import { HeroBrief } from "./HeroBrief";
import { IndexPulse } from "./IndexPulse";
import { MarketHeader } from "./MarketHeader";
import { MarketTape } from "./MarketTape";
import { OverviewCards } from "./OverviewCards";

const IndustryDrawer = lazy(() =>
  import("../industry-detail/IndustryDrawer").then((module) => ({ default: module.IndustryDrawer })),
);
const StockDrawer = lazy(() =>
  import("../stock-detail/StockDrawer").then((module) => ({ default: module.StockDrawer })),
);

export const MarketShell = () => {
  const queryClient = useQueryClient();
  const wsStatus = useDashboardStore((state) => state.wsStatus);
  const activeIndustry = useDashboardStore((state) => state.activeIndustry);
  const activeStock = useDashboardStore((state) => state.activeStock);
  const updateBannerTradeDate = useDashboardStore((state) => state.updateBannerTradeDate);
  const setUpdateBannerTradeDate = useDashboardStore((state) => state.setUpdateBannerTradeDate);

  useMarketSocket();

  const summaryQuery = useQuery({
    queryKey: ["market", "summary"],
    queryFn: fetchSummary,
  });

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["market"] });
  };

  const summary = summaryQuery.data;

  return (
    <div className="dashboard-shell">
      <MarketHeader
        tradeDate={summary?.trade_date_fmt ?? null}
        wsStatus={wsStatus}
        onRefresh={handleRefresh}
        refreshing={summaryQuery.isFetching}
      />
      {summary ? <MarketTape summary={summary} /> : null}
      {updateBannerTradeDate ? (
        <AlertBanner
          tone="info"
          className="update-banner"
          title={`检测到 ${updateBannerTradeDate} 数据更新，图表已自动刷新`}
          onClose={() => setUpdateBannerTradeDate(null)}
        />
      ) : null}
      {summary ? <ConsistencyBanner consistency={summary.data_consistency} /> : null}
      {summary ? (
        <>
          <section className="dashboard-hero">
            <HeroBrief summary={summary} />
            <div className="dashboard-hero__rail">
              <IndexPulse indices={summary.index_data} />
              <OverviewCards summary={summary} />
            </div>
          </section>
          <section className="dashboard-main">
            <ChartStage summary={summary} />
            <ChatConsole />
          </section>
          {activeIndustry ? (
            <Suspense fallback={null}>
              <IndustryDrawer />
            </Suspense>
          ) : null}
          {activeStock ? (
            <Suspense fallback={null}>
              <StockDrawer />
            </Suspense>
          ) : null}
        </>
      ) : summaryQuery.isLoading ? (
        <Surface className="dashboard-loading">
          <LoadingBlock rows={12} />
        </Surface>
      ) : (
        <AlertBanner
          tone="error"
          title="无法加载市场数据"
          description={summaryQuery.error?.message}
        />
      )}
    </div>
  );
};
