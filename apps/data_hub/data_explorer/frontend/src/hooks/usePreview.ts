import { useQuery } from "@tanstack/react-query";

import { fetchTablePreview } from "../api";

export const useTablePreview = (
  tableName: string | null,
  options: {
    page: number;
    pageSize: number;
    filters: Record<string, string>;
    allRows?: boolean;
    enabled?: boolean;
  },
) =>
  useQuery({
    queryKey: ["tablePreview", tableName, options.page, options.pageSize, options.filters, options.allRows],
    queryFn: () =>
      fetchTablePreview(tableName as string, {
        page: options.page,
        pageSize: options.pageSize,
        filters: options.filters,
        allRows: options.allRows,
      }),
    enabled: Boolean(tableName) && (options.enabled ?? true),
  });
