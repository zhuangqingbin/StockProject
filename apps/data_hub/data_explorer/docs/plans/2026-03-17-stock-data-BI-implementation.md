# data_explorer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only database information platform under `apps/data_hub/data_explorer` for browsing `stock_database_v1` by TuShare business categories, inspecting table structure and DDL, previewing data, and monitoring freshness and job status.

**Architecture:** A FastAPI backend provides category, table detail, preview, monitor, and database metadata APIs. A React + Vite frontend renders a category-first workspace with separate pages for directory, monitor, and database metadata. Table descriptions and business labels come from a local config file, while structure and statistics are queried from MySQL at runtime with read-only access.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, PyMySQL, PyYAML, React 18, Vite, TypeScript, Ant Design, TanStack Query, Zustand, pytest

**Spec:** `apps/data_hub/data_explorer/docs/prd.md`, `apps/data_hub/data_explorer/docs/page_spec.md`, `apps/data_hub/data_explorer/docs/table_inventory.md`

---

## Proposed File Structure

### Backend

| File | Responsibility |
|---|---|
| `apps/data_hub/data_explorer/backend/__init__.py` | Package marker |
| `apps/data_hub/data_explorer/backend/main.py` | FastAPI app factory, router registration, static serving |
| `apps/data_hub/data_explorer/backend/api/__init__.py` | Package marker |
| `apps/data_hub/data_explorer/backend/api/catalog.py` | Directory and table detail endpoints |
| `apps/data_hub/data_explorer/backend/api/preview.py` | Data preview endpoints |
| `apps/data_hub/data_explorer/backend/api/monitor.py` | Monitor endpoints |
| `apps/data_hub/data_explorer/backend/api/database_metadata.py` | Schema overview, DDL, index, constraint endpoints |
| `apps/data_hub/data_explorer/backend/infrastructure/__init__.py` | Package marker |
| `apps/data_hub/data_explorer/backend/infrastructure/db.py` | Read-only engine creation using existing env helpers |
| `apps/data_hub/data_explorer/backend/infrastructure/catalog_loader.py` | Load table labels and descriptions from YAML config |
| `apps/data_hub/data_explorer/backend/infrastructure/mysql_introspection.py` | SQLAlchemy inspect + MySQL metadata helpers |
| `apps/data_hub/data_explorer/backend/services/catalog_service.py` | Category list, category table list, summary fields |
| `apps/data_hub/data_explorer/backend/services/table_detail_service.py` | Single-table structure, DDL, summary aggregation |
| `apps/data_hub/data_explorer/backend/services/preview_service.py` | Read-only paginated preview queries |
| `apps/data_hub/data_explorer/backend/services/monitor_service.py` | Table freshness + job status aggregation |
| `apps/data_hub/data_explorer/backend/services/database_metadata_service.py` | Schema overview, global metadata views |

### Frontend

