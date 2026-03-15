import { create } from "zustand";

type AnalysisState = {
  focusedRunId: number;
  comparisonRunIds: number[];
  setFocusedRunId: (runId: number) => void;
  toggleComparisonRun: (runId: number) => void;
};

export const useAnalysisStore = create<AnalysisState>((set) => ({
  focusedRunId: 0,
  comparisonRunIds: [],
  setFocusedRunId: (focusedRunId) => set({ focusedRunId }),
  toggleComparisonRun: (runId) =>
    set((state) => ({
      comparisonRunIds: state.comparisonRunIds.includes(runId)
        ? state.comparisonRunIds.filter((current) => current !== runId)
        : [...state.comparisonRunIds, runId],
    })),
}));
