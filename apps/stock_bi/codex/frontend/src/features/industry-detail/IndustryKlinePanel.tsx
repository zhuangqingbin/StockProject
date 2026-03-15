import type { IndustryDetailResponse } from "../../lib/api/types";
import { StockChart as ReactECharts } from "../../lib/charts/StockChart";
import { EmptyState } from "../../ui";
import { buildLineSeriesOption } from "../chart-stage/options/lineOptions";

interface IndustryKlinePanelProps {
  detail: IndustryDetailResponse | undefined;
}

export const IndustryKlinePanel = ({ detail }: IndustryKlinePanelProps) => {
  if (!detail || detail.kline.length === 0) {
    return <EmptyState description="暂无行业 K 线数据" />;
  }

  return (
    <ReactECharts
      option={buildLineSeriesOption(
        detail.kline.map((item) => item.date),
        detail.kline.map((item) => item.close),
        "#f08f5a",
        "rgba(240,143,90,0.22)",
      )}
      style={{ height: 260 }}
    />
  );
};
