# Stock Data Platform Board Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the Tushare 1.8 board-topic endpoints that are actually available at 5120 points to `stock_data_platform`.

**Architecture:** Create a dedicated `DataFetch/BoardData/` package and keep trigger semantics aligned with existing trade-date jobs. Reuse the current runtime contract: one job maps to one fetcher that returns a `DataFrame`, with `limit_list_d` internally splitting by exchange to stay under the documented row cap.

**Tech Stack:** Python 3.11, pandas, pytest, YAML job configs, existing `BaseDataFetch` runtime.

### Task 1: Lock the available-scope behavior in tests

**Files:**
- Modify: `apps/stock_data_platform/tests/test_smoke.py`
- Modify: `apps/stock_data_platform/tests/test_daily_jobs.py`

**Step 1: Write the failing tests**

Add tests for:
- `DataFetch/BoardData/` package file layout
- `TopListFetch`, `TopInstFetch`, `LimitListDFetch` exports
- `daily_jobs.yaml` entries for `top_list`, `top_inst`, `limit_list_d`
- Fetcher behavior and column order

**Step 2: Run test to verify it fails**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'boarddata or exports_only_runtime_fetchers'`

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py -k 'top_inst or limit_list_d or top_list'`

Expected: FAIL because `BoardData` and new exports/jobs do not exist yet.

### Task 2: Implement the board-topic fetchers

**Files:**
- Create: `apps/stock_data_platform/DataFetch/BoardData/__init__.py`
- Create: `apps/stock_data_platform/DataFetch/BoardData/top_list.py`
- Create: `apps/stock_data_platform/DataFetch/BoardData/top_inst.py`
- Create: `apps/stock_data_platform/DataFetch/BoardData/limit_list_d.py`
- Delete: `apps/stock_data_platform/DataFetch/FetchTopList.py`
- Modify: `apps/stock_data_platform/DataFetch/__init__.py`

**Step 1: Write minimal implementation**

- Move `TopListFetch` into `BoardData/top_list.py`
- Add `TopInstFetch`
- Add `LimitListDFetch`
- Keep Chinese field comments and stable `DataFrame` column order
- Re-export these classes from `DataFetch/__init__.py`

**Step 2: Run focused tests**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py -k 'top_inst or limit_list_d or top_list'`

Expected: PASS.

### Task 3: Wire board-topic jobs and docs

**Files:**
- Modify: `apps/stock_data_platform/jobs/daily_jobs.yaml`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Add job definitions**

- Keep `top_list` in `daily_jobs.yaml`
- Add `top_inst`
- Add `limit_list_d`
- Use `trade_date: "{{ trade_date }}"` and `scope_columns: [trade_date]`

**Step 2: Document trigger strategy**

- Note that only the 5120-point-available board endpoints are wired
- Explain that `limit_list_d` is trade-date triggered but internally split by exchange to avoid row-cap truncation

### Task 4: Verify and summarize

**Files:**
- Modify only if verification exposes issues

**Step 1: Run regression checks**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_daily_jobs.py`

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'not root_compatibility_layer_has_been_removed'`

**Step 2: Summarize**

- List the official Tushare availability conclusions used for scoping:
  - `top_list` available
  - `top_inst` available
  - `limit_list_d` available
  - `limit_step` unavailable at 5120
  - `limit_cpt_list` unavailable at 5120
  - `hm_detail` unavailable at 5120
