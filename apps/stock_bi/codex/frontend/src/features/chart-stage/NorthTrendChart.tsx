import type { NorthTrendPoint } from "../../lib/api/types";
import { StockChart as ReactECharts } from "../../lib/charts/StockChart";
import { Surface } from "../../ui";
import { buildLineSeriesOption } from "./options/lineOptions";

interface NorthTrendChartProps {
  data: NorthTrendPoint[];
}

export const NorthTrendChart = ({ data }: NorthTrendChartProps) => {
  return (
    <Surface className="trend-card">
      <span className="section-kicker">North Flow</span>
      <h3 className="trend-card__title">北向资金趋势</h3>
      <ReactECharts
        option={buildLineSeriesOption(
          data.map((item) => item.trade_date),
          data.map((item) => item.north_total),
          "#da8e57",
          "rgba(218,142,87,0.24)",
        )}
        style={{ height: 240 }}
      />
    </Surface>
  );
};
