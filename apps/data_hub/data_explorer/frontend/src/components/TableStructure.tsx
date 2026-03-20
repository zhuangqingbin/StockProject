import { Collapse, Empty, Typography } from "antd";

import type { TableDetail } from "../types";

type TableStructureProps = {
  detail: TableDetail;
};

const { Title } = Typography;

const renderColumns = (columns: TableDetail["structure"]["columns"]) => {
  if (columns.length === 0) {
    return <Empty description="暂无字段信息" />;
  }

  return (
    <table className="data-table compact">
      <thead>
        <tr>
          <th>字段名</th>
          <th>中文名</th>
          <th>类型</th>
          <th>可空</th>
          <th>默认值</th>
          <th>注释</th>
        </tr>
      </thead>
      <tbody>
        {columns.map((column) => (
          <tr key={column.name}>
            <td>{column.name}</td>
            <td>{column.label ?? column.comment ?? "—"}</td>
            <td>{column.type}</td>
            <td>{column.nullable ? "是" : "否"}</td>
            <td>{column.default ?? "—"}</td>
            <td>{column.comment ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const renderIndexes = (indexes: TableDetail["structure"]["indexes"]) => {
  if (indexes.length === 0) {
    return <Empty description="暂无索引信息" />;
  }

  return (
    <table className="data-table compact">
      <thead>
        <tr>
          <th>索引名</th>
          <th>字段</th>
          <th>唯一</th>
          <th>主键</th>
        </tr>
      </thead>
      <tbody>
        {indexes.map((index) => (
          <tr key={index.name}>
            <td>{index.name}</td>
            <td>{index.columns.join(", ")}</td>
            <td>{index.unique ? "是" : "否"}</td>
            <td>{index.primary ? "是" : "否"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const renderConstraints = (constraints: TableDetail["structure"]["constraints"]) => {
  if (constraints.length === 0) {
    return <Empty description="暂无约束信息" />;
  }

  return (
    <table className="data-table compact">
      <thead>
        <tr>
          <th>约束名</th>
          <th>类型</th>
          <th>字段</th>
        </tr>
      </thead>
      <tbody>
        {constraints.map((constraint) => (
          <tr key={constraint.name}>
            <td>{constraint.name}</td>
            <td>{constraint.type ?? "—"}</td>
            <td>{constraint.columns?.join(", ") ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const TableStructure = ({ detail }: TableStructureProps) => (
  <section className="panel">
    <Title level={3}>字段结构</Title>
    {renderColumns(detail.structure.columns)}
    <Title level={3}>索引信息</Title>
    {renderIndexes(detail.structure.indexes)}
    <Title level={3}>约束信息</Title>
    {renderConstraints(detail.structure.constraints)}
    <Collapse
      className="ddl-collapse"
      items={[
        {
          key: "ddl",
          label: "建表 SQL",
          children: <pre className="ddl-block">{detail.structure.ddl || "暂无 DDL"}</pre>,
        },
      ]}
    />
  </section>
);

export default TableStructure;
