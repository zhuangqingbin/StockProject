import type { ComponentProps } from "react";
import ReactEChartsCoreModule from "echarts-for-react/lib/core";
import { CandlestickChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import { resolveReactComponentExport } from "./resolveReactComponentExport";

echarts.use([CandlestickChart, GridComponent, TooltipComponent, CanvasRenderer]);

const ReactEChartsCore = resolveReactComponentExport(ReactEChartsCoreModule);

type StockCandleChartProps = ComponentProps<typeof ReactEChartsCore>;

export const StockCandleChart = (props: StockCandleChartProps) => (
  <ReactEChartsCore echarts={echarts} {...props} />
);
