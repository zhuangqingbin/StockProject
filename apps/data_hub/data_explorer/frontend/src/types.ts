export type AppPage = "directory" | "monitor" | "databaseMetadata";

export type DatasetFreshness = "normal" | "delayed" | "no_data" | "error" | "manual" | string;
export type JobRunResult = "success" | "failed" | "skipped" | string;
export type PipelineRunStatus = "success" | "failed" | "partial_failed" | string;

export type CategorySummary = {
  key: string;
  label: string;
  table_count: number;
};

export type TableListItem = {
  table_name: string;
  category: string;
  description: string;
  api_name?: string;
  api_url?: string;
  row_count: number;
  earliest_data_date: string | null;
  latest_data_date: string | null;
  last_updated: string | null;
  status: DatasetFreshness;
  job_name?: string;
  job_description?: string;
  trigger_profile?: string;
};

export type TableColumn = {
  name: string;
  label?: string | null;
  type: string;
  nullable?: boolean;
  default?: string | null;
  comment?: string | null;
};

export type TableIndex = {
  name: string;
  columns: string[];
  unique?: boolean;
  primary?: boolean;
};

export type TableConstraint = {
  name: string;
  type?: string;
  columns?: string[];
};

export type TableDetail = {
  table_name: string;
  category: string;
  description: string;
  api_name?: string;
  api_url?: string;
  job_name?: string;
  job_description?: string;
  trigger_profile?: string;
  summary: {
    row_count: number;
    earliest_data_date: string | null;
    latest_data_date: string | null;
    last_updated: string | null;
    status: DatasetFreshness;
  };
  structure: {
    columns: TableColumn[];
    indexes: TableIndex[];
    constraints: TableConstraint[];
    ddl: string;
  };
  recent_runs: TableRecentRun[];
};

export type PreviewResponse = {
  table_name: string;
  page: number;
  page_size: number;
  total: number;
  all_rows?: boolean;
  displayed_rows?: number;
  truncated?: boolean;
  truncated_limit?: number | null;
  columns?: string[];
  data: Array<Record<string, unknown>>;
  filters: Record<string, string>;
};

export type TableMonitorRow = {
  table_name: string;
  category: string;
  latest_data_date: string | null;
  last_updated: string | null;
  freshness: DatasetFreshness;
  trigger_profile?: string;
  last_run_result?: JobRunResult | null;
  last_run_id?: string | null;
};

export type JobMonitorRow = {
  run_id: string | null;
  run_mode?: string | null;
  trigger_profile?: string | null;
  job_name: string;
  table_name: string;
  result: JobRunResult | null;
  effective_date?: string | null;
  executed_at: string | null;
  duration_seconds: number | null;
  rows_written?: number | null;
  error: string | null;
};

export type PipelineRunRow = {
  run_id: string;
  run_mode: string;
  status: PipelineRunStatus;
  trigger_profiles: string[];
  job_count: number;
  failed_jobs: number;
  successful_jobs: number;
  table_count: number;
  effective_window: string;
  started_at: string | null;
  ended_at: string | null;
};

export type MonitorOverview = {
  dataset_count: number;
  fresh_datasets: number;
  delayed_datasets: number;
  error_datasets: number;
  manual_datasets: number;
  no_data_datasets: number;
  recent_failed_jobs: number;
  recent_runs: number;
  latest_run: PipelineRunRow | null;
};

export type TableRecentRun = {
  run_id: string | null;
  run_mode?: string | null;
  trigger_profile?: string | null;
  job_name: string;
  result: JobRunResult | null;
  effective_date?: string | null;
  executed_at: string | null;
  duration_seconds: number | null;
  rows_written?: number | null;
  error: string | null;
};

export type DatabaseOverview = {
  schema_name?: string;
  table_count: number;
  runtime_table_count: number;
  category_counts: Record<string, number>;
};

export type TableMetadataDetail = {
  table_name?: string;
  columns: TableColumn[];
  indexes: TableIndex[];
  constraints: TableConstraint[];
  ddl: string;
};
