import { Empty, Typography } from "antd";

import type { TableRecentRun } from "../types";

type TableRecentRunsProps = {
  runs: TableRecentRun[];
};

const { Title } = Typography;

const TableRecentRuns = ({ runs }: TableRecentRunsProps) => (
  <section className="panel">
    <Title level={3}>最近运行</Title>
    {runs.length === 0 ? (
      <Empty description="当前表暂无运行记录" />
    ) : (
      <table className="data-table compact">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>模式</th>
            <th>Profile</th>
            <th>结果</th>
            <th>有效日期</th>
            <th>写入行数</th>
            <th>耗时</th>
            <th>执行时间</th>
            <th>错误</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run, index) => (
            <tr key={`${run.run_id ?? run.job_name}-${index}`}>
              <td>{run.run_id ?? "—"}</td>
              <td>{run.run_mode ?? "—"}</td>
              <td>{run.trigger_profile ?? "—"}</td>
              <td>
                <span className={`status-pill status-${run.result ?? "unknown"}`}>{run.result ?? "—"}</span>
              </td>
              <td>{run.effective_date ?? "—"}</td>
              <td>{run.rows_written ?? "—"}</td>
              <td>{run.duration_seconds ?? "—"}</td>
              <td>{run.executed_at ?? "—"}</td>
              <td>{run.error ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    )}
  </section>
);

export default TableRecentRuns;
