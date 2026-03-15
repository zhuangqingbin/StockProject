# Stock Backtest Extreme Optimization Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Push the current `stock_backtest` implementation harder on runtime flow and delivery performance by reducing initial frontend cost and trimming backend hot-path overhead.

**Architecture:** Treat optimization as targeted structural work, not cosmetic churn. Split heavy frontend concerns by route and by component boundary, keep preload hooks near navigation, and cache backend template metadata/class loading so repeated API hits and backtest submissions do not keep re-reading strategy files.

**Tech Stack:** React 18, Vite, Vitest, Ant Design, Monaco Editor, ECharts, FastAPI, SQLAlchemy, Backtrader, Python stdlib caching.

### Task 1: Optimization Tests

**Files:**
- Modify: `apps/stock_backtest/tests/test_engine_components.py`
- Create: `apps/stock_backtest/frontend/src/lib/chunkPlan.test.ts`

**Step 1: Write the failing test**
- Add a backend test that asserts strategy template discovery is cached between calls.
- Add a frontend test that asserts node modules are assigned into stable heavy chunks.

**Step 2: Run test to verify it fails**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_engine_components.py -q`
- Run: `cd apps/stock_backtest/frontend && npm test -- src/lib/chunkPlan.test.ts`

**Step 3: Write minimal implementation**
- Add explicit cache helpers in the Python loader.
- Add a shared chunk resolver for Vite.

**Step 4: Run test to verify it passes**
- Re-run both commands and confirm green.

### Task 2: Frontend Delivery Optimization

**Files:**
- Modify: `apps/stock_backtest/frontend/src/App.tsx`
- Modify: `apps/stock_backtest/frontend/src/components/StrategyCodeEditor.tsx`
- Modify: `apps/stock_backtest/frontend/src/components/ChartSurface.tsx`
- Modify: `apps/stock_backtest/frontend/src/components/TopNavigation.tsx`
- Create: `apps/stock_backtest/frontend/src/lib/chunkPlan.ts`
- Modify: `apps/stock_backtest/frontend/vite.config.ts`

**Step 1: Write the failing test**
- Existing chunk-plan test already covers part of the new behavior.

**Step 2: Run test to verify it fails**
- Done in Task 1.

**Step 3: Write minimal implementation**
- Lazy-load route modules and wrap them with a shell fallback.
- Lazy-load Monaco and ECharts behind component-level suspense boundaries.
- Prefetch heavy routes on nav hover/focus.
- Use `manualChunks` to split framework/UI/charts/editor vendors.

**Step 4: Run test to verify it passes**
- Run: `cd apps/stock_backtest/frontend && npm test`
- Run: `cd apps/stock_backtest/frontend && npm run build`

### Task 3: Backend Hot-Path Optimization

**Files:**
- Modify: `apps/stock_backtest/backend/engine/strategy_loader.py`

**Step 1: Write the failing test**
- Existing cache test covers the new behavior.

**Step 2: Run test to verify it fails**
- Done in Task 1.

**Step 3: Write minimal implementation**
- Cache template discovery and loaded template classes.
- Expose cache invalidation for tests and future template refresh flows.

**Step 4: Run test to verify it passes**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_engine_components.py -q`

### Task 4: Verification

**Files:**
- No new files required; record results in planning logs.

**Step 1: Run verification**
- `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests -q`
- `cd apps/stock_backtest/frontend && npm test`
- `cd apps/stock_backtest/frontend && npm run build`

**Step 2: Compare bundle output**
- Note whether the main entry chunk size drops materially after lazy loading and manual chunking.
