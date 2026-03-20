# Fetcher Schema Calibration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Use real TuShare API samples to validate and correct `table_schema` definitions for all 42 fetchers in `apps/data_hub/data_pipeline_ts`.

**Architecture:** Add a small schema calibration module that can resolve sample params, call real fetchers, infer candidate column types from returned DataFrames, and emit diffs against current fetcher schemas. Use the tool to batch-update fetcher definitions, then keep the inference logic covered by unit tests so future re-calibration is repeatable.

**Tech Stack:** Python 3.11, pandas, SQLAlchemy, existing TuShare client/fetchers, pytest.

### Task 1: Build and test calibration inference primitives

**Files:**
- Create: `apps/data_hub/data_pipeline_ts/schema_calibration.py`
- Create: `apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`

**Step 1: Write the failing tests**

Add tests for:
- numeric-like object series infers `DOUBLE`
- date-like 8-digit series infers `CHAR(8)`
- short categorical `_type` series infers `VARCHAR(8|16|32)`
- long free-text series infers `TEXT`
- `ts_code` always infers `VARCHAR(16)`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`
Expected: import/module failure because calibration module does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- a column inference function using real value inspection, not just pandas dtype
- a frame/schema comparison function returning only changed columns

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`
Expected: all tests pass.

### Task 2: Build a real-sample calibration runner

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/schema_calibration.py`
- Create: `apps/data_hub/data_pipeline_ts/scripts/calibrate_fetcher_schemas.py`

**Step 1: Write the failing test**

Add unit tests for:
- resolving sample params from `JobSpec.params`
- preferring latest scope value from DB when placeholders such as `{trade_date}` / `{current_date}` are present
- leaving infrastructure fetchers parameterless

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py -k sample`
Expected: failure on missing param resolution support.

**Step 3: Write minimal implementation**

Implement:
- spec enumeration for `ALL_JOBS` + `INFRASTRUCTURE_TARGETS`
- sample-param resolution from table scope columns
- live fetch execution using existing fetchers
- diff report output that includes fetcher name, table name, params used, rows fetched, and changed columns

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`
Expected: all tests pass.

### Task 3: Run calibration and review diffs

**Files:**
- Generate: temporary report under repo root or `.cache`

**Step 1: Run calibration against all 42 fetchers**

Run:
`PYTHONPATH="$PWD" python3 apps/data_hub/data_pipeline_ts/scripts/calibrate_fetcher_schemas.py --write-report`

Expected:
- each fetcher is sampled from real TuShare data
- a machine-readable diff report is produced
- failures are explicit per fetcher if any API sample cannot be fetched

**Step 2: Review report**

Focus on:
- numeric columns currently typed as `TEXT` or `VARCHAR`
- string/category columns currently typed as `DOUBLE`
- long text fields incorrectly typed as short string columns

### Task 4: Apply schema updates to fetcher files

**Files:**
- Modify fetcher files under `apps/data_hub/data_pipeline_ts/fetchers/**`

**Step 1: Write the failing regression test**

Add or extend tests to assert representative corrected columns for changed fetchers, especially previously wrong wide financial columns such as `div_receiv`.

**Step 2: Run the focused tests to verify failure**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py -k calibration`

Expected: failing assertions until schema definitions are updated.

**Step 3: Apply file updates**

Update `ColumnDef("...")` dtypes in fetcher schemas to match calibration output.

**Step 4: Run focused tests**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`

Expected: pass.

### Task 5: Verify writer compatibility and live calibration output

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_writer.py` if new type-repair cases need coverage

**Step 1: Add failing test if needed**

Cover any new repair scenario introduced by corrected schemas.

**Step 2: Run failure**

Run the focused writer test that exercises the new scenario.

**Step 3: Update implementation only if required**

Keep persistence logic unchanged unless the new schema set reveals a real mismatch.

**Step 4: Final verification**

Run:
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_schema_calibration.py`
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_writer.py`
- one fresh calibration run over all fetchers

Expected: tests pass, calibration script runs, and representative live samples match the committed schemas.
