import { Alert, Spin } from "antd";
import { useEffect, useState } from "react";

import SchemaOverview from "../components/SchemaOverview";
import { useCategories, useCategoryTables } from "../hooks/useCatalog";
import { useDatabaseOverview, useTableMetadata } from "../hooks/useDatabaseMetadata";
import { useNavigationStore } from "../stores/navigationStore";

const DatabaseMetadataPage = () => {
  const selectedCategory = useNavigationStore((state) => state.selectedCategory);
  const openTableDetail = useNavigationStore((state) => state.openTableDetail);
  const categoriesQuery = useCategories();
  const tablesQuery = useCategoryTables(selectedCategory);
  const overviewQuery = useDatabaseOverview();
  const [selectedMetadataTable, setSelectedMetadataTable] = useState<string | null>(null);
  const metadataQuery = useTableMetadata(selectedMetadataTable);
  const metadataBootstrapping =
    selectedMetadataTable !== null && metadataQuery.isLoading && !metadataQuery.data;

  useEffect(() => {
    if (!selectedMetadataTable && (tablesQuery.data?.length ?? 0) > 0) {
      setSelectedMetadataTable(tablesQuery.data?.[0].table_name ?? null);
    }
  }, [selectedMetadataTable, tablesQuery.data]);

  if (categoriesQuery.isLoading || tablesQuery.isLoading || overviewQuery.isLoading || metadataBootstrapping) {
    return (
      <div className="loading-block">
        <Spin />
      </div>
    );
  }

  if (categoriesQuery.isError || tablesQuery.isError || overviewQuery.isError) {
    return <Alert message="数据库元信息加载失败" showIcon type="error" />;
  }

  return (
    <SchemaOverview
      metadata={metadataQuery.data ?? null}
      onInspectTable={setSelectedMetadataTable}
      onOpenTableDetail={openTableDetail}
      overview={overviewQuery.data ?? { table_count: 0, runtime_table_count: 0, category_counts: {} }}
      selectedTable={selectedMetadataTable}
      tables={tablesQuery.data ?? []}
    />
  );
};

export default DatabaseMetadataPage;
