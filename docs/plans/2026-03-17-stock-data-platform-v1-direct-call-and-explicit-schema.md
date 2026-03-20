# Stock Data Platform V1 Direct Call And Explicit Schema Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `source_endpoint` / `call_source` indirection from `apps/stock_data_platform_v1` and require each fetcher file to declare its own `table_schema`.

**Architecture:** Keep `base.py` as a thin runtime layer with shared schema dataclasses and helper builders only. Push endpoint names, field lists, and explicit schema declarations back into each dataset fetcher so one file owns one dataset definition.

**Tech Stack:** Python 3.11, pandas, pytest.

### Task 1: Lock the desired contract with tests

**Files:**
- Modify: `apps/stock_data_platform_v1/tests/test_fetchers.py`
- Modify: `apps/stock_data_platform_v1/tests/test_base.py`

**Step 1: Write the failing test**

Add tests asserting:
- `BaseFetcher` no longer exposes `call_source`
- Tushare fetchers do not declare `source_endpoint`
- Job and infrastructure fetchers explicitly define `table_schema` in their own class bodies

**Step 2: Run test to verify it fails**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/tests/test_base.py apps/stock_data_platform_v1/tests/test_fetchers.py`

**Step 3: Write minimal implementation**

Refactor only enough to satisfy the contract.

**Step 4: Run test to verify it passes**

Run the same pytest command again.

### Task 2: Simplify base.py

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/base.py`

**Step 1: Remove endpoint indirection**

Delete `source_endpoint` and `call_source`.

**Step 2: Remove auto-generated schema setup**

Delete `__init_subclass__` schema auto-registration so fetchers must provide `table_schema`.

**Step 3: Keep only generic helpers**

Retain `ColumnDef`, `TableSchema`, and shared schema-builder helpers.

### Task 3: Update all fetchers

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/**/*.py`
- Modify: `apps/stock_data_platform_v1/fetchers/akshare/calendar.py` only if needed for consistency

**Step 1: Replace `self.call_source(...)`**

Use direct `self.client.call("real_endpoint", ...)` in each file.

**Step 2: Add explicit `table_schema`**

Declare `table_schema = build_table_schema(...)` or a manual `TableSchema(...)` in every fetcher file.

**Step 3: Preserve behavior**

Do not change field order, endpoints, or fan-out behavior.

### Task 4: Verify the app

**Files:**
- Modify only if regressions are found

**Step 1: Run focused tests**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/tests/test_base.py apps/stock_data_platform_v1/tests/test_fetchers.py`

**Step 2: Run full suite**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/tests`

**Step 3: Fix regressions minimally**

Only patch failing paths introduced by this refactor.
