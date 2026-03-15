import { useQuery } from "@tanstack/react-query";

import { fetchCompanyInfo, fetchMoneyflow, fetchStockDetail } from "../../lib/api/marketApi";
import { useDashboardStore } from "../../lib/state/dashboardStore";
import { DrawerPanel, EmptyState, LoadingBlock } from "../../ui";
import { StockKlinePanel } from "./StockKlinePanel";
import { StockMetricGrid } from "./StockMetricGrid";

export const StockDrawer = () => {
  const activeStock = useDashboardStore((state) => state.activeStock);
  const setActiveStock = useDashboardStore((state) => state.setActiveStock);

  const detailQuery = useQuery({
    queryKey: ["market", "stock-detail", activeStock],
    queryFn: () => fetchStockDetail(activeStock ?? ""),
    enabled: Boolean(activeStock),
  });
  const companyQuery = useQuery({
    queryKey: ["market", "company", activeStock],
    queryFn: () => fetchCompanyInfo(activeStock ?? ""),
    enabled: Boolean(activeStock),
  });
  const moneyflowQuery = useQuery({
    queryKey: ["market", "moneyflow", activeStock],
    queryFn: () => fetchMoneyflow(activeStock ?? ""),
    enabled: Boolean(activeStock),
  });

  return (
    <DrawerPanel
      title={activeStock ?? "个股详情"}
      width={960}
      open={Boolean(activeStock)}
      onClose={() => setActiveStock(null)}
    >
      {detailQuery.data ? (
        <div className="detail-stack">
          <StockMetricGrid detail={detailQuery.data} company={companyQuery.data} moneyflow={moneyflowQuery.data} />
          <section className="drawer-section">
            <h3 className="drawer-section__title">个股 K 线</h3>
            <StockKlinePanel detail={detailQuery.data} />
          </section>
        </div>
      ) : detailQuery.isLoading ? (
        <LoadingBlock rows={8} />
      ) : (
        <EmptyState description="暂无个股详情数据" />
      )}
    </DrawerPanel>
  );
};
