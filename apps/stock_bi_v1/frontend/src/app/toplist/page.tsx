"use client";

import { ToplistView } from "@/features/toplist/ToplistView";
import { useToplistData } from "@/lib/api";


export default function ToplistPage() {
  const { data } = useToplistData();
  return <ToplistView rows={data ?? []} />;
}
