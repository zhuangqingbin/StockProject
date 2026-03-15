"use client";

import { FlowView } from "@/features/flow/FlowView";
import { useDashboardData } from "@/lib/api";


export default function FlowPage() {
  const { northFlow } = useDashboardData();
  return <FlowView rows={northFlow} />;
}
