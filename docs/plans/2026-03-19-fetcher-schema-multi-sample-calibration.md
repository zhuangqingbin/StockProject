# Fetcher Schema Multi-Sample Calibration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix schema calibration blind spots caused by single-sample TuShare fetches so historically sparse numeric fields such as `stock_balancesheet_vip.lending_funds` are inferred correctly.

**Architecture:** Extend calibration from one live sample per fetcher to multiple live samples chosen from historically successful run dates, then merge evidence across frames before inferring column types. Keep the change narrow: preserve current inference rules, add deterministic multi-sample selection, and lock the behavior with regression tests before applying fresh schema updates.

**Tech Stack:** Python 3.11, pandas, SQLAlchemy, existing TuShare fetchers, pytest.

### Task 1: Reproduce the single-sample blind spot

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`

**Step 1: Write the failing tests**

Add tests that:
- assert `BalancesheetVipFetch.table_schema.columns["lending_funds"].dtype == "DOUBLE"`
- prove a later all-null frame plus an earlier numeric frame should infer `DOUBLE`

**Step 2: Run test to verify it fails**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py -k lending_funds`

Expected:
- failure because `lending_funds` is still `TEXT`

### Task 2: Add multi-sample parameter selection

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/schema_calibration.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`

**Step 1: Write the failing tests**

Add tests that:
- select multiple sample param sets from historical `job_run_log` successes
- prefer non-empty successful dates over the latest single date
- keep existing special cases such as `trade_cal` and `pledge_detail`

**Step 2: Run test to verify it fails**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py -k sample_param_sets`

Expected:
- failure because only single-sample resolution exists

**Step 3: Write minimal implementation**

Implement:
- deterministic multi-sample date selection from `job_run_log`
- fallback to existing single-sample behavior when history is unavailable
- frame aggregation across sample runs before schema comparison

### Task 3: Re-run live calibration and apply schema fixes

**Files:**
- Modify fetchers under `apps/data_hub/data_pipeline_ts/fetchers/**`
- Regenerate: `apps/data_hub/data_pipeline_ts/.cache/schema_calibration_report.json`

**Step 1: Run calibration**

Run:
`python3 apps/data_hub/data_pipeline_ts/scripts/calibrate_fetcher_schemas.py`

**Step 2: Apply report**

Run:
`python3 apps/data_hub/data_pipeline_ts/scripts/calibrate_fetcher_schemas.py --apply`

**Step 3: Re-run calibration**

Run the calibration again and confirm representative fields such as `lending_funds` now produce `diffs=0`.

### Task 4: Verify end to end

**Files:**
- Modify tests only if verification reveals a missed regression

**Step 1: Run focused verification**

Run:
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_writer.py`

**Step 2: Confirm live evidence**

Use real TuShare samples on multiple dates to confirm the originally missed fields now align with committed schemas.
