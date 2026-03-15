"use client";

import { DashboardView } from "@/features/dashboard/DashboardView";
import { useDashboardData } from "@/lib/api";


export default function Home() {
  const { overview, northFlow, topList, heatmap } = useDashboardData();

  return (
    <DashboardView overview={overview} northFlow={northFlow} topList={topList} heatmapRows={heatmap} />
  );
}
