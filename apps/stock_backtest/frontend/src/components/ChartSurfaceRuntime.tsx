import { useEffect, useRef } from "react";

import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { init, use, type EChartsCoreOption, type EChartsType } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

use([LineChart, BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

type ChartSurfaceRuntimeProps = {
  option: EChartsCoreOption;
  height: number;
};

export default function ChartSurfaceRuntime({ option, height }: ChartSurfaceRuntimeProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<EChartsType | null>(null);

  useEffect(() => {
    if (!hostRef.current) {
      return undefined;
    }

    const chart = init(hostRef.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;

    const resize = () => {
      chart.resize();
    };
    const resizeObserver = typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(resize);
    resizeObserver?.observe(hostRef.current);
    window.addEventListener("resize", resize);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(option, { lazyUpdate: true, notMerge: true });
    chartRef.current?.resize();
  }, [height, option]);

  return <div className="chart-surface" ref={hostRef} style={{ height }} />;
}
