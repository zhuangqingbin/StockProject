# Stock BI React Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the legacy imperative `stock_bi` static frontend with a React-based dashboard while preserving the existing FastAPI API, websocket update flow, and market-analysis feature set.

**Architecture:** Keep the current backend bounded contexts (`market_summary`, `ranking_kline`, `stock_detail`, `chat_query`, `realtime_updates`) as the application core. Replace only the presentation layer with a Vite + React + TypeScript SPA that consumes the existing `/api/market/*`, `/api/chat/*`, and `/ws/market` interfaces through typed clients and feature hooks.

**Tech Stack:** React, TypeScript, Vite, ECharts, Ant Design, TanStack Query, Zustand, Vitest, FastAPI static asset serving.

## Scope Assumptions

- Preserve the current FastAPI API contracts unless a small compatibility endpoint is clearly required.
- Preserve the current editorial visual direction, but re-express it with React components and a stronger component boundary.
- Migrate all current user-facing features:
  - market briefing shell
  - index pulse and summary cards
  - main chart stage with distribution / industry / ranking modes
  - north-money and amount trend charts
  - data consistency warning and update banner
  - websocket connection status
  - stock detail modal
  - industry detail modal with K-line and stocks list
  - analyst copilot / quick command panel
- Remove the legacy `frontend/app.js` imperative controller after feature parity is reached.

## Target Frontend Structure

- `apps/stock_bi/codex/frontend/package.json`
- `apps/stock_bi/codex/frontend/tsconfig.json`
- `apps/stock_bi/codex/frontend/tsconfig.node.json`
- `apps/stock_bi/codex/frontend/vite.config.ts`
- `apps/stock_bi/codex/frontend/index.html`
- `apps/stock_bi/codex/frontend/src/main.tsx`
- `apps/stock_bi/codex/frontend/src/App.tsx`
- `apps/stock_bi/codex/frontend/src/styles/`
- `apps/stock_bi/codex/frontend/src/lib/api/`
- `apps/stock_bi/codex/frontend/src/lib/ws/`
- `apps/stock_bi/codex/frontend/src/lib/state/`
- `apps/stock_bi/codex/frontend/src/features/market-overview/`
- `apps/stock_bi/codex/frontend/src/features/chart-stage/`
- `apps/stock_bi/codex/frontend/src/features/industry-detail/`
- `apps/stock_bi/codex/frontend/src/features/stock-detail/`
- `apps/stock_bi/codex/frontend/src/features/chat-console/`
- `apps/stock_bi/codex/frontend/src/test/`

## Task 1: Establish the New React Toolchain

**Files:**
- Create: `apps/stock_bi/codex/frontend/package.json`
- Create: `apps/stock_bi/codex/frontend/tsconfig.json`
- Create: `apps/stock_bi/codex/frontend/tsconfig.node.json`
- Create: `apps/stock_bi/codex/frontend/vite.config.ts`
- Create: `apps/stock_bi/codex/frontend/src/main.tsx`
- Create: `apps/stock_bi/codex/frontend/src/App.tsx`
- Create: `apps/stock_bi/codex/frontend/src/styles/app.css`
- Modify: `apps/stock_bi/codex/backend/main.py`
- Modify: `apps/stock_bi/README.md`
- Test: `apps/stock_bi/codex/tests/test_frontend_shell.py`

**Step 1: Write the failing test**

- Add assertions in `test_frontend_shell.py` that:
  - `frontend/package.json` exists
  - `frontend/src/main.tsx` exists
  - backend serves `frontend/dist/index.html` instead of raw legacy files

**Step 2: Run test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_shell.py -q
```

Expected: missing React frontend files or stale backend static path assertions.

**Step 3: Write minimal implementation**

- Add a Vite + React + TypeScript app shell.
- Set Vite build output to `frontend/dist`.
- Update `backend/main.py` to:
  - mount built assets from `frontend/dist/assets`
  - return `frontend/dist/index.html` at `/`
  - fall back cleanly when the build does not exist yet.

**Step 4: Run test to verify it passes**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_shell.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend apps/stock_bi/codex/backend/main.py apps/stock_bi/README.md apps/stock_bi/codex/tests/test_frontend_shell.py
git commit -m "feat: scaffold stock bi react frontend"
```

