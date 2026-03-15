import { create } from "zustand";

type EditorMode = "template" | "code";

type StrategyStudioState = {
  activeStrategyId: number;
  editorMode: EditorMode;
  setActiveStrategyId: (strategyId: number) => void;
  setEditorMode: (mode: EditorMode) => void;
};

export const useStrategyStudioStore = create<StrategyStudioState>((set) => ({
  activeStrategyId: 1,
  editorMode: "template",
  setActiveStrategyId: (activeStrategyId) => set({ activeStrategyId }),
  setEditorMode: (editorMode) => set({ editorMode }),
}));
