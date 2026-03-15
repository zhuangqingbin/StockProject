import type { IndustryRankingItem } from "../../lib/api/types";
import { StockTreemapChart as ReactECharts } from "../../lib/charts/StockTreemapChart";
import { buildIndustryTreemapOption } from "./options/treemapOptions";

interface IndustryTreemapProps {
  data: IndustryRankingItem[];
  topN: number;
  onSelectIndustry: (industry: string) => void;
}

export const IndustryTreemap = ({ data, topN, onSelectIndustry }: IndustryTreemapProps) => {
  return (
    <ReactECharts
      option={buildIndustryTreemapOption(data, topN)}
      style={{ height: 420 }}
      onEvents={{
        click: (params: { data?: { name?: string } }) => {
          if (params.data?.name) {
            onSelectIndustry(params.data.name);
          }
        },
      }}
    />
  );
};
