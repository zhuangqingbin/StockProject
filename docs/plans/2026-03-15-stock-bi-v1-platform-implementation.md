# Stock BI V1 Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the new Bloomberg-style stock data visualization platform in `apps/stock_bi_v1` with a FastAPI backend and a Next.js frontend, while leaving `apps/stock_bi` untouched.

**Architecture:** Reuse shared environment/database helpers from `shared/stock_core`, implement a modular FastAPI read API around the stock data warehouse tables plus lightweight precompute tables, and pair it with a Next.js App Router frontend that renders the dashboard, drill-down pages, and screener in a terminal-like high-density interface.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, cachetools, Pydantic v2, pytest, Next.js 14+, React 18, TypeScript, TailwindCSS, shadcn/ui, SWR, ECharts, Vitest, Testing Library

### Task 1: Backend foundation and red tests

**Files:**
- Create: `apps/stock_bi_v1/backend/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/settings.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/database.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/cache.py`
- Create: `apps/stock_bi_v1/backend/models/__init__.py`
- Create: `apps/stock_bi_v1/backend/models/api_models.py`
- Create: `apps/stock_bi_v1/backend/models/db_models.py`
- Create: `apps/stock_bi_v1/tests/__init__.py`
- Create: `apps/stock_bi_v1/tests/test_infrastructure.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing backend infrastructure tests**

```python
def test_cached_reuses_result_for_same_args():
    ...

def test_build_mysql_settings_contract():
    ...
```

**Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest apps/stock_bi_v1/tests/test_infrastructure.py -q`
Expected: FAIL because backend modules do not exist yet.

**Step 3: Write minimal infrastructure implementation**

Implement shared-config-backed settings, SQLAlchemy session helpers, cache decorators, baseline ORM/Pydantic models, and register the new test path.

**Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest apps/stock_bi_v1/tests/test_infrastructure.py -q`
Expected: PASS

### Task 2: Market, industry, stock, flow, toplist, and screener APIs

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/__init__.py`
- Create: `apps/stock_bi_v1/backend/modules/market/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/modules/industry/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/modules/stock/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/modules/flow/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/modules/toplist/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/modules/screener/{__init__.py,repository.py,service.py,router.py}`
- Create: `apps/stock_bi_v1/backend/precompute/{__init__.py,jobs.py}`
- Create: `apps/stock_bi_v1/backend/main.py`
- Create: `apps/stock_bi_v1/run.py`
- Create: `apps/stock_bi_v1/run.sh`
- Create: `apps/stock_bi_v1/requirements.txt`
- Create: `apps/stock_bi_v1/tests/test_market_api.py`
- Create: `apps/stock_bi_v1/tests/test_stock_api.py`
- Create: `apps/stock_bi_v1/tests/test_screener_api.py`

**Step 1: Write failing API tests**

```python
def test_market_overview_returns_dashboard_contract(client):
    ...

def test_stock_search_and_profile_routes(client):
    ...

def test_screener_supports_multi_condition_filters(client):
    ...
```

**Step 2: Run targeted API tests and verify RED**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest apps/stock_bi_v1/tests/test_market_api.py apps/stock_bi_v1/tests/test_stock_api.py apps/stock_bi_v1/tests/test_screener_api.py -q`
Expected: FAIL because routes and services are still missing.

**Step 3: Implement the minimal API surface**

Add routers, repositories, service-layer shaping, optional SQLite-friendly startup behavior, and the precompute trigger endpoint.

**Step 4: Run targeted API tests and keep them green**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest apps/stock_bi_v1/tests/test_market_api.py apps/stock_bi_v1/tests/test_stock_api.py apps/stock_bi_v1/tests/test_screener_api.py -q`
Expected: PASS

### Task 3: Frontend foundation and red tests

**Files:**
- Create: `apps/stock_bi_v1/frontend/package.json`
- Create: `apps/stock_bi_v1/frontend/next.config.js`
- Create: `apps/stock_bi_v1/frontend/tsconfig.json`
- Create: `apps/stock_bi_v1/frontend/postcss.config.js`
- Create: `apps/stock_bi_v1/frontend/tailwind.config.ts`
- Create: `apps/stock_bi_v1/frontend/vitest.config.ts`
- Create: `apps/stock_bi_v1/frontend/src/app/{layout.tsx,page.tsx,globals.css}`
- Create: `apps/stock_bi_v1/frontend/src/components/**/*`
- Create: `apps/stock_bi_v1/frontend/src/lib/{api.ts,format.ts}`
- Create: `apps/stock_bi_v1/frontend/src/test/setup.ts`
- Create: `apps/stock_bi_v1/frontend/src/test/dashboard.test.tsx`

**Step 1: Write the failing frontend shell tests**

```tsx
it('renders the terminal dashboard shell with major modules', () => {
  ...
})
```

**Step 2: Run test to verify RED**

Run: `cd apps/stock_bi_v1/frontend && npm test -- --runInBand`
Expected: FAIL because the Next.js frontend does not exist yet.

**Step 3: Write minimal frontend shell**

Create the Next.js app shell, terminal theme, shared API utilities, top bar, dashboard grid, and mock-friendly component boundaries.

**Step 4: Run test to verify GREEN**

Run: `cd apps/stock_bi_v1/frontend && npm test -- --runInBand`
Expected: PASS

### Task 4: Drill-down pages, charts, and screener UI

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/industry/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/app/stock/[code]/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/app/flow/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/app/toplist/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/app/limit/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/app/screener/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/charts/**/*`
- Create: `apps/stock_bi_v1/frontend/src/test/stock-detail.test.tsx`
- Create: `apps/stock_bi_v1/frontend/src/test/screener.test.tsx`

**Step 1: Add failing page tests**

```tsx
it('renders stock detail metrics, tabs, and kline controls', () => {
  ...
})

it('supports multi-condition screener workflows', async () => {
  ...
})
```

**Step 2: Run the new tests to verify RED**

Run: `cd apps/stock_bi_v1/frontend && npm test -- --runInBand`
Expected: FAIL because the page routes and interactions are not implemented yet.

**Step 3: Implement the minimal interactive pages**

Build the drill-down routes, reusable charts, sortable tables, breadcrumb flow, and screener interactions while preserving the Bloomberg-style visual direction.

**Step 4: Re-run frontend tests**

Run: `cd apps/stock_bi_v1/frontend && npm test -- --runInBand`
Expected: PASS

### Task 5: End-to-end verification

**Files:**
- Modify as needed: any files touched above

**Step 1: Run backend suite**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest apps/stock_bi_v1/tests -q`
Expected: PASS

**Step 2: Run frontend suite**

Run: `cd apps/stock_bi_v1/frontend && npm test -- --runInBand`
Expected: PASS

**Step 3: Run frontend production build**

Run: `cd apps/stock_bi_v1/frontend && npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git add apps/stock_bi_v1 pyproject.toml docs/plans/2026-03-15-stock-bi-v1-platform-implementation.md
git commit -m "feat: implement stock bi v1 platform"
```