| File | Responsibility |
|---|---|
| `apps/data_hub/data_explorer/frontend/package.json` | Frontend dependencies and scripts |
| `apps/data_hub/data_explorer/frontend/vite.config.ts` | Dev server and build config |
| `apps/data_hub/data_explorer/frontend/tsconfig.json` | TypeScript config |
| `apps/data_hub/data_explorer/frontend/index.html` | Frontend entry |
| `apps/data_hub/data_explorer/frontend/src/main.tsx` | React root |
| `apps/data_hub/data_explorer/frontend/src/App.tsx` | Top-level layout and routing |
| `apps/data_hub/data_explorer/frontend/src/api.ts` | HTTP client and API functions |
| `apps/data_hub/data_explorer/frontend/src/types.ts` | Shared frontend types |
| `apps/data_hub/data_explorer/frontend/src/stores/navigationStore.ts` | Selected category, selected table, current page |
| `apps/data_hub/data_explorer/frontend/src/hooks/useCatalog.ts` | Directory data hooks |
| `apps/data_hub/data_explorer/frontend/src/hooks/usePreview.ts` | Preview data hooks |
| `apps/data_hub/data_explorer/frontend/src/hooks/useMonitor.ts` | Monitor data hooks |
| `apps/data_hub/data_explorer/frontend/src/hooks/useDatabaseMetadata.ts` | Database metadata hooks |
| `apps/data_hub/data_explorer/frontend/src/pages/DirectoryPage.tsx` | Directory page |
| `apps/data_hub/data_explorer/frontend/src/pages/TableDetailPage.tsx` | Table detail page |
| `apps/data_hub/data_explorer/frontend/src/pages/MonitorPage.tsx` | Monitor page |
| `apps/data_hub/data_explorer/frontend/src/pages/DatabaseMetadataPage.tsx` | Database metadata page |
| `apps/data_hub/data_explorer/frontend/src/components/CategoryTree.tsx` | Left category tree with counts |
| `apps/data_hub/data_explorer/frontend/src/components/TableList.tsx` | Current-category table list |
| `apps/data_hub/data_explorer/frontend/src/components/TableSummary.tsx` | Table summary cards |
| `apps/data_hub/data_explorer/frontend/src/components/TableStructure.tsx` | Fields, indexes, constraints, DDL |
| `apps/data_hub/data_explorer/frontend/src/components/TablePreview.tsx` | Data preview |
| `apps/data_hub/data_explorer/frontend/src/components/MonitorTabs.tsx` | Table/task monitor tabs |
| `apps/data_hub/data_explorer/frontend/src/components/SchemaOverview.tsx` | Database metadata overview |

### Config, Scripts, Tests

| File | Responsibility |
|---|---|
| `apps/data_hub/data_explorer/config/table_catalog.yaml` | Chinese labels, descriptions, category overrides, runtime entries |
| `apps/data_hub/data_explorer/requirements.txt` | Backend dependencies |
| `apps/data_hub/data_explorer/scripts/run.sh` | Local startup for backend and frontend |
| `apps/data_hub/data_explorer/tests/test_catalog_loader.py` | Config loader tests |
| `apps/data_hub/data_explorer/tests/test_catalog_service.py` | Directory and detail service tests |
| `apps/data_hub/data_explorer/tests/test_preview_service.py` | Preview rules and pagination tests |
| `apps/data_hub/data_explorer/tests/test_monitor_service.py` | Freshness and job status tests |
| `apps/data_hub/data_explorer/tests/test_database_metadata_service.py` | Schema overview and DDL tests |
| `apps/data_hub/data_explorer/tests/test_api_smoke.py` | API integration smoke tests |

---

## Task 1: Scaffold `data_explorer`

**Files:**
- Create: `apps/data_hub/data_explorer/backend/__init__.py`
- Create: `apps/data_hub/data_explorer/backend/api/__init__.py`
- Create: `apps/data_hub/data_explorer/backend/infrastructure/__init__.py`
- Create: `apps/data_hub/data_explorer/backend/services/__init__.py`
- Create: `apps/data_hub/data_explorer/tests/__init__.py`
- Create: `apps/data_hub/data_explorer/backend/main.py`
- Create: `apps/data_hub/data_explorer/requirements.txt`
- Create: `apps/data_hub/data_explorer/scripts/run.sh`
- Test: `apps/data_hub/data_explorer/tests/test_api_smoke.py`

- [ ] **Step 1: Write the failing smoke test**
  Add a test that imports `create_app()` and asserts `GET /health` returns `200`.

- [ ] **Step 2: Run the smoke test**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_api_smoke.py -q`
  Expected: fail because `create_app()` and routes do not exist yet.

- [ ] **Step 3: Create the minimal backend shell**
  Add `create_app()` in `backend/main.py`, mount a `/health` route, and add package markers.

- [ ] **Step 4: Add backend dependencies and startup script**
  Include FastAPI, SQLAlchemy, PyMySQL, and PyYAML in `requirements.txt`. Create `scripts/run.sh` that can start backend first and later integrate frontend startup.

- [ ] **Step 5: Re-run the smoke test**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_api_smoke.py -q`
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): scaffold backend app shell"`

## Task 2: Add table catalog config

