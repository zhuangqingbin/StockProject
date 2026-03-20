# Data Hub Bounded-Context Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor `apps/data_hub` so `tushare_data_pipeline` and `akshare_data_pipeline` own their provider-specific code, notebooks, and most tests, while the root app becomes a thin composition layer.

**Architecture:** Apply a behavior-preserving bounded-context extraction. Lock the target package layout with import tests first, then move Tushare code, create the AkShare context, and finally delete the obsolete `common/` wrappers and shrink root tests to app-level contracts.

**Tech Stack:** Python 3.11, pytest, FastAPI, Vite/React, shell scripts

### Task 1: Lock the New Pipeline Package Layout

**Files:**
- Create: `apps/data_hub/tests/test_pipeline_boundaries.py`

**Step 1: Write the failing test**

Add tests that import:
- `apps.data_hub.tushare_data_pipeline.fetchers.base`
- `apps.data_hub.tushare_data_pipeline.notebooks.data_notebook_support`
- `apps.data_hub.tushare_data_pipeline.provider.client`
- `apps.data_hub.akshare_data_pipeline.fetchers.calendar`
- `apps.data_hub.akshare_data_pipeline.provider.client`

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/data_hub/tests/test_pipeline_boundaries.py`

Expected: FAIL because the target package layout does not exist yet.

### Task 2: Consolidate Tushare Into Its Pipeline

**Files:**
- Move: `apps/data_hub/fetchers/tushare/** -> apps/data_hub/tushare_data_pipeline/fetchers/**`
- Move: `apps/data_hub/fetchers/base.py -> apps/data_hub/tushare_data_pipeline/fetchers/base.py`
- Move: `apps/data_hub/notebooks/** -> apps/data_hub/tushare_data_pipeline/notebooks/**`
- Create: `apps/data_hub/tushare_data_pipeline/provider/client.py`
- Modify: Tushare imports under `apps/data_hub/tushare_data_pipeline/**`

**Step 1: Move files**

Move Tushare-owned fetchers and notebook files into the Tushare context.

**Step 2: Update imports**

Switch all Tushare-internal imports to the new bounded-context paths.

**Step 3: Rehome tests**

Move Tushare-internal tests from `apps/data_hub/tests` into `apps/data_hub/tushare_data_pipeline/tests`.

### Task 3: Extract AkShare Context

**Files:**
- Create: `apps/data_hub/akshare_data_pipeline/__init__.py`
- Create: `apps/data_hub/akshare_data_pipeline/provider/__init__.py`
- Create: `apps/data_hub/akshare_data_pipeline/provider/client.py`
- Create: `apps/data_hub/akshare_data_pipeline/fetchers/__init__.py`
- Move: `apps/data_hub/fetchers/akshare/calendar.py -> apps/data_hub/akshare_data_pipeline/fetchers/calendar.py`
- Create/Move: AkShare-specific tests into `apps/data_hub/akshare_data_pipeline/tests`

**Step 1: Create the context shell**

Add the new package and provider/fetcher/test directories.

**Step 2: Move AkShare code**

Move `AkShareClient` and the calendar fetcher into that context.

**Step 3: Rehome tests**

Move AkShare-focused tests out of root.

### Task 4: Remove `common/` and Shrink Root Tests

**Files:**
- Delete: `apps/data_hub/common/clients.py`
- Delete: `apps/data_hub/common/market_calendar.py`
- Delete: `apps/data_hub/common/database.py`
- Modify: root import and test references

**Step 1: Replace wrappers**

Use `shared.stock_core.db` directly where the app truly needs shared MySQL URL construction.

**Step 2: Collapse root tests**

Keep only import/bootstrap/app-composition tests at `apps/data_hub/tests`.

### Task 5: Verify the Refactor

**Files:**
- Test: `apps/data_hub/tests/test_pipeline_boundaries.py`
- Test: `apps/data_hub/tushare_data_pipeline/tests`
- Test: `apps/data_hub/akshare_data_pipeline/tests`
- Test: `apps/data_hub/data_explorer/tests`

**Step 1: Re-run the new boundary test**

Run: `python -m pytest -q apps/data_hub/tests/test_pipeline_boundaries.py`

Expected: PASS.

**Step 2: Run focused Python tests**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/tests apps/data_hub/tushare_data_pipeline/tests apps/data_hub/akshare_data_pipeline/tests apps/data_hub/data_explorer/tests`

Expected: PASS or a small, explainable list of follow-up failures caused by incomplete boundary cleanup.
