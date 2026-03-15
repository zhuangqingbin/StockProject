import type { IndustryStocksResponse } from "../../lib/api/types";
import { DataTable } from "../../ui";

interface IndustryStocksTableProps {
  data: IndustryStocksResponse | undefined;
  onSelectStock: (tsCode: string) => void;
}

export const IndustryStocksTable = ({ data, onSelectStock }: IndustryStocksTableProps) => {
  return (
    <DataTable
      data={data?.stocks ?? []}
      rowKey={(row) => row.ts_code}
      onRowClick={(row) => onSelectStock(row.ts_code)}
      columns={[
        { key: "ts_code", header: "代码", render: (row) => row.ts_code },
        { key: "name", header: "名称", render: (row) => row.name ?? "--" },
        { key: "pct_chg", header: "涨跌幅", render: (row) => `${row.pct_chg.toFixed(2)}%` },
        {
          key: "close",
          header: "收盘价",
          render: (row) => (row.close == null ? "--" : row.close.toFixed(2)),
        },
        {
          key: "turnover_rate",
          header: "换手率",
          render: (row) =>
            row.turnover_rate == null ? "--" : `${row.turnover_rate.toFixed(2)}%`,
        },
      ]}
    />
  );
};