**Files:**
- Create: `apps/data_hub/data_explorer/config/table_catalog.yaml`
- Create: `apps/data_hub/data_explorer/backend/infrastructure/catalog_loader.py`
- Test: `apps/data_hub/data_explorer/tests/test_catalog_loader.py`

- [ ] **Step 1: Write the failing loader test**
  Test that the loader returns Chinese labels and descriptions for at least `stock_daily`, `stock_basic`, and `job_run_log`.

- [ ] **Step 2: Run the loader test**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_catalog_loader.py -q`
  Expected: fail because config and loader are missing.

- [ ] **Step 3: Create `table_catalog.yaml`**
  Populate it from `docs/table_inventory.md`. Include:
  - category labels
  - table descriptions
  - runtime entries such as `job_run_log`
  - exclusion list for `precomputed_*`

- [ ] **Step 4: Implement the loader**
  Create a small loader that reads YAML once and returns a normalized mapping keyed by table name and category key.

- [ ] **Step 5: Re-run the loader test**
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add table catalog configuration"`

## Task 3: Build read-only database infrastructure

**Files:**
- Create: `apps/data_hub/data_explorer/backend/infrastructure/db.py`
- Create: `apps/data_hub/data_explorer/backend/infrastructure/mysql_introspection.py`
- Test: `apps/data_hub/data_explorer/tests/test_database_metadata_service.py`

- [ ] **Step 1: Write failing infrastructure tests**
  Cover:
  - engine creation uses `MYSQL_DATABASE`
  - inspector helpers normalize columns, indexes, constraints
  - DDL query helper returns one string per table

- [ ] **Step 2: Run the tests**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_database_metadata_service.py -q`
  Expected: fail.

- [ ] **Step 3: Implement read-only engine creation**
  Reuse env conventions from `apps/data_hub/common/database.py`. Keep one engine singleton for the backend.

- [ ] **Step 4: Implement introspection helpers**
  Use SQLAlchemy inspect plus MySQL-specific SQL for:
  - `SHOW CREATE TABLE`
  - index listing
  - primary key detection
  - constraint listing
  - exact row count query
  - latest business date query

- [ ] **Step 5: Re-run tests**
  Expected: pass for mocked/isolated helpers.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add read-only db introspection layer"`

## Task 4: Implement catalog and table detail services

**Files:**
- Create: `apps/data_hub/data_explorer/backend/services/catalog_service.py`
- Create: `apps/data_hub/data_explorer/backend/services/table_detail_service.py`
- Test: `apps/data_hub/data_explorer/tests/test_catalog_service.py`

- [ ] **Step 1: Write failing service tests**
  Cover:
  - category list includes counts
  - category table list only returns current-category tables
  - table detail includes structure, exact row count, latest date, and status

- [ ] **Step 2: Run the tests**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_catalog_service.py -q`
  Expected: fail.

- [ ] **Step 3: Implement category aggregation**
  Merge:
  - `fetchers/tushare` directory structure
  - `data_pipeline_ts/registry.py`
  - `config/table_catalog.yaml`
  - runtime entries

- [ ] **Step 4: Implement table detail aggregation**
  Provide one object that combines:
  - summary cards
  - columns
  - indexes
  - constraints
  - collapsed DDL payload

- [ ] **Step 5: Re-run tests**
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add catalog and table detail services"`

## Task 5: Implement preview service

**Files:**
- Create: `apps/data_hub/data_explorer/backend/services/preview_service.py`
- Test: `apps/data_hub/data_explorer/tests/test_preview_service.py`

- [ ] **Step 1: Write failing preview tests**
  Cover:
  - every table can request preview
  - page size defaults to 50
  - ordering uses main date column descending when available
  - fallback ordering uses primary key or first index
  - filters only allow supported columns

- [ ] **Step 2: Run the tests**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_preview_service.py -q`
  Expected: fail.

- [ ] **Step 3: Implement preview query builder**
  Build parameterized SQL for:
  - page
  - page size
  - main date filter
  - `ts_code` filter
  - exact total row count

- [ ] **Step 4: Add error handling**
  Reject unsafe identifiers and unsupported filters with explicit backend errors.

- [ ] **Step 5: Re-run tests**
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add preview service"`

