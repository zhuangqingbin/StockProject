import { Alert } from "antd";
import { Typography } from "antd";

import TableList from "../components/TableList";
import { useCategories, useCategoryTables } from "../hooks/useCatalog";
import { useNavigationStore } from "../stores/navigationStore";

const { Title, Text } = Typography;

const DirectoryPage = () => {
  const selectedCategory = useNavigationStore((state) => state.selectedCategory);
  const directorySearch = useNavigationStore((state) => state.directorySearch);
  const monitorStatusFilter = useNavigationStore((state) => state.monitorStatusFilter);
  const setSelectedCategory = useNavigationStore((state) => state.setSelectedCategory);
  const setDirectorySearch = useNavigationStore((state) => state.setDirectorySearch);
  const setMonitorStatusFilter = useNavigationStore((state) => state.setMonitorStatusFilter);
  const openTableDetail = useNavigationStore((state) => state.openTableDetail);

  const categoriesQuery = useCategories();
  const tablesQuery = useCategoryTables(selectedCategory);

  const categoryLabel =
    categoriesQuery.data?.find((category) => category.key === selectedCategory)?.label ?? selectedCategory;

  const filteredTables = (tablesQuery.data ?? []).filter((table) => {
    const matchesSearch =
      directorySearch.trim() === "" ||
      table.table_name.toLowerCase().includes(directorySearch.trim().toLowerCase()) ||
      table.description.toLowerCase().includes(directorySearch.trim().toLowerCase());
    const matchesStatus = monitorStatusFilter === "all" || table.status === monitorStatusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="content-stack">
      <section className="panel">
        <Text className="eyebrow">当前工作区</Text>
        <Title level={2}>数据目录</Title>
      </section>
      {tablesQuery.isError ? <Alert message="目录加载失败" showIcon type="error" /> : null}
      <TableList
        categoryLabel={categoryLabel}
        loading={tablesQuery.isLoading}
        onSearchChange={setDirectorySearch}
        onSelectTable={openTableDetail}
        onStatusFilterChange={setMonitorStatusFilter}
        searchValue={directorySearch}
        statusFilter={monitorStatusFilter}
        tables={filteredTables}
      />
    </div>
  );
};

export default DirectoryPage;
