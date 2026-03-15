"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";
import { BarChart, CandlestickChart, LineChart, TreemapChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { init, use as registerEcharts } from "echarts/core";

registerEcharts([BarChart, CandlestickChart, GridComponent, LegendComponent, LineChart, TooltipComponent, TreemapChart, CanvasRenderer]);

type TerminalChartProps = {
  option: EChartsOption;
  height?: number;
  onChartClick?: (params: { name?: string | number; value?: unknown; data?: unknown }) => void;
};


export const TerminalChart = ({ option, height = 240, onChartClick }: TerminalChartProps) => {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current || typeof navigator !== "undefined" && navigator.userAgent.includes("jsdom")) {
      return;
    }

    const chart = init(chartRef.current);
    chart.setOption(option);
    const clickHandler = (params: { name?: string | number; value?: unknown; data?: unknown }) => {
      onChartClick?.(params);
    };
    if (onChartClick) {
      chart.on("click", clickHandler);
    }

    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      if (onChartClick) {
        chart.off("click", clickHandler);
      }
      chart.dispose();
    };
  }, [onChartClick, option]);

  return <div ref={chartRef} data-testid="terminal-chart" style={{ height }} className={onChartClick ? "w-full cursor-pointer" : "w-full"} />;
};
