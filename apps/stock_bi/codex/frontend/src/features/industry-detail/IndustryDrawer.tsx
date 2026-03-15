import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchIndustryDetail, fetchIndustryStocks } from "../../lib/api/marketApi";
import type { SortDirection } from "../../lib/api/types";
import { useDashboardStore } from "../../lib/state/dashboardStore";
import { Button, DescriptionGrid, DrawerPanel, EmptyState, LoadingBlock, SegmentedControl } from "../../ui";
import { IndustryKlinePanel } from "./IndustryKlinePanel";
import { IndustryStocksTable } from "./IndustryStocksTable";

export const IndustryDrawer = () => {
  const [order, setOrder] = useState<SortDirection>("desc");
  const activeIndustry = useDashboardStore((state) => state.activeIndustry);
  const setActiveIndustry = useDashboardStore((state) => state.setActiveIndustry);
  const setActiveStock = useDashboardStore((state) => state.setActiveStock);

  const detailQuery = useQuery({
    queryKey: ["market", "industry-detail", activeIndustry],
    queryFn: () => fetchIndustryDetail(activeIndustry ?? ""),
    enabled: Boolean(activeIndustry),
  });
  const stocksQuery = useQuery({
    queryKey: ["market", "industry-stocks", activeIndustry, order],
    queryFn: () => fetchIndustryStocks(activeIndustry ?? "", order),
    enabled: Boolean(activeIndustry),
  });

  return (
    <DrawerPanel
      title={activeIndustry ?? "行业详情"}
      width={920}
      open={Boolean(activeIndustry)}
      onClose={() => setActiveIndustry(null)}
    >
      {detailQuery.data ? (
        <div className="detail-stack">
          <DescriptionGrid
            items={[
              { label: "行业", value: detailQuery.data.industry },
              { label: "指数", value: detailQuery.data.index_name ?? "聚合口径" },
              { label: "交易日", value: detailQuery.data.trade_date },
              { label: "成分股", value: detailQuery.data.stats?.stock_count ?? "--" },
              { label: "上涨家数", value: detailQuery.data.stats?.up_count ?? "--" },
              {
                label: "平均涨跌幅",
                value: detailQuery.data.stats ? `${detailQuery.data.stats.avg_pct_chg.toFixed(2)}%` : "--",
              },
            ]}
          />
          <section className="drawer-section">
            <h3 className="drawer-section__title">行业 K 线</h3>
            <IndustryKlinePanel detail={detailQuery.data} />
          </section>
          <section className="drawer-section">
            <div className="drawer-section__header">
              <h3 className="drawer-section__title">成分股列表</h3>
              <SegmentedControl
                value={order}
                onChange={(next) => setOrder(next as SortDirection)}
                options={[
                  { label: "强势", value: "desc" },
                  { label: "弱势", value: "asc" },
                ]}
              />
            </div>
            {stocksQuery.data ? (
              <IndustryStocksTable data={stocksQuery.data} onSelectStock={setActiveStock} />
            ) : stocksQuery.isLoading ? (
              <LoadingBlock rows={6} />
            ) : (
              <EmptyState description="暂无行业成分股数据" />
            )}
          </section>
        </div>
      ) : detailQuery.isLoading ? (
        <LoadingBlock rows={8} />
      ) : (
        <EmptyState
          description="暂无行业详情数据"
          action={
            <Button variant="ghost" onClick={() => setActiveIndustry(null)}>
              关闭
            </Button>
          }
        />
      )}
    </DrawerPanel>
  );
};
