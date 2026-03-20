# Stock Data Platform Reference Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dedicated reference-data ingestion lane for the `1.4 参考数据` TuShare APIs, with clear trigger semantics, runtime exports, documentation, and regression tests.

**Architecture:** Create a new `DataFetch/ReferenceData/` package with one fetcher per endpoint and a small shared helper for stock-universe iteration. Add a separate `reference_jobs.yaml` plus `run_stock_data_reference.sh` so these jobs stay isolated from `daily_jobs.yaml` and `financial_jobs.yaml`. Date-driven jobs pass `trade_date`, `ann_date`, or `as_of_date`; `ts_code`-required endpoints use `as_of_date` and perform the stock loop inside the fetcher.

**Tech Stack:** Python 3.11, pandas, pytest, existing `apps.stock_data_platform.jobs.runtime`, existing `TuShareClient`.

### Task 1: Write failing package and runner tests

**Files:**
- Modify: `apps/stock_data_platform/tests/test_smoke.py`
- Modify: `apps/stock_data_platform/tests/test_daily_jobs.py`

**Step 1: Write the failing test**

- Add `ReferenceData/` package structure assertions.
- Add runtime export assertions for the new fetchers.
- Add config/script existence assertions for `reference_jobs.yaml` and `run_stock_data_reference.sh`.
- Add representative job-definition tests for each trigger class:
  - `block_trade` with `trade_date`
  - `repurchase`, `share_float`, `stk_holdertrade`, `stk_holdernumber` with `ann_date`
  - `top10_holders`, `top10_floatholders`, `pledge_stat`, `pledge_detail` with `as_of_date`

**Step 2: Run test to verify it fails**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'reference'`

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py -k 'reference or holders or pledge or repurchase or share_float or block_trade'`

Expected: failures because `ReferenceData`, exports, config, and runner do not exist yet.

### Task 2: Implement the shared reference-data package

**Files:**
- Create: `apps/stock_data_platform/DataFetch/ReferenceData/__init__.py`
- Create: `apps/stock_data_platform/DataFetch/ReferenceData/stock_universe.py`
- Create: one fetcher file per `1.4` endpoint
- Modify: `apps/stock_data_platform/DataFetch/__init__.py`

**Step 1: Write minimal implementation**

- Add one class per endpoint:
  - `Top10HoldersFetch`
  - `Top10FloatHoldersFetch`
  - `StkHolderNumberFetch`
  - `StkHolderTradeFetch`
  - `PledgeStatFetch`
  - `PledgeDetailFetch`
  - `RepurchaseFetch`
  - `ShareFloatFetch`
  - `BlockTradeFetch`
- Keep output fields in the documented order with Chinese inline comments.
- Use a shared helper to obtain stock codes from `stock_basic`.
- For `ts_code`-required endpoints, loop codes inside the fetcher and concatenate results.
- Return an empty `DataFrame` with expected columns when upstream returns no rows.

**Step 2: Run focused tests**

Run the specific fetcher behavior tests added in Task 1 until they pass.

### Task 3: Add the reference-data job lane

**Files:**
- Create: `apps/stock_data_platform/jobs/reference_jobs.yaml`
- Create: `apps/stock_data_platform/scripts/run_stock_data_reference.sh`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Write minimal implementation**

- Add a dedicated runner script that reuses `apps.stock_data_platform.jobs.daily_runner` with `--config reference_jobs.yaml`.
- Add jobs with trigger semantics:
  - `trade_date`: `block_trade`
  - `ann_date`: `repurchase`, `share_float`, `stk_holdertrade`, `stk_holdernumber`
  - `as_of_date`: `top10_holders`, `top10_floatholders`, `pledge_stat`, `pledge_detail`
- Document the new lane and the trigger rules in `README.md`.

**Step 2: Run test to verify it passes**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'reference'`

Expected: PASS.

### Task 4: Verify the app-level integration

**Files:**
- None beyond previous tasks

**Step 1: Run the broader verification**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py`

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'not root_compatibility_layer_has_been_removed'`

Run: `bash apps/stock_data_platform/scripts/run_stock_data_reference.sh --help`

Expected: targeted suites pass and the runner help prints successfully.
