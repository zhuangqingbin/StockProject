# Stock Data Platform V1 Fetcher Self-Contained Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor `apps/stock_data_platform_v1` fetchers so each dataset is defined by one self-contained Python file whose filename matches the final MySQL `table_name`, while keeping only generic mechanics in `base.py`.

**Architecture:** Keep the existing category folders under `fetchers/tushare/`, but rename each dataset module to the target table name and move all dataset-specific fetch rules into that file. Remove shared `universe` and `report_period` helpers so special datasets own their own parameter derivation and stock-code fan-out logic.

**Tech Stack:** Python 3.11, pandas, pytest, YAML job definitions, local fetcher registry.

### Task 1: Lock the target structure with tests

**Files:**
- Modify: `apps/stock_data_platform_v1/tests/test_fetchers.py`
- Modify: `apps/stock_data_platform_v1/tests/test_common.py`

**Step 1: Write the failing test**

Add tests asserting:
- dataset modules are imported from table-name-aligned paths
- reference-data fan-out works without shared `stock_universe` helpers
- financial fetchers resolve report periods without shared `report_period.py`

**Step 2: Run test to verify it fails**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py apps/stock_data_platform_v1/tests/test_common.py`

**Step 3: Write minimal implementation**

Change imports and tests only until the failure is structural and expected.

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm the new structure tests are green.

### Task 2: Rename modules to table-name-aligned filenames

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/**/__init__.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/__init__.py`
- Modify: `apps/stock_data_platform_v1/fetchers/__init__.py`
- Rename: dataset fetcher modules whose filename does not match YAML `table_name`

**Step 1: Write the failing test**

Use the Task 1 path-based import assertions.

**Step 2: Run test to verify it fails**

Use the focused pytest command from Task 1.

**Step 3: Write minimal implementation**

Rename modules, update imports and package exports, and keep fetcher class names stable so YAML fetcher references remain valid.

**Step 4: Run test to verify it passes**

Run focused tests again.

### Task 3: Inline dataset-specific logic and delete shared helper modules

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/*.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/financial_data/*.py`
- Delete: `apps/stock_data_platform_v1/common/stock_universe.py`
- Delete: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_universe.py`
- Delete: `apps/stock_data_platform_v1/fetchers/tushare/financial_data/report_period.py`

**Step 1: Write the failing test**

Add assertions covering:
- explicit `ts_code` and `stock_codes` handling inside dataset fetchers
- fallback stock-code loading via `stock_basic`
- `as_of_date` to report-period conversion inside financial fetchers

**Step 2: Run test to verify it fails**

Run focused pytest.

**Step 3: Write minimal implementation**

Implement small file-local helpers inside each dataset module or use direct inline logic when short enough.

**Step 4: Run test to verify it passes**

Run focused pytest again.

### Task 4: Validate the full app test suite

**Files:**
- Modify only if regressions are found during validation

**Step 1: Run full test suite**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/tests`

**Step 2: Fix regressions minimally**

Address import-path or behavior regressions without reintroducing removed helper layers.

**Step 3: Re-run full suite**

Use the same command until green.
