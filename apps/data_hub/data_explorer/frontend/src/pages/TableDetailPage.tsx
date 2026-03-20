import { Button, Empty, Spin, Tabs } from "antd";

import TableRecentRuns from "../components/TableRecentRuns";
import TablePreview from "../components/TablePreview";
import TableStructure from "../components/TableStructure";
import TableSummary from "../components/TableSummary";
import { useTableDetail } from "../hooks/useCatalog";
import { useNavigationStore } from "../stores/navigationStore";

type TableDetailPageProps = {
  tableName: string;
};

const TableDetailPage = ({ tableName }: TableDetailPageProps) => {
  const activeTab = useNavigationStore((state) => state.tableDetailTab);
  const setSelectedTable = useNavigationStore((state) => state.setSelectedTable);
  const setTableDetailTab = useNavigationStore((state) => state.setTableDetailTab);
  const detailQuery = useTableDetail(tableName);

  if (detailQuery.isLoading) {
    return (
      <div className="loading-block">
        <Spin />
      </div>
    );
  }

  if (!detailQuery.data) {
    return <Empty description="未找到表详情" />;
  }

  return (
    <div className="content-stack">
      <Button
        className="back-button"
        onClick={() => {
          setSelectedTable(null);
          setTableDetailTab("structure");
        }}
      >
        返回目录
      </Button>
      <TableSummary detail={detailQuery.data} />
      <Tabs
        activeKey={activeTab}
        className="detail-tabs"
        items={[
          {
            key: "structure",
            label: "结构信息",
            children: <TableStructure detail={detailQuery.data} />,
          },
          {
            key: "preview",
            label: "数据预览",
            children: <TablePreview enabled={activeTab === "preview"} tableName={tableName} />,
          },
          {
            key: "runs",
            label: "最近运行",
            children: <TableRecentRuns runs={detailQuery.data.recent_runs} />,
          },
        ]}
        onChange={(value) => setTableDetailTab(value as "structure" | "preview" | "runs")}
      />
    </div>
  );
};

export default TableDetailPage;
