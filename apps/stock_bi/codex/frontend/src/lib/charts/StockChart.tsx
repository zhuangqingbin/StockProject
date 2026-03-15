import type { ComponentProps } from "react";
import ReactEChartsCoreModule from "echarts-for-react/lib/core";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import { resolveReactComponentExport } from "./resolveReactComponentExport";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

const ReactEChartsCore = resolveReactComponentExport(ReactEChartsCoreModule);

type StockChartProps = ComponentProps<typeof ReactEChartsCore>;

export const StockChart = (props: StockChartProps) => <ReactEChartsCore echarts={echarts} {...props} />;