## Task 2: Add Typed API Clients and Shared Runtime State

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/lib/api/httpClient.ts`
- Create: `apps/stock_bi/codex/frontend/src/lib/api/marketApi.ts`
- Create: `apps/stock_bi/codex/frontend/src/lib/api/chatApi.ts`
- Create: `apps/stock_bi/codex/frontend/src/lib/api/types.ts`
- Create: `apps/stock_bi/codex/frontend/src/lib/state/dashboardStore.ts`
- Create: `apps/stock_bi/codex/frontend/src/lib/ws/useMarketSocket.ts`
- Test: `apps/stock_bi/codex/frontend/src/test/lib/api/marketApi.test.ts`
- Test: `apps/stock_bi/codex/tests/test_frontend_interactions.py`

**Step 1: Write the failing test**

- Add a frontend unit test covering market API response normalization.
- Extend `test_frontend_interactions.py` to assert the new store and websocket hook markers exist.

**Step 2: Run test to verify it fails**

Run:

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 3: Write minimal implementation**

- Add typed market/chat API helpers.
- Add Zustand store for UI mode, top-N, sort order, active modals, and banners.
- Add websocket hook handling:
  - connection status
  - reconnect timer
  - update banner trigger

**Step 4: Run tests to verify they pass**

Run:

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/src/lib apps/stock_bi/codex/frontend/src/test apps/stock_bi/codex/tests/test_frontend_interactions.py
git commit -m "feat: add stock bi frontend api and runtime state"
```

## Task 3: Rebuild the Dashboard Shell in React

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/MarketShell.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/MarketHeader.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/HeroBrief.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/OverviewCards.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/IndexPulse.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/ConsistencyBanner.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/App.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/styles/app.css`
- Test: `apps/stock_bi/codex/tests/test_frontend_shell.py`

**Step 1: Write the failing test**

- Update `test_frontend_shell.py` to assert the React entry references shell markers or component data-testid markers:
  - market pulse
  - signal strip
  - hero brief
  - assistant console

**Step 2: Run test to verify it fails**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_shell.py -q
```

**Step 3: Write minimal implementation**

- Move the shell layout into React components.
- Fetch `/api/market/summary`, `/api/market/north-money-trend`, `/api/market/amount-trend` with React Query.
- Preserve the current editorial layout and market tape information hierarchy.

**Step 4: Run test to verify it passes**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_shell.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/src/features/market-overview apps/stock_bi/codex/frontend/src/App.tsx apps/stock_bi/codex/frontend/src/styles/app.css apps/stock_bi/codex/tests/test_frontend_shell.py
git commit -m "feat: rebuild stock bi dashboard shell in react"
```

## Task 4: Rebuild the Main Chart Stage with ECharts Components

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/ChartStage.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/DistributionChart.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/IndustryTreemap.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/RankingTreemap.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/NorthTrendChart.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/AmountTrendChart.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chart-stage/chartOptions.ts`
- Test: `apps/stock_bi/codex/frontend/src/test/features/chart-stage/chartOptions.test.ts`
- Test: `apps/stock_bi/codex/tests/test_frontend_interactions.py`

**Step 1: Write the failing test**

- Add unit tests validating:
  - distribution option generation
  - industry treemap option generation
  - ranking treemap option generation
- Extend Python regression tests to assert the new feature component markers exist.

**Step 2: Run test to verify it fails**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 3: Write minimal implementation**

- Use `echarts-for-react` or a thin React wrapper around ECharts.
- Keep `topN`, `order`, and `view` in Zustand.
- Support click-through:
  - ranking treemap -> stock detail
  - industry treemap -> industry detail

**Step 4: Run tests to verify they pass**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/src/features/chart-stage apps/stock_bi/codex/frontend/src/test/features/chart-stage apps/stock_bi/codex/tests/test_frontend_interactions.py
git commit -m "feat: migrate stock bi chart stage to react echarts"
```

## Task 5: Rebuild Industry and Stock Detail Panels

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/features/industry-detail/IndustryDrawer.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/industry-detail/IndustryKlinePanel.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/industry-detail/IndustryStocksTable.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/stock-detail/StockDrawer.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/stock-detail/StockKlinePanel.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/stock-detail/StockMetricGrid.tsx`
- Test: `apps/stock_bi/codex/frontend/src/test/features/industry-detail/industryDrawer.test.tsx`
- Test: `apps/stock_bi/codex/frontend/src/test/features/stock-detail/stockDrawer.test.tsx`

**Step 1: Write the failing test**

- Add drawer rendering tests for:
  - industry detail view switch
  - stock detail metric rendering

