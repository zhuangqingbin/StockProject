import { Button, Card, Col, Empty, Row, Typography } from "antd";

import { getProfileDescription } from "../profileInfo";
import type { DatabaseOverview, TableListItem, TableMetadataDetail } from "../types";

type SchemaOverviewProps = {
  metadata: TableMetadataDetail | null;
  overview: DatabaseOverview;
  tables: TableListItem[];
  onInspectTable: (tableName: string) => void;
  onOpenTableDetail: (tableName: string) => void;
  selectedTable: string | null;
};

const { Title, Text } = Typography;

const SchemaOverview = ({
  metadata,
  overview,
  tables,
  onInspectTable,
  onOpenTableDetail,
  selectedTable,
}: SchemaOverviewProps) => {
  const selectedTableEntry = tables.find((table) => table.table_name === selectedTable) ?? null;
  const categoryEntries = Object.entries(overview.category_counts).sort((left, right) => right[1] - left[1]);
  const summaryCards = [
    { label: "数据库", value: overview.schema_name ?? "stock_database_v1" },
    { label: "表总数", value: overview.table_count },
    { label: "系统表", value: overview.runtime_table_count },
    { label: "分类数", value: categoryEntries.length },
    { label: "当前分类表数", value: tables.length },
    { label: "当前查看", value: selectedTable ?? "—" },
  ];

  return (
    <div className="metadata-layout">
      <section className="panel">
        <div className="panel-header">
          <div>
            <Text className="eyebrow">库级概览</Text>
            <Title level={2}>数据库元信息</Title>
          </div>
        </div>
        <Row gutter={[16, 16]}>
          {summaryCards.map((card) => (
            <Col key={card.label} lg={8} md={12} span={24}>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">{card.label}</Text>
                <Text className="metric-value-text">{String(card.value)}</Text>
              </Card>
            </Col>
          ))}
        </Row>
        <div className="metadata-secondary-grid">
          <Card className="metric-card metadata-distribution-card" variant="borderless">
            <Text className="metric-label">分类分布</Text>
            <div className="metadata-distribution-list">
              {categoryEntries.map(([category, count]) => (
                <div key={category} className="metadata-distribution-row">
                  <div>
                    <Text className="metadata-distribution-name">{category}</Text>
                    <Text className="metadata-helper-text">当前数据库中的目录分层</Text>
                  </div>
                  <Text className="metric-value-text metadata-distribution-count">{count}</Text>
                </div>
              ))}
            </div>
          </Card>
          <Card className="metric-card metadata-selector-card" variant="borderless">
            <Text className="metric-label">当前分类表清单</Text>
            <Text className="metadata-helper-text">点击切换右侧结构面板与表画像。</Text>
            <section aria-label="metadata-overview" className="metadata-table-picks">
              {tables.map((table) => (
                <Button
                  key={table.table_name}
                  onClick={() => onInspectTable(table.table_name)}
                  type={selectedTable === table.table_name ? "primary" : "default"}
                >
                  {table.table_name}
                </Button>
              ))}
            </section>
          </Card>
        </div>
      </section>
      <section className="panel">
        {metadata ? (
          <>
            <div className="panel-header">
              <div>
                <Text className="eyebrow">元信息明细</Text>
                <Title level={3}>{selectedTable}</Title>
              </div>
              {selectedTable ? (
                <Button onClick={() => onOpenTableDetail(selectedTable)} type="primary">
                  打开表详情
                </Button>
              ) : null}
            </div>
            <div className="metadata-detail-grid">
              <Card className="metadata-profile-card" variant="borderless">
                <Text className="metric-label">表画像</Text>
                <Title level={4}>{selectedTable}</Title>
                <Text className="metadata-copy">{selectedTableEntry?.description ?? "—"}</Text>
                <div className="metadata-pill-row">
                  {selectedTableEntry?.status ? (
                    <span className={`status-pill status-${selectedTableEntry.status}`}>
                      {selectedTableEntry.status}
                    </span>
                  ) : null}
                  {selectedTableEntry?.api_url ? (
                    <a
                      className="table-link"
                      href={selectedTableEntry.api_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      API 文档
                    </a>
                  ) : null}
                </div>
                <Text className="metadata-helper-text">
                  {getProfileDescription(selectedTableEntry?.trigger_profile)}
                </Text>
              </Card>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">字段数</Text>
                <Text className="metric-value-text">{metadata.columns.length}</Text>
              </Card>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">索引数</Text>
                <Text className="metric-value-text">{metadata.indexes.length}</Text>
              </Card>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">约束数</Text>
                <Text className="metric-value-text">{metadata.constraints.length}</Text>
              </Card>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">最新数据日期</Text>
                <Text className="metric-value-text metadata-value-inline">
                  {selectedTableEntry?.latest_data_date ?? "—"}
                </Text>
              </Card>
              <Card className="metric-card" variant="borderless">
                <Text className="metric-label">最近更新时间</Text>
                <Text className="metric-value-text metadata-value-inline">
                  {selectedTableEntry?.last_updated ?? "—"}
                </Text>
              </Card>
            </div>
            <Title level={4}>字段</Title>
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>字段名</th>
                  <th>字段类型</th>
                </tr>
              </thead>
              <tbody>
                {metadata.columns.map((column) => (
                  <tr key={column.name}>
                    <td>{column.name}</td>
                    <td>{column.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Title level={4}>索引</Title>
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>索引名</th>
                  <th>字段列</th>
                </tr>
              </thead>
              <tbody>
                {metadata.indexes.map((index) => (
                  <tr key={index.name}>
                    <td>{index.name}</td>
                    <td>{index.columns.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Title level={4}>约束</Title>
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>约束名</th>
                  <th>约束类型</th>
                </tr>
              </thead>
              <tbody>
                {metadata.constraints.map((constraint) => (
                  <tr key={constraint.name}>
                    <td>{constraint.name}</td>
                    <td>{constraint.type ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Title level={4}>DDL</Title>
            <pre className="ddl-block">{metadata.ddl}</pre>
          </>
        ) : (
          <Empty description="选择一张表查看元信息详情" />
        )}
      </section>
    </div>
  );
};

export default SchemaOverview;
