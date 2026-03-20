# Stock Data Platform Special Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first available `1.7 特色数据` TuShare datasets with a split between lightweight daily jobs and heavier special jobs.

**Architecture:** Create a new `DataFetch/SpecialData/` package with one fetcher per endpoint. Add direct `trade_date`-driven jobs for `hk_hold`, `stk_factor_pro`, `stk_ah_comparison`, `stk_surv`, and `ccass_hold` to `daily_jobs.yaml`. Add a separate `special_jobs.yaml` plus `run_stock_data_special.sh` for the stock-loop datasets `cyq_perf`, `cyq_chips`, and the non-date dataset `hm_list`.

**Tech Stack:** Python 3.11, pandas, pytest, existing `daily_runner`, existing `ReferenceData/stock_universe.py` helper pattern.

### Task 1: Write failing tests for the new package and job split

**Files:**
- Modify: `apps/stock_data_platform/tests/test_smoke.py`
- Modify: `apps/stock_data_platform/tests/test_daily_jobs.py`

**Step 1: Write the failing test**

- Add `SpecialData/` package structure assertions.
- Add Chinese field-comment assertions for the new modules.
- Add runtime export assertions for all new fetchers.
- Add `special_jobs.yaml` and `run_stock_data_special.sh` existence assertions.
- Add job-definition tests for:
  - daily lane: `hk_hold`, `stk_factor_pro`, `stk_ah_comparison`, `stk_surv`, `ccass_hold`
  - special lane: `cyq_perf`, `cyq_chips`, `hm_list`
- Add representative fetcher behavior tests, including stock-universe looping for `cyq_perf` and `cyq_chips`.

**Step 2: Run test to verify it fails**

Run the focused smoke and daily-job subsets and confirm the failures are due to missing package/config/exports.

### Task 2: Implement the `SpecialData/` package

**Files:**
- Create: `apps/stock_data_platform/DataFetch/SpecialData/__init__.py`
- Create: `apps/stock_data_platform/DataFetch/SpecialData/*.py` for each endpoint
- Modify: `apps/stock_data_platform/DataFetch/__init__.py`

**Step 1: Write minimal implementation**

- Add one class per endpoint:
  - `HKHoldFetch`
  - `StkFactorProFetch`
  - `StkAHComparisonFetch`
  - `StkSurvFetch`
  - `CCASSHoldFetch`
  - `CyqPerfFetch`
  - `CyqChipsFetch`
  - `HMListFetch`
- Keep fields in the documented order with Chinese inline comments.
- Use the stock-universe helper for `cyq_perf` and `cyq_chips`.
- Return empty `DataFrame`s with expected columns when upstream returns no rows.

### Task 3: Add the daily/special job split and runner

**Files:**
- Modify: `apps/stock_data_platform/jobs/daily_jobs.yaml`
- Create: `apps/stock_data_platform/jobs/special_jobs.yaml`
- Create: `apps/stock_data_platform/scripts/run_stock_data_special.sh`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Write minimal implementation**

- Add the five lightweight daily datasets to `daily_jobs.yaml`, all using `trade_date`.
- Add `cyq_perf`, `cyq_chips`, and `hm_list` to `special_jobs.yaml`.
- Keep `cyq_perf` and `cyq_chips` `trade_date`-driven but isolated in the special lane because they loop all stocks.
- Keep `hm_list` as a no-date refresh job in the special lane.
- Document the lane split in `README.md`.

### Task 4: Verify the integration

**Step 1: Run the broader verification**

Run:
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py`
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'not root_compatibility_layer_has_been_removed'`
- `bash apps/stock_data_platform/scripts/run_stock_data_special.sh --help`

Expected: all targeted suites pass and the special runner help prints successfully.
