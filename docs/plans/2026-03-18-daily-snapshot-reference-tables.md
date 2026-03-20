# Daily Snapshot Reference Tables Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preserve daily observation snapshots for `stock_top10_holders`, `stock_top10_floatholders`, `stock_pledge_stat`, `stock_pledge_detail`, and `stock_hm_list`.

**Architecture:** Add an explicit `snapshot_date` column to the affected fetchers, populate it from the orchestrator run day, and change orchestrator scopes so writes replace one snapshot day at a time instead of overwriting by `end_date`, `ts_code`, or `name`.

**Tech Stack:** Python 3.11, pandas, SQLAlchemy, pytest

### Task 1: Lock the new snapshot contract with tests

**Files:**
- Modify: `apps/stock_data_platform_v1/tests/test_fetchers.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

**Step 1: Write the failing tests**

- Add fetcher tests asserting:
  - `Top10HoldersFetch.fetch(as_of_date=...)` returns a `snapshot_date` column and does not pass `as_of_date` through to `client.call`.
  - `Top10FloatHoldersFetch.fetch(as_of_date=...)` returns a `snapshot_date` column.
  - `PledgeStatFetch.fetch(as_of_date=...)` returns a `snapshot_date` column.
  - `PledgeDetailFetch.fetch(as_of_date=...)` returns a `snapshot_date` column.
  - `HMListFetch.fetch(as_of_date=...)` returns a `snapshot_date` column and does not pass `as_of_date` through to `client.call`.
- Add orchestrator tests asserting:
  - the five jobs use `snapshot_date` in `scope_columns`
  - `hm_list` receives `as_of_date` from the registry params

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py
```

Expected: failures referencing missing `snapshot_date` columns and old scopes.

### Task 2: Add snapshot columns to the five fetchers

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_top10_holders.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_top10_floatholders.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_pledge_stat.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_pledge_detail.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/board_data/stock_hm_list.py`

**Step 1: Implement the minimal code**

- Add `snapshot_date` to `fields`, `table_schema`, and useful snapshot indexes.
- Derive `snapshot_date` from `as_of_date` inside each fetcher.
- Keep upstream API params unchanged:
  - `top10_*` still call the Tushare endpoints with `period`
  - `pledge_stat` still probes and fetches by resolved `end_date`
  - `pledge_detail` still fans out by `ts_code`
  - `hm_list` still calls `hm_list` without a date filter
- Append the resolved `snapshot_date` to every returned row before reindexing.

**Step 2: Run the targeted tests**

Run:

```bash
python -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py
```

Expected: pass.

### Task 3: Change orchestrator scopes to snapshot partitions

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`

**Step 1: Implement the minimal code**

- Change the five job specs to use `scope_columns=("snapshot_date",)`.
- Pass `params={}` to `hm_list`.

**Step 2: Run orchestrator tests**

Run:

```bash
python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py
```

Expected: pass.

### Task 4: Update docs and run full verification

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/README.md`

**Step 1: Document the new snapshot behavior**

- Explain that the five tables now store `snapshot_date` daily observations.
- Clarify that `end_date` remains the source business date, not the write partition.

**Step 2: Run the full relevant suite**

Run:

```bash
python -m pytest -q apps/stock_data_platform_v1/tests apps/stock_data_platform_v1/orchestrator_v2/tests
```

Expected: pass.

### Task 5: Backfill the confirmed snapshot tables

**Files:**
- No source changes.

**Step 1: Rebuild affected historical data**

- Remove old rows from the five target tables before re-backfill because old rows do not have `snapshot_date`.
- Re-run:
  - `top10_holders`
  - `top10_floatholders`
  - `pledge_stat`
  - `pledge_detail`
  - `hm_list`

**Step 2: Verify resulting partitions**

- Confirm each table now has a populated `snapshot_date`.
- Confirm multiple snapshot days coexist without overwrite.