## Task 6: Implement monitor and database metadata services

**Files:**
- Create: `apps/data_hub/data_explorer/backend/services/monitor_service.py`
- Create: `apps/data_hub/data_explorer/backend/services/database_metadata_service.py`
- Test: `apps/data_hub/data_explorer/tests/test_monitor_service.py`
- Test: `apps/data_hub/data_explorer/tests/test_database_metadata_service.py`

- [ ] **Step 1: Write failing tests**
  Cover:
  - table monitor rows show latest data date, latest update, status
  - job monitor rows show latest execution and error
  - schema overview returns table totals and category totals
  - DDL/index/constraint drill-down returns structured payloads

- [ ] **Step 2: Run the tests**
  Run:
  - `python -m pytest apps/data_hub/data_explorer/tests/test_monitor_service.py -q`
  - `python -m pytest apps/data_hub/data_explorer/tests/test_database_metadata_service.py -q`
  Expected: fail.

- [ ] **Step 3: Implement monitor service**
  Read from `job_run_log` and table detail helpers to compute:
  - table perspective rows
  - task perspective rows
  - default status ordering

- [ ] **Step 4: Implement database metadata service**
  Return:
  - schema overview
  - DDL list
  - index list
  - constraint list
  - column metadata list

- [ ] **Step 5: Re-run tests**
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add monitor and metadata services"`

## Task 7: Expose backend APIs

**Files:**
- Create: `apps/data_hub/data_explorer/backend/api/catalog.py`
- Create: `apps/data_hub/data_explorer/backend/api/preview.py`
- Create: `apps/data_hub/data_explorer/backend/api/monitor.py`
- Create: `apps/data_hub/data_explorer/backend/api/database_metadata.py`
- Modify: `apps/data_hub/data_explorer/backend/main.py`
- Test: `apps/data_hub/data_explorer/tests/test_api_smoke.py`

- [ ] **Step 1: Write failing API tests**
  Cover:
  - categories endpoint
  - category table list endpoint
  - table detail endpoint
  - preview endpoint
  - monitor endpoints
  - schema overview endpoint

- [ ] **Step 2: Run the tests**
  Run: `python -m pytest apps/data_hub/data_explorer/tests/test_api_smoke.py -q`
  Expected: fail.

- [ ] **Step 3: Implement routers**
  Suggested endpoint surface:
  - `GET /api/catalog/categories`
  - `GET /api/catalog/categories/{category_key}/tables`
  - `GET /api/catalog/tables/{table_name}`
  - `GET /api/preview/{table_name}`
  - `GET /api/monitor/tables`
  - `GET /api/monitor/jobs`
  - `GET /api/database/overview`
  - `GET /api/database/tables/{table_name}/ddl`
  - `GET /api/database/tables/{table_name}/indexes`
  - `GET /api/database/tables/{table_name}/constraints`

- [ ] **Step 4: Re-run API tests**
  Expected: pass.

- [ ] **Step 5: Commit**
  `git commit -m "feat(BI): expose backend apis"`

## Task 8: Scaffold frontend shell

**Files:**
- Create: `apps/data_hub/data_explorer/frontend/package.json`
- Create: `apps/data_hub/data_explorer/frontend/vite.config.ts`
- Create: `apps/data_hub/data_explorer/frontend/tsconfig.json`
- Create: `apps/data_hub/data_explorer/frontend/index.html`
- Create: `apps/data_hub/data_explorer/frontend/src/main.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/App.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/api.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/types.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/stores/navigationStore.ts`

- [ ] **Step 1: Initialize frontend project files**
  Add React, Vite, TypeScript, Ant Design, Zustand, TanStack Query dependencies.

- [ ] **Step 2: Create the app shell**
  Implement:
  - top navigation
  - left navigation region
  - right content region

- [ ] **Step 3: Wire API client and store**
  Add base API functions and a simple store for current page, category, and selected table.

