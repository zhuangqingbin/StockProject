import { useQuery } from "@tanstack/react-query";

import { fetchCategories, fetchTableDetail, fetchTablesByCategory } from "../api";

export const useCategories = () =>
  useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

export const useCategoryTables = (categoryKey: string) =>
  useQuery({
    queryKey: ["categoryTables", categoryKey],
    queryFn: () => fetchTablesByCategory(categoryKey),
    enabled: Boolean(categoryKey),
  });

export const useTableDetail = (tableName: string | null) =>
  useQuery({
    queryKey: ["tableDetail", tableName],
    queryFn: () => fetchTableDetail(tableName as string),
    enabled: Boolean(tableName),
  });
