# Tushare Runtime Module Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split `tushare_data_pipeline/registry.py` and `runtime.py` into smaller modules for job definitions, calendar/context logic, and persistence while preserving behavior and compatibility imports.

**Architecture:** Add a `jobs/` package for specs, profiles, and catalogs; add `calendar.py`, `context.py`, and `persistence.py` for runtime services; keep `registry.py` and `runtime.py` as thin compatibility re-export layers. Update `executor.py` and focused tests to consume the new modules internally.

**Tech Stack:** Python 3.11, pytest, pandas, SQLAlchemy

### Task 1: Lock the new module boundaries with tests

**Files:**
- Create: `apps/data_hub/tushare_data_pipeline/tests/test_module_boundaries.py`

**Step 1: Write the failing test**
- Import the planned `jobs.*`, `calendar`, `context`, and `persistence` modules.
- Assert `registry.py` and `runtime.py` re-export the same symbols.
- Assert `registry.py` and `runtime.py` source text no longer contains inline definitions.

**Step 2: Run test to verify it fails**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/tushare_data_pipeline/tests/test_module_boundaries.py`

Expected: fail because the split modules do not exist yet.

### Task 2: Extract job definitions into `jobs/`

**Files:**
- Create: `apps/data_hub/tushare_data_pipeline/jobs/__init__.py`
- Create: `apps/data_hub/tushare_data_pipeline/jobs/specs.py`
- Create: `apps/data_hub/tushare_data_pipeline/jobs/profiles.py`
- Create: `apps/data_hub/tushare_data_pipeline/jobs/catalog.py`
- Modify: `apps/data_hub/tushare_data_pipeline/registry.py`

**Step 1: Move `JobSpec`, `InfrastructureSpec`, and `JobRunResult` to `jobs/specs.py`.**

**Step 2: Move `ProfileId`, `ProfileSpec`, and profile constants to `jobs/profiles.py`.**

**Step 3: Move job and infrastructure catalogs to `jobs/catalog.py`.**

**Step 4: Convert `registry.py` into a compatibility export layer.**

### Task 3: Extract runtime services

**Files:**
- Create: `apps/data_hub/tushare_data_pipeline/calendar.py`
- Create: `apps/data_hub/tushare_data_pipeline/context.py`
- Create: `apps/data_hub/tushare_data_pipeline/persistence.py`
- Modify: `apps/data_hub/tushare_data_pipeline/runtime.py`

**Step 1: Move `get_trade_cal` into `calendar.py`.**

**Step 2: Move `ExecutionContext` and date helpers into `context.py`.**

**Step 3: Move `build_mysql_url`, `validate_frame_columns`, and `DatabaseWriter` into `persistence.py`.**

**Step 4: Convert `runtime.py` into a compatibility export layer.**

### Task 4: Repoint internal consumers

**Files:**
- Modify: `apps/data_hub/tushare_data_pipeline/executor.py`
- Modify: `apps/data_hub/tushare_data_pipeline/tests/test_context.py`
- Modify: `apps/data_hub/tushare_data_pipeline/tests/test_writer.py`
- Modify: `apps/data_hub/tushare_data_pipeline/tests/test_validator.py`
- Modify: `apps/data_hub/tushare_data_pipeline/tests/test_provider_client.py`
- Modify: `apps/data_hub/tushare_data_pipeline/tests/test_executor.py`

**Step 1: Update imports so internal code uses the new modules directly.**

**Step 2: Keep external compatibility through `registry.py` and `runtime.py`.**

### Task 5: Verify

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Step 1: Run the new boundary test.**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/tushare_data_pipeline/tests/test_module_boundaries.py`

**Step 2: Run the focused Tushare suite.**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/tushare_data_pipeline/tests`

**Step 3: Run the full `data_hub` Python suite.**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/tests apps/data_hub/pipeline_kernel/tests apps/data_hub/tushare_data_pipeline/tests apps/data_hub/akshare_data_pipeline/tests apps/data_hub/data_explorer/tests`
