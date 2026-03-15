import { StockDetailPageClient } from "@/features/stock-detail/StockDetailPageClient";


export default async function StockDetailPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const resolvedParams = await params;
  return <StockDetailPageClient code={resolvedParams.code} />;
}
