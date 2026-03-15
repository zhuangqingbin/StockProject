import { Suspense, lazy } from "react";
import type { EChartsCoreOption } from "echarts/core";

type ChartSurfaceProps = {
  title: string;
  option: EChartsCoreOption;
  height?: number;
};

const ChartSurfaceRuntime = lazy(() => import("./ChartSurfaceRuntime"));

const ChartSurfaceFallback = ({ title, height = 280 }: Pick<ChartSurfaceProps, "title" | "height">) => (
  <div aria-label={title} className="chart-surface__placeholder" role="img" style={{ height }}>
    <span>{title}</span>
  </div>
);

export const ChartSurface = ({ title, option, height = 280 }: ChartSurfaceProps) => {
  if (import.meta.env.MODE === "test") {
    return <ChartSurfaceFallback height={height} title={title} />;
  }

  return (
    <Suspense fallback={<ChartSurfaceFallback height={height} title={title} />}>
      <ChartSurfaceRuntime height={height} option={option} />
    </Suspense>
  );
};
