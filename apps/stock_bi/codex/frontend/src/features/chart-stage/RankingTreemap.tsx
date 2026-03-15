import type { RankingItem, SortDirection } from "../../lib/api/types";
import { StockTreemapChart as ReactECharts } from "../../lib/charts/StockTreemapChart";
import { buildRankingTreemapOption } from "./options/treemapOptions";

interface RankingTreemapProps {
  data: RankingItem[];
  order: SortDirection;
  topN: number;
  onSelectStock: (tsCode: string) => void;
}

export const RankingTreemap = ({ data, order, topN, onSelectStock }: RankingTreemapProps) => {
  return (
    <ReactECharts
      option={buildRankingTreemapOption(data, order, topN)}
      style={{ height: 420 }}
      onEvents={{
        click: (params: { data?: { ts_code?: string } }) => {
          if (params.data?.ts_code) {
            onSelectStock(params.data.ts_code);
          }
        },
      }}
    />
  );
};
