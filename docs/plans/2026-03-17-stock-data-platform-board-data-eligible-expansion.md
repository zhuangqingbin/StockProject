# Stock Data Platform Board Data Eligible Expansion Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the remaining Tushare board-topic endpoints that are actually available at 5120 points and wire them into the right job lanes.

**Architecture:** Keep all 1.8 board-topic fetchers under `DataFetch/BoardData/` with one class per file. Put pure daily snapshot tables in `daily_jobs.yaml`, and keep non-standard board refreshes in `special_jobs.yaml` with a dedicated runner so they do not pollute the default trade-date schedule.

**Tech Stack:** Python 3.11, pandas, pytest, YAML job configs, existing `BaseDataFetch` runtime.

### Task 1: Lock scope and triggers in tests

**Files:**
- Modify: `apps/stock_data_platform/tests/test_smoke.py`
- Modify: `apps/stock_data_platform/tests/test_daily_jobs.py`
- Modify: `apps/stock_data_platform/tests/test_board_jobs.py`

**Step 1: Write the failing tests**

Cover:
- `BoardData/` file layout for `hm_list`, `kpl_list`, `kpl_concept_cons`
- `DataFetch.__all__` exports
- `daily_jobs.yaml` entry for `kpl_list`
- `special_jobs.yaml` entries for `hm_list` and `kpl_concept_cons`
- `run_stock_data_special.sh`
- fetcher behavior and field order

**Step 2: Run tests to verify they fail**

Run:
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_board_jobs.py`
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'boarddata or special_jobs or special_runner or exports_only_runtime_fetchers'`

Expected: FAIL because the new files and exports do not exist yet.

### Task 2: Implement the fetchers

**Files:**
- Create: `apps/stock_data_platform/DataFetch/BoardData/hm_list.py`
- Create: `apps/stock_data_platform/DataFetch/BoardData/kpl_list.py`
- Create: `apps/stock_data_platform/DataFetch/BoardData/kpl_concept_cons.py`
- Modify: `apps/stock_data_platform/DataFetch/BoardData/__init__.py`
- Modify: `apps/stock_data_platform/DataFetch/__init__.py`

**Step 1: Write minimal implementation**

- `HMListFetch`: single call, no params, stable field order
- `KPLListFetch`: trade-date triggered, fan out internally by tag and concatenate
- `KPLConceptConsFetch`: trade-date triggered, single call

**Step 2: Re-run focused tests**

Run: `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_board_jobs.py`

Expected: PASS.

### Task 3: Wire lanes and docs

**Files:**
- Modify: `apps/stock_data_platform/jobs/daily_jobs.yaml`
- Create: `apps/stock_data_platform/jobs/special_jobs.yaml`
- Create: `apps/stock_data_platform/scripts/run_stock_data_special.sh`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Register jobs**

- `kpl_list` in `daily_jobs.yaml` with `trade_date`
- `hm_list` in `special_jobs.yaml` with no params and `scope_columns: [name]`
- `kpl_concept_cons` in `special_jobs.yaml` with `trade_date`

**Step 2: Document trigger strategy**

- daily lane for `top_list`, `top_inst`, `limit_list_d`, `kpl_list`
- special lane for `hm_list`, `kpl_concept_cons`
- note why `kpl_concept_cons` is special: official page says source currently has no new increments

### Task 4: Verify and summarize

**Files:**
- Modify only if verification exposes issues

**Step 1: Run checks**

Run:
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_board_jobs.py`
- `bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_smoke.py -k 'boarddata or special_jobs or special_runner or exports_only_runtime_fetchers'`
- `bash apps/stock_data_platform/scripts/run_stock_data_special.sh --help`

**Step 2: Summarize**

- list the 5120-point-eligible board endpoints that are now wired:
  - `top_list`
  - `top_inst`
  - `limit_list_d`
  - `hm_list`
  - `kpl_list`
  - `kpl_concept_cons`
