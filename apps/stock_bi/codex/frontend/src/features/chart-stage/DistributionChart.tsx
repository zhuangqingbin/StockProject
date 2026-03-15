import type { DistributionBucket } from "../../lib/api/types";
import { StockChart as ReactECharts } from "../../lib/charts/StockChart";
import { buildDistributionOption } from "./options/distributionOptions";

interface DistributionChartProps {
  data: DistributionBucket[];
}

export const DistributionChart = ({ data }: DistributionChartProps) => {
  return <ReactECharts option={buildDistributionOption(data)} style={{ height: 420 }} />;
};
