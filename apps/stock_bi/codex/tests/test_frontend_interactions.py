import unittest
import json
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def _major_version(spec: str) -> int:
    match = __import__("re").search(r"(\d+)", spec)
    return int(match.group(1)) if match else 0


class FrontendInteractionTest(unittest.TestCase):
    def test_react_runtime_modules_exist(self):
        for relative_path in [
            "src/lib/api/marketApi.ts",
            "src/lib/api/chatApi.ts",
            "src/lib/state/dashboardStore.ts",
            "src/lib/ws/useMarketSocket.ts",
            "src/features/chart-stage/ChartStage.tsx",
            "src/features/chat-console/ChatConsole.tsx",
            "src/features/industry-detail/IndustryDrawer.tsx",
            "src/features/stock-detail/StockDrawer.tsx",
        ]:
            self.assertTrue((FRONTEND_DIR / relative_path).exists(), relative_path)

    def test_react_runtime_contains_expected_markers(self):
        store_content = (FRONTEND_DIR / "src/lib/state/dashboardStore.ts").read_text(encoding="utf-8")
        socket_content = (FRONTEND_DIR / "src/lib/ws/useMarketSocket.ts").read_text(encoding="utf-8")
        chart_stage_content = (FRONTEND_DIR / "src/features/chart-stage/ChartStage.tsx").read_text(encoding="utf-8")
        chat_console_content = (FRONTEND_DIR / "src/features/chat-console/ChatConsole.tsx").read_text(encoding="utf-8")

        self.assertIn("create<DashboardStoreState>()", store_content)
        self.assertIn("new WebSocket(", socket_content)
        self.assertIn('data-testid="chart-stage"', chart_stage_content)
        self.assertIn('data-testid="assistant-console"', chat_console_content)

    def test_chart_stack_is_echarts_only(self):
        package_data = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        north_chart_content = (FRONTEND_DIR / "src/features/chart-stage/NorthTrendChart.tsx").read_text(encoding="utf-8")
        amount_chart_content = (FRONTEND_DIR / "src/features/chart-stage/AmountTrendChart.tsx").read_text(encoding="utf-8")

        self.assertNotIn("@ant-design/charts", package_data["dependencies"])
        self.assertIn("echarts-for-react", package_data["dependencies"])
        self.assertIn("ReactECharts", north_chart_content)
        self.assertIn("ReactECharts", amount_chart_content)
        self.assertNotIn("@ant-design/charts", north_chart_content)
        self.assertNotIn("@ant-design/charts", amount_chart_content)

    def test_chart_runtime_uses_echarts_core_build(self):
        chart_runtime = (FRONTEND_DIR / "src/lib/charts/StockChart.tsx").read_text(encoding="utf-8")
        source_files = sorted((FRONTEND_DIR / "src").rglob("*.tsx"))

        self.assertIn('from "echarts-for-react/lib/core"', chart_runtime)
        self.assertIn("echarts.use([", chart_runtime)

        for path in source_files:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn('from "echarts-for-react";', content, str(path))
            self.assertNotIn("from 'echarts-for-react';", content, str(path))

    def test_heavy_detail_panels_are_lazy_loaded(self):
        market_shell = (FRONTEND_DIR / "src/features/market-overview/MarketShell.tsx").read_text(encoding="utf-8")

        self.assertIn("const IndustryDrawer = lazy(() =>", market_shell)
        self.assertIn('import("../industry-detail/IndustryDrawer")', market_shell)
        self.assertIn("const StockDrawer = lazy(() =>", market_shell)
        self.assertIn('import("../stock-detail/StockDrawer")', market_shell)
        self.assertIn("<Suspense", market_shell)
        self.assertIn("const activeIndustry = useDashboardStore((state) => state.activeIndustry);", market_shell)
        self.assertIn("const activeStock = useDashboardStore((state) => state.activeStock);", market_shell)
        self.assertIn("{activeIndustry ? (", market_shell)
        self.assertIn("{activeStock ? (", market_shell)

    def test_chart_stage_lazily_loads_heavy_views(self):
        chart_stage = (FRONTEND_DIR / "src/features/chart-stage/ChartStage.tsx").read_text(encoding="utf-8")

        self.assertIn("const DistributionChart = lazy(() =>", chart_stage)
        self.assertIn('import("./DistributionChart")', chart_stage)
        self.assertIn("const IndustryTreemap = lazy(() =>", chart_stage)
        self.assertIn('import("./IndustryTreemap")', chart_stage)
        self.assertIn("const RankingTreemap = lazy(() =>", chart_stage)
        self.assertIn('import("./RankingTreemap")', chart_stage)

    def test_trend_charts_wait_for_scroll_activation(self):
        market_shell = (FRONTEND_DIR / "src/features/market-overview/MarketShell.tsx").read_text(encoding="utf-8")
        chart_stage = (FRONTEND_DIR / "src/features/chart-stage/ChartStage.tsx").read_text(encoding="utf-8")

        self.assertTrue(
            (FRONTEND_DIR / "src/lib/viewport/useScrollActivatedVisibility.ts").exists(),
            "src/lib/viewport/useScrollActivatedVisibility.ts",
        )
        self.assertNotIn("fetchNorthMoneyTrend", market_shell)
        self.assertNotIn("fetchAmountTrend", market_shell)
        self.assertIn("useScrollActivatedVisibility", chart_stage)
        self.assertIn("enabled: trendReady", chart_stage)
        self.assertIn("向下滚动以加载趋势图", chart_stage)

    def test_chart_options_are_split_by_chart_type(self):
        option_modules = [
            "src/features/chart-stage/options/distributionOptions.ts",
            "src/features/chart-stage/options/lineOptions.ts",
            "src/features/chart-stage/options/treemapOptions.ts",
            "src/features/chart-stage/options/candleOptions.ts",
        ]
        chart_consumers = [
            "src/features/chart-stage/DistributionChart.tsx",
            "src/features/chart-stage/IndustryTreemap.tsx",
            "src/features/chart-stage/RankingTreemap.tsx",
            "src/features/chart-stage/NorthTrendChart.tsx",
            "src/features/chart-stage/AmountTrendChart.tsx",
            "src/features/industry-detail/IndustryKlinePanel.tsx",
            "src/features/stock-detail/StockKlinePanel.tsx",
        ]

        for relative_path in option_modules:
            self.assertTrue((FRONTEND_DIR / relative_path).exists(), relative_path)

        for relative_path in chart_consumers:
            content = (FRONTEND_DIR / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("from \"./chartOptions\"", content, relative_path)
            self.assertNotIn("from '../chart-stage/chartOptions'", content, relative_path)

    def test_frontend_is_not_coupled_to_antd(self):
        package_data = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        source_files = sorted((FRONTEND_DIR / "src").rglob("*.tsx")) + sorted((FRONTEND_DIR / "src").rglob("*.ts"))

        self.assertNotIn("antd", package_data["dependencies"])

        main_content = (FRONTEND_DIR / "src/main.tsx").read_text(encoding="utf-8")
        self.assertNotIn("antd/dist/reset.css", main_content)

        for path in source_files:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn('from "antd"', content, str(path))
            self.assertNotIn("from 'antd'", content, str(path))

    def test_frontend_toolchain_meets_security_floor(self):
        package_data = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        dev_dependencies = package_data["devDependencies"]

        self.assertGreaterEqual(_major_version(dev_dependencies["vite"]), 8)
        self.assertGreaterEqual(_major_version(dev_dependencies["vitest"]), 4)


if __name__ == "__main__":
    unittest.main()
