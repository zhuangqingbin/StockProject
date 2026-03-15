import { lazy } from "react";
import type { ComponentType, LazyExoticComponent } from "react";

type RouteLoader = () => Promise<{ [key: string]: ComponentType<any> }>;

type RouteDefinition = {
  path: string;
  label: string;
  component: LazyExoticComponent<ComponentType<any>>;
  preload: () => Promise<void>;
};

const toLazyRoute = (loader: RouteLoader, exportName: string) => {
  const component = lazy(async () => {
    const module = await loader();
    return { default: module[exportName] };
  });

  const preload = async () => {
    await loader();
  };

  return { component, preload };
};

const dashboardRoute = toLazyRoute(() => import("../pages/DashboardPage"), "DashboardPage");
const dataLabRoute = toLazyRoute(() => import("../pages/DataLabPage"), "DataLabPage");
const strategyStudioRoute = toLazyRoute(() => import("../pages/StrategyStudioPage"), "StrategyStudioPage");
const backtestControlRoute = toLazyRoute(() => import("../pages/BacktestControlPage"), "BacktestControlPage");
const analysisRoute = toLazyRoute(() => import("../pages/AnalysisPage"), "AnalysisPage");
const comparisonRoute = toLazyRoute(() => import("../pages/ComparisonPage"), "ComparisonPage");
const notebookRoute = toLazyRoute(() => import("../pages/NotebookPage"), "NotebookPage");

export const appRoutes: RouteDefinition[] = [
  { path: "/dashboard", label: "总览塔台", component: dashboardRoute.component, preload: dashboardRoute.preload },
  { path: "/data", label: "数据实验室", component: dataLabRoute.component, preload: dataLabRoute.preload },
  { path: "/strategies", label: "策略工坊", component: strategyStudioRoute.component, preload: strategyStudioRoute.preload },
  { path: "/runs", label: "回测发射台", component: backtestControlRoute.component, preload: backtestControlRoute.preload },
  { path: "/analysis", label: "结果分析", component: analysisRoute.component, preload: analysisRoute.preload },
  { path: "/compare", label: "策略对比", component: comparisonRoute.component, preload: comparisonRoute.preload },
  { path: "/notebook", label: "研究入口", component: notebookRoute.component, preload: notebookRoute.preload },
];
