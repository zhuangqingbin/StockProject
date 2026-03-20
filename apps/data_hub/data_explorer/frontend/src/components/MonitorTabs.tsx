import { Card, Select, Tabs, Typography } from "antd";

import type { JobMonitorRow, MonitorOverview, PipelineRunRow, TableMonitorRow } from "../types";

type MonitorTabsProps = {
  activeView: "overview" | "datasets" | "jobs" | "runs";
  activeStatusFilter: string;
  jobRows: JobMonitorRow[];
  overview: MonitorOverview | null;
  runRows: PipelineRunRow[];
  tableRows: TableMonitorRow[];
  onOpenTable: (tableName: string) => void;
  onStatusFilterChange: (value: string) => void;
  onViewChange: (value: "overview" | "datasets" | "jobs" | "runs") => void;
};

const { Text, Title } = Typography;

const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "delayed", label: "延迟" },
  { value: "partial_failed", label: "部分失败" },
  { value: "failed", label: "失败" },
  { value: "success", label: "成功" },
  { value: "error", label: "异常" },
  { value: "no_data", label: "无数据" },
  { value: "manual", label: "手工" },
  { value: "normal", label: "正常" },
];

const getStatusValue = (row: Record<string, unknown>) =>
  String(row.freshness ?? row.result ?? row.status ?? "unknown");

const matchesStatusFilter = (row: Record<string, unknown>, filter: string) =>
  filter === "all" ? true : getStatusValue(row) === filter;

const renderRows = <T extends Record<string, unknown>>(
  rows: T[],
  keys: string[],
  onRowClick?: (tableName: string) => void,
) => (
  <table className="data-table">
    <thead>
      <tr>
        {keys.map((key) => (
          <th key={key}>{key}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {rows.map((row, index) => (
        <tr
          key={`${String(row[keys[0]])}-${index}`}
          onClick={
            onRowClick && typeof row.table_name === "string" ? () => onRowClick(row.table_name as string) : undefined
          }
        >
          {keys.map((key) => (
            <td key={key}>{String(row[key] ?? "—")}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);

const renderOverview = (overview: MonitorOverview | null) => {
  if (!overview) {
    return null;
  }

  const cards = [
    { label: "数据资产总数", value: overview.dataset_count },
    { label: "新鲜资产", value: overview.fresh_datasets },
    { label: "延迟资产", value: overview.delayed_datasets },
    { label: "异常资产", value: overview.error_datasets },
    { label: "近 24h 失败 jobs", value: overview.recent_failed_jobs },
    { label: "近期 runs", value: overview.recent_runs },
  ];

  return (
    <div className="monitor-overview">
      <div className="monitor-summary-grid">
        {cards.map((card) => (
          <Card key={card.label} className="metric-card monitor-metric-card" variant="borderless">
            <Text className="metric-label">{card.label}</Text>
            <Text className="metric-value-text">{String(card.value)}</Text>
          </Card>
        ))}
      </div>
      <Card className="monitor-run-callout" variant="borderless">
        <Text className="metric-label">最近一次批次</Text>
        {overview.latest_run ? (
          <div className="monitor-run-stack">
            <Title level={4}>{overview.latest_run.run_id}</Title>
            <div className="detail-chip-row">
              <span className={`status-pill status-${overview.latest_run.status}`}>{overview.latest_run.status}</span>
              <span className="detail-chip">模式 · {overview.latest_run.run_mode}</span>
              <span className="detail-chip">窗口 · {overview.latest_run.effective_window}</span>
            </div>
            <Text>开始时间：{overview.latest_run.started_at ?? "—"}</Text>
            <Text>结束时间：{overview.latest_run.ended_at ?? "—"}</Text>
            <Text>触发 Profile：{overview.latest_run.trigger_profiles.join(", ") || "—"}</Text>
          </div>
        ) : (
          <Text>当前还没有可展示的 run 记录。</Text>
        )}
      </Card>
    </div>
  );
};

const MonitorTabs = ({
  activeView,
  activeStatusFilter,
  jobRows,
  overview,
  runRows,
  tableRows,
  onOpenTable,
  onStatusFilterChange,
  onViewChange,
}: MonitorTabsProps) => {
  const filteredTableRows = tableRows.filter((row) => matchesStatusFilter(row, activeStatusFilter));
  const filteredJobRows = jobRows.filter((row) => matchesStatusFilter(row, activeStatusFilter));
  const filteredRunRows = runRows.filter((row) => matchesStatusFilter(row, activeStatusFilter));

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <Text className="eyebrow">Ops Workspace</Text>
          <Title level={3}>运行与健康视图</Title>
        </div>
        <Select
          className="toolbar-select"
          onChange={onStatusFilterChange}
          options={statusOptions}
          value={activeStatusFilter}
        />
      </div>
      <Tabs
        activeKey={activeView}
        onChange={(value) => onViewChange(value as "overview" | "datasets" | "jobs" | "runs")}
        items={[
          {
            key: "overview",
            label: "总览",
            children: renderOverview(overview),
          },
          {
            key: "datasets",
            label: "数据资产",
            children: renderRows(
              filteredTableRows,
              ["table_name", "category", "freshness", "latest_data_date", "last_updated", "last_run_result"],
              onOpenTable,
            ),
          },
          {
            key: "jobs",
            label: "任务执行",
            children: renderRows(
              filteredJobRows,
              ["run_id", "job_name", "table_name", "result", "effective_date", "duration_seconds", "error"],
              onOpenTable,
            ),
          },
          {
            key: "runs",
            label: "批次 Runs",
            children: renderRows(
              filteredRunRows,
              ["run_id", "run_mode", "status", "effective_window", "job_count", "failed_jobs", "started_at"],
            ),
          },
        ]}
      />
    </section>
  );
};

export default MonitorTabs;
