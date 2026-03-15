"use client";

import { IndustryView } from "@/features/industry/IndustryView";
import { useIndustryData } from "@/lib/api";


export const IndustryPageClient = ({ industryName }: { industryName: string }) => {
  const { detail, stocks } = useIndustryData(industryName);
  return <IndustryView detail={detail} stocks={stocks} />;
};
