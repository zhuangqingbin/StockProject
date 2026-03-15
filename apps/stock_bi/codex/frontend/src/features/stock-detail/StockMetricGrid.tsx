import type { CompanyInfoResponse, MoneyflowResponse, StockDetailResponse } from "../../lib/api/types";
import { DescriptionGrid, MetricTile, Surface } from "../../ui";

interface StockMetricGridProps {
  detail: StockDetailResponse | undefined;
  company: CompanyInfoResponse | undefined;
  moneyflow: MoneyflowResponse | undefined;
}

export const StockMetricGrid = ({ detail, company, moneyflow }: StockMetricGridProps) => {
  return (
    <div className="stock-metric-grid">
      <Surface>
        <MetricTile label="最新收盘价" value={detail?.daily?.close?.toFixed(2) ?? "--"} />
        <MetricTile label="当日涨跌幅" value={detail?.daily?.pct_chg?.toFixed(2) ?? "--"} suffix="%" />
      </Surface>
      <Surface>
        <MetricTile label="换手率" value={detail?.basic?.turnover_rate?.toFixed(2) ?? "--"} suffix="%" />
        <MetricTile label="成交额" value={detail?.daily?.amount?.toFixed(0) ?? "--"} />
      </Surface>
      <DescriptionGrid
        columns={2}
        items={[
          { label: "名称", value: company?.name ?? detail?.company?.name ?? "--" },
          { label: "行业", value: company?.industry ?? detail?.company?.industry ?? "--" },
          { label: "板块", value: company?.market ?? detail?.company?.market ?? "--" },
          { label: "主营", value: company?.main_business ?? "--" },
          { label: "主力净额", value: moneyflow?.net_mf_amount == null ? "--" : moneyflow.net_mf_amount.toFixed(2) },
          { label: "官网", value: company?.website ?? "--" },
        ]}
      />
    </div>
  );
};
