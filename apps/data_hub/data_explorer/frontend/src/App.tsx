import { App as AntdApp, Layout, Space, Typography, Button } from "antd";
import { Suspense, lazy, useEffect, useRef } from "react";

import CategoryTree from "./components/CategoryTree";
import { useCategories } from "./hooks/useCatalog";
import { useNavigationStore } from "./stores/navigationStore";
import type { AppPage } from "./types";

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;
const DirectoryPage = lazy(() => import("./pages/DirectoryPage"));
const TableDetailPage = lazy(() => import("./pages/TableDetailPage"));
const MonitorPage = lazy(() => import("./pages/MonitorPage"));
const DatabaseMetadataPage = lazy(() => import("./pages/DatabaseMetadataPage"));

const pageLabels: Record<AppPage, string> = {
  directory: "数据目录",
  monitor: "运维监控",
  databaseMetadata: "数据库元信息",
};

const App = () => {
  const currentPage = useNavigationStore((state) => state.currentPage);
  const selectedCategory = useNavigationStore((state) => state.selectedCategory);
  const selectedTable = useNavigationStore((state) => state.selectedTable);
  const directorySearch = useNavigationStore((state) => state.directorySearch);
  const monitorStatusFilter = useNavigationStore((state) => state.monitorStatusFilter);
  const monitorView = useNavigationStore((state) => state.monitorView);
  const tableDetailTab = useNavigationStore((state) => state.tableDetailTab);
  const setCurrentPage = useNavigationStore((state) => state.setCurrentPage);
  const setSelectedCategory = useNavigationStore((state) => state.setSelectedCategory);
  const categoriesQuery = useCategories();
  const urlHydrated = useRef(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const page = params.get("page");
    const category = params.get("category");
    const table = params.get("table");
    const directoryQuery = params.get("q");
    const status = params.get("status");
    const view = params.get("view");
    const tab = params.get("tab");

    useNavigationStore.setState((state) => ({
      ...state,
      currentPage:
        page === "directory" || page === "monitor" || page === "databaseMetadata"
          ? page
          : state.currentPage,
      selectedCategory: category || state.selectedCategory,
      selectedTable: table || state.selectedTable,
      directorySearch: directoryQuery ?? state.directorySearch,
      monitorStatusFilter: status ?? state.monitorStatusFilter,
      monitorView:
        view === "overview" || view === "datasets" || view === "jobs" || view === "runs"
          ? view
          : state.monitorView,
      tableDetailTab: tab === "structure" || tab === "preview" || tab === "runs" ? tab : state.tableDetailTab,
    }));
    urlHydrated.current = true;
  }, []);

  useEffect(() => {
    if (!urlHydrated.current) {
      return;
    }

    const params = new URLSearchParams();
    params.set("page", currentPage);
    params.set("category", selectedCategory);
    if (selectedTable) {
      params.set("table", selectedTable);
      params.set("tab", tableDetailTab);
    }
    if (directorySearch.trim()) {
      params.set("q", directorySearch.trim());
    }
    if (monitorStatusFilter !== "all") {
      params.set("status", monitorStatusFilter);
    }
    if (currentPage === "monitor") {
      params.set("view", monitorView);
    }

    const query = params.toString();
    const nextUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    window.history.replaceState(null, "", nextUrl);
  }, [
    currentPage,
    directorySearch,
    monitorStatusFilter,
    monitorView,
    selectedCategory,
    selectedTable,
    tableDetailTab,
  ]);

  const showCategorySidebar = currentPage !== "monitor";

  return (
    <AntdApp>
      <Layout className="app-shell">
        <Header className="topbar">
          <div>
            <Text className="eyebrow">只读数据库看板</Text>
            <Title level={3} className="title">
              data_explorer
            </Title>
          </div>
          <Space>
            {Object.entries(pageLabels).map(([page, label]) => (
              <Button
                key={page}
                onClick={() => setCurrentPage(page as AppPage)}
                type={currentPage === page ? "primary" : "default"}
              >
                {label}
              </Button>
            ))}
          </Space>
        </Header>
        <Layout>
          {showCategorySidebar ? (
            <Sider width={300} className="sidebar">
              <div className="sidebar-header">
                <Text className="sidebar-title">TuShare 分类树</Text>
                <Text type="secondary">
                  {currentPage === "databaseMetadata" ? "结构与治理入口" : "按分类进入数据资产"}
                </Text>
              </div>
              <CategoryTree
                categories={categoriesQuery.data ?? []}
                loading={categoriesQuery.isLoading}
                onSelect={setSelectedCategory}
                selectedCategory={selectedCategory}
              />
            </Sider>
          ) : null}
          <Content className={`content ${showCategorySidebar ? "" : "content-full"}`.trim()}>
            <Suspense fallback={<div className="loading-block">加载中...</div>}>
              {currentPage === "directory" && selectedTable ? <TableDetailPage tableName={selectedTable} /> : null}
              {currentPage === "directory" && !selectedTable ? <DirectoryPage /> : null}
              {currentPage === "monitor" ? <MonitorPage /> : null}
              {currentPage === "databaseMetadata" ? <DatabaseMetadataPage /> : null}
            </Suspense>
          </Content>
        </Layout>
      </Layout>
    </AntdApp>
  );
};

export default App;
