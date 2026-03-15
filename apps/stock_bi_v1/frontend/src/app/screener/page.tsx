"use client";

import { ScreenerView } from "@/features/screener/ScreenerView";
import { useScreenerData } from "@/lib/api";


export default function ScreenerPage() {
  const { filters, initialResults } = useScreenerData();
  return <ScreenerView filters={filters} initialResults={initialResults} />;
}
