import { useQuery } from "@tanstack/react-query";

import { fetchDatabaseOverview, fetchTableMetadata } from "../api";

export const useDatabaseOverview = () =>
  useQuery({
    queryKey: ["databaseOverview"],
    queryFn: fetchDatabaseOverview,
  });

export const useTableMetadata = (tableName: string | null) =>
  useQuery({
    queryKey: ["tableMetadata", tableName],
    queryFn: () => fetchTableMetadata(tableName as string),
    enabled: Boolean(tableName),
  });
