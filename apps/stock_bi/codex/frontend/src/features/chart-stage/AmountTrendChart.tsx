import type { AmountTrendPoint } from "../../lib/api/types";
import { StockChart as ReactECharts } from "../../lib/charts/StockChart";
import { Surface } from "../../ui";
import { buildLineSeriesOption } from "./options/lineOptions";

interface AmountTrendChartProps {
  data: AmountTrendPoint[];
}

export const AmountTrendChart = ({ data }: AmountTrendChartProps) => {
  return (
    <Surface className="trend-card">
      <span className="section-kicker">Turnover Flow</span>
      <h3 className="trend-card__title">成交额趋势</h3>
      <ReactECharts
        option={buildLineSeriesOption(
          data.map((item) => item.trade_date),
          data.map((item) => item.total_amount),
          "#5486c8",
          "rgba(84,134,200,0.24)",
        )}
        style={{ height: 240 }}
      />
    </Surface>
  );
};
