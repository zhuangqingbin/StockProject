"use client";

import { LimitView } from "@/features/limit/LimitView";
import { useLimitData } from "@/lib/api";


export default function LimitPage() {
  const { limitStats, limitList } = useLimitData();
  return <LimitView limitStats={limitStats} limitList={limitList} />;
}
