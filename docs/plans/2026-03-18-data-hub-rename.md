# Data Hub Rename Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the stock data app, explorer, and pipeline packages to the new canonical names selected by the user.

**Architecture:** Apply a behavior-preserving package rename. Lock the target import surface with a small regression test first, then rename directories and update imports, shell entrypoints, frontend/backend references, and active documentation in focused passes.

**Tech Stack:** Python 3.11, pytest, FastAPI, Vite/React, shell scripts

### Task 1: Lock the New Import Surface

**Files:**
- Create: `apps/data_hub/tests/test_package_renames.py`

**Step 1: Write the failing test**

Add a test that imports:
- `apps.data_hub`
- `apps.data_hub.data_explorer.backend.main`
- `apps.data_hub.tushare_data_pipeline`

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/data_hub/tests/test_package_renames.py`

Expected: FAIL because the renamed packages do not exist yet.

### Task 2: Rename the Package Directories

**Files:**
- Move: `apps/stock_data_platform_v1 -> apps/data_hub`
- Move: `apps/data_hub/BI -> apps/data_hub/data_explorer`
- Move: `apps/data_hub/orchestrator_v2 -> apps/data_hub/tushare_data_pipeline`

**Step 1: Rename directories**

Use filesystem moves only after the failing test is confirmed.

**Step 2: Update package markers if needed**

Ensure `__init__.py` files still expose the expected runtime entrypoints after the moves.

### Task 3: Update Code Imports and Runtime Paths

**Files:**
- Modify all Python modules, tests, and scripts under `apps/data_hub`
- Modify frontend/backend references under `apps/data_hub/data_explorer`

**Step 1: Replace import paths**

Update `apps.stock_data_platform_v1...` to `apps.data_hub...`.

**Step 2: Replace runtime package references**

Update `orchestrator_v2` to `tushare_data_pipeline` and `BI` to `data_explorer` in code and scripts.

**Step 3: Keep behavior unchanged**

Do not alter runtime semantics beyond the naming changes.

### Task 4: Update Active Documentation

**Files:**
- Modify active docs and READMEs under `apps/data_hub`
- Modify directly affected plan/docs references if they point users to old runtime paths

**Step 1: Rewrite current docs**

Update active app docs to the new names.

**Step 2: Leave archival docs alone unless they mislead current usage**

Only touch historical plans when they now block discoverability.

### Task 5: Verify the Rename

**Files:**
- Test: `apps/data_hub/tests/test_package_renames.py`
- Test: focused pytest suites under `apps/data_hub`

**Step 1: Re-run the rename regression test**

Run: `python -m pytest -q apps/data_hub/tests/test_package_renames.py`

Expected: PASS.

**Step 2: Run focused app tests**

Run:
- `python -m pytest -q apps/data_hub/tests apps/data_hub/tushare_data_pipeline/tests apps/data_hub/data_explorer/tests`

Expected: PASS or a narrow list of follow-up failures caused by residual rename references.
