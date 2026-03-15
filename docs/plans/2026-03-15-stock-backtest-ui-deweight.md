# Stock Backtest UI Deweight Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the remaining heavy Ant Design footprint from `apps/stock_backtest/frontend` while preserving the current visual direction and interaction flow.

**Architecture:** Replace shallow Ant Design usage with a small app-local UI layer built from semantic React components and CSS already aligned with the existing visual system. Keep behavior stable by adding focused regression tests first, then swap page usage one surface at a time, then remove the unused dependency and simplify chunking.

**Tech Stack:** React 18, Vite, Vitest, CSS modules-in-file via `app.css`, TanStack Query, Zustand.

### Task 1: Lock Behavior With Tests

**Files:**
- Modify: `apps/stock_backtest/frontend/src/test/app.test.tsx`
- Create: `apps/stock_backtest/frontend/src/components/ui.test.tsx`

**Step 1: Write the failing test**
- Add an app-level regression test for the analysis page tab switch behavior.
- Add a component-level test for the lightweight UI tabs/button/progress primitives that will replace Ant Design.

**Step 2: Run test to verify it fails**
- Run: `cd apps/stock_backtest/frontend && npm test -- src/test/app.test.tsx src/components/ui.test.tsx`

**Step 3: Write minimal implementation**
- Keep the tests focused on interaction behavior, not implementation details.

**Step 4: Run test to verify it passes**
- Re-run the same command and confirm green.

### Task 2: Replace Ant Design With App-Local UI

**Files:**
- Modify: `apps/stock_backtest/frontend/src/App.tsx`
- Create: `apps/stock_backtest/frontend/src/components/ui.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/StrategyStudioPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/BacktestControlPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/AnalysisPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/ComparisonPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/NotebookPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/styles/app.css`

**Step 1: Write the failing test**
- Covered by Task 1.

**Step 2: Run test to verify it fails**
- Covered by Task 1.

**Step 3: Write minimal implementation**
- Build small local components for button, status tag, progress bar, data table, and tabs.
- Remove `ConfigProvider` and rely on the existing CSS visual language.
- Swap all page imports from `antd` to the new app-local UI layer.

**Step 4: Run test to verify it passes**
- Run: `cd apps/stock_backtest/frontend && npm test -- src/test/app.test.tsx src/components/ui.test.tsx`

### Task 3: Remove Dead Dependencies and Chunk Rules

**Files:**
- Modify: `apps/stock_backtest/frontend/package.json`
- Modify: `apps/stock_backtest/frontend/package-lock.json`
- Modify: `apps/stock_backtest/frontend/src/lib/chunkPlan.ts`
- Modify: `apps/stock_backtest/frontend/src/lib/chunkPlan.test.ts`

**Step 1: Write the failing test**
- Extend chunk-plan coverage to assert Ant Design no longer maps into a dedicated UI chunk.

**Step 2: Run test to verify it fails**
- Run: `cd apps/stock_backtest/frontend && npm test -- src/lib/chunkPlan.test.ts`

**Step 3: Write minimal implementation**
- Remove the Ant Design dependency.
- Delete the dedicated UI chunk rule if it is no longer needed.
- Keep manual chunks only for the still-heavy editor/framework/chart buckets.

**Step 4: Run test to verify it passes**
- Re-run the same command and confirm green.

### Task 4: Verify and Compare

**Files:**
- Update: `progress.md`
- Update: `findings.md`

**Step 1: Run verification**
- `cd apps/stock_backtest/frontend && npm test`
- `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests -q`
- `cd apps/stock_backtest/frontend && npm run build`

**Step 2: Compare bundle output**
- Record the new chunk sizes and confirm whether the dedicated `ui` chunk disappeared or materially shrank.
