import { create } from "zustand";

import type { AppPage } from "../types";

export type MonitorView = "overview" | "datasets" | "jobs" | "runs";
export type TableDetailTab = "structure" | "preview" | "runs";

type NavigationState = {
  currentPage: AppPage;
  selectedCategory: string;
  selectedTable: string | null;
  directorySearch: string;
  monitorStatusFilter: string;
  monitorView: MonitorView;
  tableDetailTab: TableDetailTab;
  setCurrentPage: (page: AppPage) => void;
  setSelectedCategory: (category: string) => void;
  setSelectedTable: (tableName: string | null) => void;
  setDirectorySearch: (value: string) => void;
  setMonitorStatusFilter: (value: string) => void;
  setMonitorView: (value: MonitorView) => void;
  setTableDetailTab: (value: TableDetailTab) => void;
  openTableDetail: (tableName: string) => void;
};

export const useNavigationStore = create<NavigationState>((set) => ({
  currentPage: "directory",
  selectedCategory: "basic_data",
  selectedTable: null,
  directorySearch: "",
  monitorStatusFilter: "all",
  monitorView: "overview",
  tableDetailTab: "structure",
  setCurrentPage: (currentPage) => set({ currentPage }),
  setSelectedCategory: (selectedCategory) => set({ currentPage: "directory", selectedCategory, selectedTable: null }),
  setSelectedTable: (selectedTable) => set({ selectedTable }),
  setDirectorySearch: (directorySearch) => set({ directorySearch }),
  setMonitorStatusFilter: (monitorStatusFilter) => set({ monitorStatusFilter }),
  setMonitorView: (monitorView) => set({ monitorView }),
  setTableDetailTab: (tableDetailTab) => set({ tableDetailTab }),
  openTableDetail: (tableName) => set({ currentPage: "directory", selectedTable: tableName, tableDetailTab: "structure" }),
}));
