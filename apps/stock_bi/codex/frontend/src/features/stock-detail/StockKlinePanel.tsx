import type { StockDetailResponse } from "../../lib/api/types";
import { StockCandleChart as ReactECharts } from "../../lib/charts/StockCandleChart";
import { EmptyState } from "../../ui";
import { buildStockCandleOption } from "../chart-stage/options/candleOptions";

interface StockKlinePanelProps {
  detail: StockDetailResponse | undefined;
}

export const StockKlinePanel = ({ detail }: StockKlinePanelProps) => {
  if (!detail || detail.kline.length === 0) {
    return <EmptyState description="暂无个股 K 线数据" />;
  }

  return (
    <ReactECharts
      option={buildStockCandleOption(
        detail.kline.map((item) => item.date),
        detail.kline.map((item) => ({
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        })),
      )}
      style={{ height: 320 }}
    />
  );
};
