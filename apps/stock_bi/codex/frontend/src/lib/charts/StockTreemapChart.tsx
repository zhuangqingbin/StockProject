import type { ComponentProps } from "react";
import ReactEChartsCoreModule from "echarts-for-react/lib/core";
import { TreemapChart } from "echarts/charts";
import { TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import { resolveReactComponentExport } from "./resolveReactComponentExport";

echarts.use([TreemapChart, TooltipComponent, CanvasRenderer]);

const ReactEChartsCore = resolveReactComponentExport(ReactEChartsCoreModule);

type StockTreemapChartProps = ComponentProps<typeof ReactEChartsCore>;

export const StockTreemapChart = (props: StockTreemapChartProps) => (
  <ReactEChartsCore echarts={echarts} {...props} />
);