- [ ] **Step 4: Verify frontend builds**
  Run: `npm --prefix apps/data_hub/data_explorer/frontend run build`
  Expected: successful production build.

- [ ] **Step 5: Commit**
  `git commit -m "feat(BI): scaffold frontend shell"`

## Task 9: Build directory page and table detail page

**Files:**
- Create: `apps/data_hub/data_explorer/frontend/src/hooks/useCatalog.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/hooks/usePreview.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/pages/DirectoryPage.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/pages/TableDetailPage.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/CategoryTree.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/TableList.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/TableSummary.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/TableStructure.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/TablePreview.tsx`

- [ ] **Step 1: Implement category tree**
  Show category counts, selection state, and current-category search behavior.

- [ ] **Step 2: Implement current-category table list**
  Show the agreed summary columns and default sorting.

- [ ] **Step 3: Implement table detail layout**
  Show summary cards and structure-first detail layout.

- [ ] **Step 4: Implement data preview**
  Use default page size 50 and agreed fallback sort behavior.

- [ ] **Step 5: Run frontend build**
  Run: `npm --prefix apps/data_hub/data_explorer/frontend run build`
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add directory and table detail pages"`

## Task 10: Build monitor and database metadata pages

**Files:**
- Create: `apps/data_hub/data_explorer/frontend/src/hooks/useMonitor.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/hooks/useDatabaseMetadata.ts`
- Create: `apps/data_hub/data_explorer/frontend/src/pages/MonitorPage.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/pages/DatabaseMetadataPage.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/MonitorTabs.tsx`
- Create: `apps/data_hub/data_explorer/frontend/src/components/SchemaOverview.tsx`

- [ ] **Step 1: Implement monitor tabs**
  Default to table perspective and expose task perspective as peer tab.

- [ ] **Step 2: Implement table/task monitor tables**
  Add status filters and row click-through to table detail.

- [ ] **Step 3: Implement database metadata overview**
  Show schema summary cards and entry cards for DDL, indexes, and constraints.

- [ ] **Step 4: Implement metadata drill-down**
  Allow user to move from overview to per-table metadata detail and back to table detail.

- [ ] **Step 5: Run frontend build**
  Run: `npm --prefix apps/data_hub/data_explorer/frontend run build`
  Expected: pass.

- [ ] **Step 6: Commit**
  `git commit -m "feat(BI): add monitor and database metadata pages"`

## Task 11: Add test coverage and startup workflow

**Files:**
- Modify: `apps/data_hub/data_explorer/scripts/run.sh`
- Modify: `apps/data_hub/data_explorer/README.md` if created later
- Test: `apps/data_hub/data_explorer/tests/test_api_smoke.py`

- [ ] **Step 1: Add backend test command coverage**
  Run:
  - `python -m pytest apps/data_hub/data_explorer/tests -q`

- [ ] **Step 2: Add frontend build verification**
  Run:
  - `npm --prefix apps/data_hub/data_explorer/frontend run build`

- [ ] **Step 3: Finalize `scripts/run.sh`**
  Support:
  - backend only
  - frontend dev mode
  - combined local start

- [ ] **Step 4: Record startup notes**
  Add or update a small `README.md` later if needed, but do not expand scope beyond startup and verification.

- [ ] **Step 5: Commit**
  `git commit -m "chore(BI): finalize startup workflow and verification"`

## Task 12: Final verification

**Files:**
- No new files

- [ ] **Step 1: Run backend tests**
  `python -m pytest apps/data_hub/data_explorer/tests -q`

- [ ] **Step 2: Run frontend build**
  `npm --prefix apps/data_hub/data_explorer/frontend run build`

- [ ] **Step 3: Run manual smoke**
  Start the app and verify:
  - directory page loads
  - category tree shows counts
  - table detail opens with structure first
  - preview loads with 50-row pagination
  - monitor defaults to table tab
  - database metadata shows schema overview first

- [ ] **Step 4: Commit**
  `git commit -m "feat(BI): ship stock data bi v1"`
