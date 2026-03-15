# Stock Backtest Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-style `apps/stock_backtest` application with a FastAPI backend, a Backtrader-oriented execution core, and a polished React frontend for strategy management, backtest execution, and result analysis.

**Architecture:** Keep the app self-contained under `apps/stock_backtest` with clear boundaries between API routers, services, repositories, and engine helpers. Use shared config/database primitives from `shared/stock_core`, but keep backtest-specific domain models and UI state local to the new app. Support production MySQL by default and SQLite-based tests through configurable URLs.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2, Pandas, Backtrader, React 18, TypeScript, Vite, Ant Design 5, ECharts, Zustand, TanStack Query, Monaco Editor, Vitest.

### Task 1: Backend Skeleton And Configuration

**Files:**
- Create: `apps/stock_backtest/backend/main.py`
- Create: `apps/stock_backtest/backend/infrastructure/settings.py`
- Create: `apps/stock_backtest/backend/infrastructure/database.py`
- Create: `apps/stock_backtest/tests/test_settings.py`

**Step 1: Write the failing test**
- Add tests that assert environment-driven settings, test DB URL overrides, and app metadata/health behavior.

**Step 2: Run test to verify it fails**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_settings.py -q`
- Expected: import or module-not-found failures before implementation.

**Step 3: Write minimal implementation**
- Add settings and DB helpers that default to shared MySQL config but allow `STOCK_BACKTEST_DATABASE_URL`.
- Add a FastAPI app factory with `/health` and static frontend serving hooks.

**Step 4: Run test to verify it passes**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_settings.py -q`
- Expected: PASS.

### Task 2: Strategy Templates, Metrics, And Engine Helpers

**Files:**
- Create: `apps/stock_backtest/backend/engine/data_registry.py`
- Create: `apps/stock_backtest/backend/engine/metrics.py`
- Create: `apps/stock_backtest/backend/engine/strategy_loader.py`
- Create: `apps/stock_backtest/templates/ma_crossover.py`
- Create: `apps/stock_backtest/templates/breakout.py`
- Create: `apps/stock_backtest/templates/mean_reversion.py`
- Create: `apps/stock_backtest/templates/momentum.py`
- Create: `apps/stock_backtest/templates/money_flow.py`
- Create: `apps/stock_backtest/tests/test_engine_components.py`

**Step 1: Write the failing test**
- Add tests for template discovery, strategy loading, data-feed registry shape, and core metrics computations.

**Step 2: Run test to verify it fails**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_engine_components.py -q`
- Expected: missing module/template failures.

**Step 3: Write minimal implementation**
- Implement template metadata loading, feed registry definitions, strategy import helpers, and deterministic metric calculations from daily equity data.

**Step 4: Run test to verify it passes**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_engine_components.py -q`
- Expected: PASS.

### Task 3: Domain Models, Repositories, And API Flows

**Files:**
- Create: `apps/stock_backtest/backend/models/db_models.py`
- Create: `apps/stock_backtest/backend/models/api_models.py`
- Create: `apps/stock_backtest/backend/modules/strategy/{repository.py,service.py,router.py}`
- Create: `apps/stock_backtest/backend/modules/backtest/{repository.py,service.py,router.py,websocket.py}`
- Create: `apps/stock_backtest/backend/modules/analysis/{repository.py,service.py,router.py}`
- Create: `apps/stock_backtest/backend/modules/notebook/{service.py,router.py}`
- Create: `apps/stock_backtest/backend/modules/data/router.py`
- Create: `apps/stock_backtest/tests/test_api_flows.py`

**Step 1: Write the failing test**
- Add API tests for template listing, strategy CRUD, backtest run submission/listing, analysis reads, feed listing, and notebook status using an in-memory DB.

**Step 2: Run test to verify it fails**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_api_flows.py -q`
- Expected: route/repository failures.

**Step 3: Write minimal implementation**
- Build SQLAlchemy models, repositories, service logic, and routers.
- Keep run execution asynchronous but start with a thread-safe in-process task runner interface so the API works before full executor sophistication.

**Step 4: Run test to verify it passes**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests/test_api_flows.py -q`
- Expected: PASS.

### Task 4: Frontend Shell, Stores, And Visual System

**Files:**
- Create: `apps/stock_backtest/frontend/package.json`
- Create: `apps/stock_backtest/frontend/tsconfig*.json`
- Create: `apps/stock_backtest/frontend/vite.config.ts`
- Create: `apps/stock_backtest/frontend/src/{main.tsx,App.tsx}`
- Create: `apps/stock_backtest/frontend/src/styles/app.css`
- Create: `apps/stock_backtest/frontend/src/components/*`
- Create: `apps/stock_backtest/frontend/src/pages/*`
- Create: `apps/stock_backtest/frontend/src/services/*`
- Create: `apps/stock_backtest/frontend/src/stores/*`
- Create: `apps/stock_backtest/frontend/src/test/*`

**Step 1: Write the failing test**
- Add frontend tests for navigation, backtest progress rendering, strategy editor interactions, and comparison table/chart content.

**Step 2: Run test to verify it fails**
- Run: `cd apps/stock_backtest/frontend && npm test -- --runInBand`
- Expected: missing file/import failures.

**Step 3: Write minimal implementation**
- Implement a distinctive trading dashboard aesthetic, seeded demo data, page navigation, stores, chart cards, and forms matching the design doc’s five modules.

**Step 4: Run test to verify it passes**
- Run: `cd apps/stock_backtest/frontend && npm test`
- Expected: PASS.

### Task 5: Integration, Launch Scripts, And Verification

**Files:**
- Create: `apps/stock_backtest/requirements.txt`
- Create: `apps/stock_backtest/run.sh`
- Modify: `pyproject.toml`
- Create: `apps/stock_backtest/README.md`

**Step 1: Write the failing test**
- Add any remaining smoke coverage for app factory wiring or script assumptions if needed.

**Step 2: Run test to verify it fails**
- Run focused backend/frontend verification commands as needed.

**Step 3: Write minimal implementation**
- Add install/runtime docs, script entrypoints, and include stock_backtest tests in the root pytest config.

**Step 4: Run test to verify it passes**
- Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest apps/stock_backtest/tests -q`
- Run: `cd apps/stock_backtest/frontend && npm test && npm run build`
- Expected: PASS.
