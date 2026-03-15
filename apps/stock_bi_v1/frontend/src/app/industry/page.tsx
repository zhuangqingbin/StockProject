import { IndustryPageClient } from "@/features/industry/IndustryPageClient";


export default async function IndustryPage({
  searchParams,
}: {
  searchParams: Promise<{ name?: string }>;
}) {
  const resolvedSearchParams = await searchParams;
  return <IndustryPageClient industryName={resolvedSearchParams.name ?? "银行"} />;
}
