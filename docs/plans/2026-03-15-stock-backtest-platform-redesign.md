# Stock Backtest Platform Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework `apps/stock_backtest` from a thin showcase into a more complete quant workbench with a one-command launcher, a broader product surface, richer market-data entry points, and a usable backtest launch flow.

**Architecture:** Keep the current FastAPI + Backtrader + React foundation, but expand the surface area around it instead of replacing the stack. Backend changes stay inside `apps/stock_backtest/backend` with small additions to the data module and strategy bootstrap flow; frontend changes extend the existing lazy-loaded route system into a fuller workbench with a dashboard, data lab, strategy studio, launch pad, analysis, compare, and research entry points.

**Tech Stack:** Python 3.9+, FastAPI, SQLAlchemy 2, Pydantic v2, Backtrader, React 18, TypeScript, Vite, TanStack Query, Zustand, ECharts core, app-local UI primitives.

### Task 1: Redesign Plan And Product Surface

**Files:**
- Create: `docs/plans/2026-03-15-stock-backtest-platform-redesign.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Step 1: Write the design and scope**
- Define the new information architecture: dashboard, data lab, strategy studio, launch pad, analysis, compare, research.
- Record why the current product feels thin even though engine primitives already exist.

**Step 2: Save the plan and assumptions**
- Document the minimal backend APIs needed to support the expanded surface.
- Record launcher and template-sync expectations so implementation stays bounded.

### Task 2: Backend Red Tests For Expanded Platform Data

**Files:**
- Modify: `apps/stock_backtest/tests/test_api_flows.py`
- Modify: `apps/stock_backtest/tests/test_engine_components.py`
- Modify: `apps/stock_backtest/tests/test_settings.py`

**Step 1: Write the failing tests**
- Add coverage for expanded built-in templates.
- Add API tests for market-data overview, benchmark catalog, and richer universe search/filter behavior.
- Add a launcher-focused regression for stale-process handling if it can be validated at the helper level.

**Step 2: Run tests to verify they fail**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_engine_components.py apps/stock_backtest/tests/test_api_flows.py apps/stock_backtest/tests/test_settings.py -q`
- Expected: failures caused by missing templates, missing data routes, and missing bootstrap behavior.

### Task 3: Backend Implementation For Usability

**Files:**
- Modify: `apps/stock_backtest/run.sh`
- Modify: `apps/stock_backtest/backend/models/api_models.py`
- Modify: `apps/stock_backtest/backend/modules/data/router.py`
- Modify: `apps/stock_backtest/backend/modules/strategy/service.py`
- Modify: `apps/stock_backtest/backend/modules/strategy/repository.py`
- Modify: `apps/stock_backtest/backend/main.py`
- Create: `apps/stock_backtest/templates/rsi_rotation.py`
- Create: `apps/stock_backtest/templates/bollinger_reversion.py`
- Create: `apps/stock_backtest/templates/volume_breakout.py`
- Create: `apps/stock_backtest/templates/atr_trend_following.py`

**Step 1: Write minimal implementation**
- Fold stale `uvicorn` cleanup into `run.sh` so backend startup is single-command.
- Expand built-in template catalog and sync missing system templates into the app database without overwriting user-owned records.
- Expose market overview, benchmark list, and richer universe endpoints sourced from the existing MySQL tables.

**Step 2: Run backend tests**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_engine_components.py apps/stock_backtest/tests/test_api_flows.py apps/stock_backtest/tests/test_settings.py -q`
- Expected: PASS.

### Task 4: Frontend Red Tests For A Real Workbench

**Files:**
- Modify: `apps/stock_backtest/frontend/src/test/app.test.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/BacktestControlPage.test.tsx`

**Step 1: Write the failing tests**
- Assert the new dashboard/data-lab navigation exists.
- Assert the launch pad can fill a real request and submit it through the client.
- Assert expanded template catalog and data-lab content render from live/demo data.

**Step 2: Run tests to verify they fail**
- Run: `cd apps/stock_backtest/frontend && npm test`
- Expected: failures due to missing routes, missing client methods, and missing UI sections.

### Task 5: Frontend Implementation For The Redesigned Platform

**Files:**
- Modify: `apps/stock_backtest/frontend/src/App.tsx`
- Modify: `apps/stock_backtest/frontend/src/lib/routeModules.tsx`
- Modify: `apps/stock_backtest/frontend/src/components/TopNavigation.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/StrategyStudioPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/BacktestControlPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/pages/NotebookPage.tsx`
- Create: `apps/stock_backtest/frontend/src/pages/DashboardPage.tsx`
- Create: `apps/stock_backtest/frontend/src/pages/DataLabPage.tsx`
- Modify: `apps/stock_backtest/frontend/src/services/client.ts`
- Modify: `apps/stock_backtest/frontend/src/services/types.ts`
- Modify: `apps/stock_backtest/frontend/src/services/demoData.ts`
- Modify: `apps/stock_backtest/frontend/src/styles/app.css`

**Step 1: Write minimal implementation**
- Add a dashboard route as the control tower for strategies, runs, and data coverage.
- Add a data-lab route backed by the new APIs.
- Rework strategy and run pages into a fuller workflow with template gallery, data requirements, and an actual submit path for backtests.
- Preserve the existing visual direction while making the interface feel more like a quant desk than a static demo.

**Step 2: Run frontend tests**
- Run: `cd apps/stock_backtest/frontend && npm test`
- Expected: PASS.

### Task 6: Full Verification And Handoff

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`
- Modify: `apps/stock_backtest/README.md`

**Step 1: Run full verification**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests -q`
- Run: `cd apps/stock_backtest/frontend && npm test`
- Run: `cd apps/stock_backtest/frontend && npm run build`

**Step 2: Record outcomes**
- Update planning files with what changed, what was verified, and any remaining product gaps.
- Refresh README startup guidance if launcher behavior changed.
