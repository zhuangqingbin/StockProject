# Reference Daily Direct Date Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Switch `top10_holders`, `top10_floatholders`, and `pledge_stat` to direct day-level triggering using the trigger date as the API date parameter, without extra stock-code fan-out or snapshot-date probing.

**Architecture:** Keep the existing fetcher and writer framework, but simplify three reference-data fetchers so they call the upstream API directly with `ann_date` or `end_date`. Update the Python registry so these jobs live in the calendar-driven daily profile and write by source date instead of `snapshot_date`.

**Tech Stack:** Python 3.11, pandas, pytest, orchestrator_v2 registry/runtime, TuShare fetchers

### Task 1: Write failing fetcher tests for direct date behavior

**Files:**
- Modify: `apps/stock_data_platform_v1/tests/test_fetchers.py`
- Modify: `apps/stock_data_platform_v1/tests/test_common.py`

**Step 1: Write the failing tests**

Add tests that assert:
- `Top10HoldersFetch.fetch(ann_date="20260317")` calls `top10_holders` once with `ann_date="20260317"` and does not add `snapshot_date`
- `Top10FloatHoldersFetch.fetch(ann_date="20260317")` calls `top10_floatholders` once with `ann_date="20260317"` and does not add `snapshot_date`
- `PledgeStatFetch.fetch(end_date="20260317")` calls `pledge_stat` once with `end_date="20260317"` and does not add `snapshot_date`
- old disclosure/fan-out/probe-specific tests are removed or rewritten to match the new contract

**Step 2: Run test to verify it fails**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py apps/stock_data_platform_v1/tests/test_common.py`

Expected: failures showing the old fetchers still require `as_of_date`, add `snapshot_date`, or fan out by `ts_code`.

### Task 2: Write failing registry tests for new daily profile mapping

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

**Step 1: Write the failing tests**

Add assertions that:
- `top10_holders.profile == "reference_calendar_nightly"`
- `top10_floatholders.profile == "reference_calendar_nightly"`
- `pledge_stat.profile == "reference_calendar_nightly"`
- `top10_holders.scope_columns == ("ann_date",)`
- `top10_floatholders.scope_columns == ("ann_date",)`
- `pledge_stat.scope_columns == ("end_date",)`
- `pledge_detail` and `hm_list` stay on `snapshot_date`

**Step 2: Run test to verify it fails**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: failures showing the registry still maps these jobs to `reference_manual_snapshot` with `snapshot_date`.

### Task 3: Implement minimal fetcher changes

**Files:**
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_top10_holders.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_top10_floatholders.py`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/reference_data/stock_pledge_stat.py`

**Step 1: Remove the extra date/snapshot logic**

- `Top10HoldersFetch`: keep only upstream fields, drop `snapshot_date`, drop report-period and stock-code resolution helpers, and call `self.client.call("top10_holders", ann_date=..., fields=...)`
- `Top10FloatHoldersFetch`: same pattern using `top10_floatholders`
- `PledgeStatFetch`: keep only upstream fields, drop `snapshot_date`, drop snapshot probing and bulk supplementation, and call `self.client.call("pledge_stat", end_date=..., fields=...)`

**Step 2: Run focused tests**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py apps/stock_data_platform_v1/tests/test_common.py`

Expected: PASS

### Task 4: Implement registry and doc updates

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/README.md`

**Step 1: Update registry**

- `top10_holders`: `profile="reference_calendar_nightly"`, `params={"ann_date": "{current_date}"}`, `scope_columns=("ann_date",)`
- `top10_floatholders`: same
- `pledge_stat`: `profile="reference_calendar_nightly"`, `params={"end_date": "{current_date}"}`, `scope_columns=("end_date",)`
- leave `pledge_detail` and `hm_list` unchanged

**Step 2: Update docs**

Explain that these three tables are now source-date-driven daily tables, not observation snapshot tables.

**Step 3: Run registry/doc-adjacent tests**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: PASS

### Task 5: Verify full relevant suites and rebuild impacted tables

**Files:**
- Runtime only

**Step 1: Run verification**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/tests apps/stock_data_platform_v1/orchestrator_v2/tests`

Expected: PASS with no failures

**Step 2: Rebuild affected data**

- Clear `stock_top10_holders`
- Clear `stock_top10_floatholders`
- Clear `stock_pledge_stat`
- Re-run current-day jobs using the new registry semantics

**Step 3: Smoke-check the rebuilt tables**

Run SQL checks confirming:
- `stock_top10_holders` has no `snapshot_date` column and writes by `ann_date`
- `stock_top10_floatholders` has no `snapshot_date` column and writes by `ann_date`
- `stock_pledge_stat` has no `snapshot_date` column and writes by `end_date`
