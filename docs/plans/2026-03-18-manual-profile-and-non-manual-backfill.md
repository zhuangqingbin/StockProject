# Manual Profile And Non-Manual Backfill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge `pledge_detail` and `hm_list` under a single `manual` profile, keep their snapshot semantics unchanged, and then backfill all non-manual data through `2026-03-17`.

**Architecture:** Keep the current job registry model and only rename the manual profiles plus the executor's serial-profile gate. Reuse existing scripts for infrastructure sync and date-range backfill, excluding the new `manual` profile from the replay run.

**Tech Stack:** Python 3.11, pytest, orchestrator_v2 registry/executor/runtime, MySQL

### Task 1: Write failing tests for the unified manual profile

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

**Step 1: Write the failing test**

Add assertions that:
- `hm_list.profile == "manual"`
- `pledge_detail.profile == "manual"`
- both still use `scope_columns=("snapshot_date",)`
- serial execution test uses `profile="manual"`

**Step 2: Run test to verify it fails**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: FAIL because registry still uses `manual_special` and `reference_manual_snapshot`, and executor only serializes `reference_manual_snapshot`.

### Task 2: Implement minimal registry and executor changes

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/executor.py`

**Step 1: Change the registry**

- set `pledge_detail.profile = "manual"`
- set `hm_list.profile = "manual"`

**Step 2: Change serial execution**

- replace `SERIAL_PROFILES = {"reference_manual_snapshot"}` with `{"manual"}`

**Step 3: Run test to verify it passes**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: PASS

### Task 3: Update docs and verify full suites

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`
- Modify: `apps/stock_data_platform_v1/fetchers/tushare/README.md`

**Step 1: Update docs**

- replace `reference_manual_snapshot` / `manual_special` mentions with a single `manual` profile where appropriate
- document that `manual` contains `pledge_detail` and `hm_list`

**Step 2: Run full relevant tests**

Run: `python3.11 -m pytest -q apps/stock_data_platform_v1/tests apps/stock_data_platform_v1/orchestrator_v2/tests`

Expected: PASS

### Task 4: Sync infrastructure and start non-manual backfill

**Files:**
- Runtime only

**Step 1: Sync infrastructure**

Run:
- `bash apps/stock_data_platform_v1/orchestrator_v2/scripts/sync_infrastructure.sh --targets stock_basic,stock_company`
- `bash apps/stock_data_platform_v1/orchestrator_v2/scripts/sync_infrastructure.sh --targets trade_cal --start 20200101 --end 20260317`

**Step 2: Start backfill for all non-manual profiles**

Run:
`bash apps/stock_data_platform_v1/orchestrator_v2/scripts/run_backfill.sh --profiles trade_day_pre_open,trade_day_post_close_core,trade_day_post_close_extended,financial_calendar_nightly,reference_trade_day_post_close,reference_calendar_nightly --start 20200101 --end 20260317`

**Step 3: Smoke-check progress**

- verify the backfill process is alive
- inspect recent `job_run_log` rows to confirm non-manual jobs are writing
