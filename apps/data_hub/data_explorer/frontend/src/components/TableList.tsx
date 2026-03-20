import { Empty, Input, Select, Spin, Typography } from "antd";

import type { TableListItem } from "../types";

type TableListProps = {
  categoryLabel: string;
  loading?: boolean;
  searchValue: string;
  statusFilter: string;
  tables: TableListItem[];
  onSearchChange: (value: string) => void;
  onStatusFilterChange: (value: string) => void;
  onSelectTable: (tableName: string) => void;
};

const { Title, Text } = Typography;

const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "delayed", label: "延迟" },
  { value: "no_data", label: "无数据" },
  { value: "error", label: "异常" },
  { value: "normal", label: "正常" },
  { value: "manual", label: "手工维护" },
];

const renderCell = (value: string | number | null) => (value === null || value === "" ? "—" : value);

const TableList = ({
  categoryLabel,
  loading = false,
  searchValue,
  statusFilter,
  tables,
  onSearchChange,
  onStatusFilterChange,
  onSelectTable,
}: TableListProps) => (
  <section className="panel">
    <div className="panel-header">
      <div>
        <Text className="eyebrow">当前分类</Text>
        <Title level={2}>{categoryLabel}</Title>
      </div>
      <div className="toolbar">
        <Input
          allowClear
          className="toolbar-input"
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="搜索当前分类表名或说明"
          value={searchValue}
        />
        <Select
          className="toolbar-select"
          onChange={onStatusFilterChange}
          options={statusOptions}
          value={statusFilter}
        />
      </div>
    </div>
    <div className="table-frame">
      {loading ? (
        <div className="loading-block">
          <Spin />
        </div>
      ) : tables.length === 0 ? (
        <Empty description="当前分类下无匹配结果" />
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>表名</th>
              <th>中文说明</th>
              <th>总行数</th>
              <th>最早数据日期</th>
              <th>最新数据日期</th>
              <th>最近更新时间</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {tables.map((table) => (
              <tr key={table.table_name} onClick={() => onSelectTable(table.table_name)}>
                <td>
                  {table.api_url ? (
                    <a
                      aria-label={`查看 ${table.table_name} API 文档`}
                      className="table-link"
                      href={table.api_url}
                      onClick={(event) => event.stopPropagation()}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {table.table_name}
                    </a>
                  ) : (
                    table.table_name
                  )}
                </td>
                <td>{table.description}</td>
                <td>{renderCell(table.row_count)}</td>
                <td>{renderCell(table.earliest_data_date)}</td>
                <td>{renderCell(table.latest_data_date)}</td>
                <td>{renderCell(table.last_updated)}</td>
                <td>
                  <span className={`status-pill status-${table.status}`}>{table.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  </section>
);

export default TableList;
