import axios from "axios";

import type {
  CategorySummary,
  DatabaseOverview,
  JobMonitorRow,
  MonitorOverview,
  PipelineRunRow,
  PreviewResponse,
  TableDetail,
  TableListItem,
  TableMetadataDetail,
  TableMonitorRow,
} from "./types";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 10000
});

export const fetchCategories = async (): Promise<CategorySummary[]> => {
  const response = await apiClient.get<CategorySummary[]>("/catalog/categories");
  return response.data;
};

export const fetchTablesByCategory = async (categoryKey: string): Promise<TableListItem[]> => {
  const response = await apiClient.get<TableListItem[]>(`/catalog/categories/${categoryKey}/tables`);
  return response.data;
};

export const fetchTableDetail = async (tableName: string): Promise<TableDetail> => {
  const response = await apiClient.get<TableDetail>(`/catalog/tables/${tableName}`);
  return response.data;
};

export const fetchTablePreview = async (
  tableName: string,
  options: {
    page: number;
    pageSize: number;
    filters: Record<string, string>;
    allRows?: boolean;
  },
): Promise<PreviewResponse> => {
  const response = await apiClient.get<PreviewResponse>(`/preview/${tableName}`, {
    params: {
      page: options.page,
      page_size: options.pageSize,
      all_rows: options.allRows,
      ...options.filters,
    },
  });
  return response.data;
};

export const fetchMonitorTables = async (): Promise<TableMonitorRow[]> => {
  const response = await apiClient.get<TableMonitorRow[]>("/monitor/tables");
  return response.data;
};

export const fetchMonitorOverview = async (): Promise<MonitorOverview> => {
  const response = await apiClient.get<MonitorOverview>("/monitor/overview");
  return response.data;
};

export const fetchMonitorJobs = async (): Promise<JobMonitorRow[]> => {
  const response = await apiClient.get<JobMonitorRow[]>("/monitor/jobs");
  return response.data;
};

export const fetchMonitorRuns = async (): Promise<PipelineRunRow[]> => {
  const response = await apiClient.get<PipelineRunRow[]>("/monitor/runs");
  return response.data;
};

export const fetchDatabaseOverview = async (): Promise<DatabaseOverview> => {
  const response = await apiClient.get<DatabaseOverview>("/database/overview");
  return response.data;
};

export const fetchTableMetadata = async (tableName: string): Promise<TableMetadataDetail> => {
  const response = await apiClient.get<TableMetadataDetail>(`/database/tables/${tableName}/metadata`);
  return response.data;
};