**Step 2: Run test to verify it fails**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
```

**Step 3: Write minimal implementation**

- Use Ant Design `Drawer`, `Segmented`, `Table`, `Statistic`, `Skeleton`.
- Load:
  - `/api/market/industry-detail/{industry}`
  - `/api/market/industry-stocks/{industry}`
  - `/api/market/stock/{ts_code}`
- Keep event flow feature-local; only the selected entity IDs belong in the global store.

**Step 4: Run tests to verify they pass**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/src/features/industry-detail apps/stock_bi/codex/frontend/src/features/stock-detail apps/stock_bi/codex/frontend/src/test/features
git commit -m "feat: migrate stock bi detail drawers"
```

## Task 6: Rebuild the Analyst Copilot Panel

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/features/chat-console/ChatConsole.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chat-console/QuickCommands.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chat-console/ChatTimeline.tsx`
- Create: `apps/stock_bi/codex/frontend/src/features/chat-console/useChatConsole.ts`
- Test: `apps/stock_bi/codex/frontend/src/test/features/chat-console/useChatConsole.test.ts`
- Test: `apps/stock_bi/codex/tests/test_frontend_interactions.py`

**Step 1: Write the failing test**

- Add tests covering:
  - quick command dispatch
  - message append behavior
  - `/api/chat/query` response binding

**Step 2: Run test to verify it fails**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 3: Write minimal implementation**

- Use React state + Ant Design form controls for the console.
- Keep the current rule-based quick command behavior and preserve the current backend chat integration.
- If streaming migration is not stable in the same slice, ship `/query` first and add `/stream` behind a feature toggle.

**Step 4: Run tests to verify they pass**

```bash
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/src/features/chat-console apps/stock_bi/codex/frontend/src/test/features/chat-console apps/stock_bi/codex/tests/test_frontend_interactions.py
git commit -m "feat: migrate stock bi analyst console"
```

## Task 7: Remove Legacy Static Frontend Controller

**Files:**
- Delete: `apps/stock_bi/codex/frontend/app.js`
- Delete: `apps/stock_bi/codex/frontend/styles.css`
- Modify: `apps/stock_bi/codex/frontend/index.html`
- Modify: `apps/stock_bi/codex/tests/test_frontend_interactions.py`
- Modify: `apps/stock_bi/codex/tests/test_layout.py`
- Modify: `apps/stock_bi/README.md`

**Step 1: Write the failing test**

- Change the Python regression tests so they stop checking legacy function markers and instead check:
  - React entrypoint markers
  - build files and feature directories
  - absence of legacy controller files

**Step 2: Run test to verify it fails**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py apps/stock_bi/codex/tests/test_layout.py -q
```

**Step 3: Write minimal implementation**

- Remove the legacy imperative frontend files after the React feature set is live.
- Keep `index.html` as the Vite host document only.

**Step 4: Run test to verify it passes**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_frontend_interactions.py apps/stock_bi/codex/tests/test_layout.py -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/codex/frontend/index.html apps/stock_bi/codex/tests/test_frontend_interactions.py apps/stock_bi/codex/tests/test_layout.py apps/stock_bi/README.md
git rm apps/stock_bi/codex/frontend/app.js apps/stock_bi/codex/frontend/styles.css
git commit -m "refactor: remove legacy stock bi static frontend"
```

## Task 8: Full Verification and Runbook

**Files:**
- Modify: `apps/stock_bi/README.md`
- Modify: `apps/stock_bi/codex/run.sh`
- Modify: `apps/stock_bi/codex/tests/test_runtime_env.py`

**Step 1: Write the failing test**

- Add test expectations for the new frontend toolchain and production asset serving.

**Step 2: Run test to verify it fails**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests/test_runtime_env.py -q
```

**Step 3: Write minimal implementation**

- Document:
  - `npm install`
  - `npm run dev`
  - `npm run build`
  - backend launch with built assets
- Optionally add a convenience build step in `run.sh` only if it remains predictable and fast.

**Step 4: Run full verification**

```bash
npm --prefix apps/stock_bi/codex/frontend install
npm --prefix apps/stock_bi/codex/frontend run build
npm --prefix apps/stock_bi/codex/frontend test -- --runInBand
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest apps/stock_bi/codex/tests -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

**Step 5: Commit**

```bash
git add apps/stock_bi/README.md apps/stock_bi/codex/run.sh apps/stock_bi/codex/tests/test_runtime_env.py
git commit -m "docs: finalize stock bi react refactor runbook"
```

## Risk Controls

- Do not rewrite backend query logic in the same pass unless a frontend contract bug forces it.
- Keep websocket and data consistency behavior identical at first; optimize only after parity.
- Keep chart option builders pure and unit-tested.
- Keep drawers and chart-stage features isolated; do not reintroduce one giant controller.
- Avoid shipping a half-migrated shell that mixes React state and imperative DOM mutation.

## Recommended Execution Order

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7
8. Task 8
