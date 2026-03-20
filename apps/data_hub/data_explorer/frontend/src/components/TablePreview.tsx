import { Button, Empty, Input, Pagination, Spin, Typography } from "antd";
import { useState } from "react";

import { useTablePreview } from "../hooks/usePreview";

type TablePreviewProps = {
  tableName: string;
  enabled: boolean;
};

const DEFAULT_PAGE_SIZE = 50;
const { Text } = Typography;

const TablePreview = ({ tableName, enabled }: TablePreviewProps) => {
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<"all" | "page">("all");
  const [draftFilters, setDraftFilters] = useState({
    ts_code: "",
    trade_date_start: "",
    trade_date_end: "",
  });
  const [filters, setFilters] = useState<Record<string, string>>({});

  const previewQuery = useTablePreview(tableName, {
    page: viewMode === "all" ? 1 : page,
    pageSize: DEFAULT_PAGE_SIZE,
    filters,
    allRows: viewMode === "all",
    enabled,
  });

  const handleApplyFilters = () => {
    setPage(1);
    setFilters(
      Object.fromEntries(
        Object.entries(draftFilters).filter(([, value]) => value.trim() !== ""),
      ),
    );
  };

  const rows = previewQuery.data?.data ?? [];
  const columns = previewQuery.data?.columns ?? Object.keys(rows[0] ?? {});
  const total = previewQuery.data?.total ?? 0;
  const allRowsMode = previewQuery.data?.all_rows ?? viewMode === "all";
  const displayedRows = previewQuery.data?.displayed_rows ?? rows.length;
  const truncated = previewQuery.data?.truncated ?? false;
  const truncatedLimit = previewQuery.data?.truncated_limit ?? displayedRows;
  const startRow = total === 0 ? 0 : allRowsMode ? 1 : (page - 1) * DEFAULT_PAGE_SIZE + 1;
  const endRow = total === 0 ? 0 : allRowsMode ? rows.length : Math.min(page * DEFAULT_PAGE_SIZE, total);

  return (
    <section className="panel">
      <div className="preview-toolbar">
        <Button onClick={() => setViewMode("all")} type={viewMode === "all" ? "primary" : "default"}>
          显示全部
        </Button>
        <Button onClick={() => setViewMode("page")} type={viewMode === "page" ? "primary" : "default"}>
          分页查看
        </Button>
        <Input
          onChange={(event) => setDraftFilters((previous) => ({ ...previous, ts_code: event.target.value }))}
          placeholder="按 ts_code 筛选"
          value={draftFilters.ts_code}
        />
        <Input
          onChange={(event) =>
            setDraftFilters((previous) => ({ ...previous, trade_date_start: event.target.value }))
          }
          placeholder="起始日期"
          value={draftFilters.trade_date_start}
        />
        <Input
          onChange={(event) =>
            setDraftFilters((previous) => ({ ...previous, trade_date_end: event.target.value }))
          }
          placeholder="结束日期"
          value={draftFilters.trade_date_end}
        />
        <Button onClick={handleApplyFilters} type="primary">
          应用筛选
        </Button>
      </div>
      <div className="summary-stack">
        {allRowsMode ? (
          <>
            {truncated ? (
              <Text className="preview-note">
                当前表共 {total} 行，已截断显示前 {truncatedLimit} 行、{columns.length} 个字段。
              </Text>
            ) : (
              <Text className="preview-note">当前已显示整张表，共 {total} 行、{columns.length} 个字段。</Text>
            )}
            <Text className="preview-note">
              当前已加载 {displayedRows} 行；整表数据按主日期列倒序展示，超大表建议先加筛选条件再查看。
            </Text>
          </>
        ) : (
          <>
            <Text className="preview-note">当前表共 {total} 行，支持翻页查看整张表。</Text>
            <Text className="preview-note">
              当前展示第 {startRow}-{endRow} 行，共 {columns.length} 个字段；默认每页 50 行，只读展示，优先按主日期列倒序。
            </Text>
          </>
        )}
      </div>
      {previewQuery.isLoading ? (
        <div className="loading-block">
          <Spin />
        </div>
      ) : columns.length === 0 ? (
        <Empty description="当前表暂无可预览数据" />
      ) : (
        <>
          <div className="table-frame">
            <table className="data-table compact">
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={`${tableName}-${index}`}>
                    {columns.map((column) => (
                      <td key={column}>{String(row[column] ?? "—")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {allRowsMode ? null : (
            <Pagination
              align="end"
              className="preview-pagination"
              current={page}
              onChange={(nextPage) => setPage(nextPage)}
              pageSize={DEFAULT_PAGE_SIZE}
              total={total}
            />
          )}
        </>
      )}
    </section>
  );
};

export default TablePreview;
