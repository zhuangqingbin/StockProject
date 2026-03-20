# Stock BI V1 Optimization Pass

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the main remaining product gap in `apps/stock_bi_v1` by implementing the real precompute pipeline and surfacing its output through the existing API and dashboard.

**Architecture:** Keep the existing modular FastAPI read API, but add a precompute write path that aggregates raw market tables into `precomputed_market`, `precomputed_industry`, and `precomputed_limit`. Preserve the current frontend shell and only add a thin UI enhancement if it improves visibility of the new backend capability without broad redesign.

**Tech Stack:** Python 3.11-compatible FastAPI, SQLAlchemy, cachetools, pytest, Next.js, React, Tailwind, Vitest

### Task 1: Lock the optimization scope in planning files

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`
- Create: `docs/plans/2026-03-15-stock-bi-v1-optimization-pass.md`

**Step 1: Record the remaining gap**

Write down that `apps/stock_bi_v1/backend/precompute/runner.py` is still a placeholder and that the design doc requires real aggregation into all three precompute tables.

**Step 2: Record the execution sequence**

Capture the intended order: failing tests first, repository/service implementation second, verification last.

### Task 2: Add failing precompute regressions

**Files:**
- Create: `apps/stock_bi_v1/tests/test_precompute_api.py`

**Step 1: Write the failing test**

Add an integration-style test that:
- seeds `daily_kline`, `daily_basic`, `moneyflow`, `moneyflow_hsgt`, `index_daily`, `stock_basic`, and `stock_stk_limit`
- calls `POST /api/precompute/{trade_date}`
- verifies the precompute tables are written with expected aggregates
- verifies `/api/market/overview`, `/api/industry/heatmap`, and `/api/market/limit-list` return the computed results

**Step 2: Run the test to verify RED**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_bi_v1/tests/test_precompute_api.py -q`

Expected: FAIL because the runner is still a no-op.

### Task 3: Implement the real precompute pipeline

**Files:**
- Modify: `apps/stock_bi_v1/backend/precompute/runner.py`
- Create or modify: `apps/stock_bi_v1/backend/precompute/repository.py`
- Modify: `apps/stock_bi_v1/backend/models/db_models.py` only if field naming alignment is required
- Modify: `apps/stock_bi_v1/backend/modules/market/repository.py`
- Modify: `apps/stock_bi_v1/backend/modules/industry/repository.py`

**Step 1: Add minimal write-path repositories**

Create focused repository functions for:
- reading raw rows needed for market, industry, and limit aggregates
- upserting/deleting daily precompute rows
- resolving consecutive limit-up streaks from historical rows

**Step 2: Implement the aggregation**

Compute:
- market distribution, totals, and top lists
- per-industry stats
- limit-up/down lists, broken-board count/rate, and tier stats

**Step 3: Clear caches after write**

Preserve the existing TTL caching model by clearing caches after a successful precompute run.

### Task 4: Add a thin visibility enhancement

**Files:**
- Modify as needed: `apps/stock_bi_v1/frontend/src/lib/types.ts`
- Modify as needed: `apps/stock_bi_v1/frontend/src/features/dashboard/DashboardView.tsx`
- Modify as needed: `apps/stock_bi_v1/frontend/src/features/dashboard/DashboardView.test.tsx`

**Step 1: Add a small dashboard signal**

If the backend contract already exposes enough information, show a compact precompute freshness/readiness hint on the dashboard using the existing `trade_date` and limit/heatmap sections. Skip broader UI work if it does not materially improve usability.

**Step 2: Add or update a focused test**

Keep this regression narrow and avoid redesigning unrelated pages.

### Task 5: Verify the optimization pass

**Files:**
- Modify as needed: touched files above

**Step 1: Run backend tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_bi_v1/tests -q`

**Step 2: Run frontend tests**

Run: `cd apps/stock_bi_v1/frontend && npm test`

**Step 3: Run lint and production build**

Run:
- `cd apps/stock_bi_v1/frontend && npm run lint`
- `cd apps/stock_bi_v1/frontend && npm run build`
