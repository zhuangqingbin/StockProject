import { useQuery } from "@tanstack/react-query";

import { fetchMonitorJobs, fetchMonitorOverview, fetchMonitorRuns, fetchMonitorTables } from "../api";

export const useMonitorOverview = () =>
  useQuery({
    queryKey: ["monitor", "overview"],
    queryFn: fetchMonitorOverview,
  });

export const useTableMonitor = () =>
  useQuery({
    queryKey: ["monitor", "tables"],
    queryFn: fetchMonitorTables,
  });

export const useJobMonitor = () =>
  useQuery({
    queryKey: ["monitor", "jobs"],
    queryFn: fetchMonitorJobs,
  });

export const usePipelineRuns = () =>
  useQuery({
    queryKey: ["monitor", "runs"],
    queryFn: fetchMonitorRuns,
  });
