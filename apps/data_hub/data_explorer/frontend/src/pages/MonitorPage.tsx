import { Alert, Spin, Typography } from "antd";

import MonitorTabs from "../components/MonitorTabs";
import { useJobMonitor, useMonitorOverview, usePipelineRuns, useTableMonitor } from "../hooks/useMonitor";
import { useNavigationStore } from "../stores/navigationStore";

const { Title, Text } = Typography;

const MonitorPage = () => {
  const monitorView = useNavigationStore((state) => state.monitorView);
  const monitorStatusFilter = useNavigationStore((state) => state.monitorStatusFilter);
  const setMonitorView = useNavigationStore((state) => state.setMonitorView);
  const setMonitorStatusFilter = useNavigationStore((state) => state.setMonitorStatusFilter);
  const openTableDetail = useNavigationStore((state) => state.openTableDetail);

  const overviewQuery = useMonitorOverview();
  const tableMonitorQuery = useTableMonitor();
  const jobMonitorQuery = useJobMonitor();
  const runMonitorQuery = usePipelineRuns();

  if (overviewQuery.isLoading || tableMonitorQuery.isLoading || jobMonitorQuery.isLoading || runMonitorQuery.isLoading) {
    return (
      <div className="loading-block">
        <Spin />
      </div>
    );
  }

  if (overviewQuery.isError || tableMonitorQuery.isError || jobMonitorQuery.isError || runMonitorQuery.isError) {
    return <Alert message="监控数据加载失败" showIcon type="error" />;
  }

  return (
    <div className="content-stack">
      <section className="panel">
        <Text className="eyebrow">Operations</Text>
        <Title level={2}>运维监控</Title>
      </section>
      <MonitorTabs
        activeView={monitorView}
        activeStatusFilter={monitorStatusFilter}
        jobRows={jobMonitorQuery.data ?? []}
        onOpenTable={openTableDetail}
        onStatusFilterChange={setMonitorStatusFilter}
        onViewChange={setMonitorView}
        overview={overviewQuery.data ?? null}
        runRows={runMonitorQuery.data ?? []}
        tableRows={tableMonitorQuery.data ?? []}
      />
    </div>
  );
};

export default MonitorPage;
