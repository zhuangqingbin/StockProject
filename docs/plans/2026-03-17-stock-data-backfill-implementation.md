# Stock Data Backfill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a resumable backfill runner that can download and store all configured stock data jobs into MySQL for the range 2010-01-01 through 2026-03-16 using batching strategies matched to each dataset.

**Architecture:** Add a dedicated `jobs.backfill_runner` module that plans batches by data shape instead of reusing the single-date daily runner. Keep the existing daily scheduling flow unchanged and execute backfill batches directly with cloned `JobDefinition` instances plus runtime writer logic.

**Tech Stack:** Python 3.11, existing `apps.stock_data_platform.jobs.runtime`, SQLAlchemy/MySQL, Tushare fetchers, pytest.

### Task 1: Backfill Plan Model

**Files:**
- Create: `apps/stock_data_platform/jobs/backfill_runner.py`
- Test: `apps/stock_data_platform/tests/test_backfill_runner.py`

**Step 1: Write the failing test**

Cover:
- trade-date batch planning
- calendar-date batch planning
- report-period batch planning
- manual snapshot / stock-scan batch planning

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Add batch dataclasses and planner helpers that produce deterministic batch sequences for:
- trade-day jobs
- calendar-day jobs
- quarter-period jobs
- low-frequency stock-scan jobs

**Step 4: Run test to verify it passes**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: PASS for planning behavior.

### Task 2: Batch Execution and Retry

**Files:**
- Modify: `apps/stock_data_platform/jobs/backfill_runner.py`
- Test: `apps/stock_data_platform/tests/test_backfill_runner.py`

**Step 1: Write the failing test**

Cover:
- batch execution builds overridden params correctly
- retries only failed jobs in a batch
- checkpoint state advances after success
- post-hook stays disabled during backfill

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: FAIL on missing executor/state behavior.

**Step 3: Write minimal implementation**

Add:
- batch executor
- retry loop
- JSON checkpoint persistence
- CLI entrypoint

**Step 4: Run test to verify it passes**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: PASS.

### Task 3: Stock-Universe Chunking Support

**Files:**
- Modify: `apps/stock_data_platform/DataFetch/ReferenceData/stock_universe.py`
- Test: `apps/stock_data_platform/tests/test_daily_jobs.py`
- Test: `apps/stock_data_platform/tests/test_backfill_runner.py`

**Step 1: Write the failing test**

Cover:
- explicit stock-code sequences bypass live-only lookup
- optional full-status universe collection returns live, paused, and delisted codes

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_daily_jobs.py apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: FAIL because the helper only supports current live codes.

**Step 3: Write minimal implementation**

Allow the helper to:
- accept explicit stock code lists
- optionally fetch all historical statuses for backfill jobs

**Step 4: Run test to verify it passes**

Run: `python -m pytest -q apps/stock_data_platform/tests/test_daily_jobs.py apps/stock_data_platform/tests/test_backfill_runner.py`
Expected: PASS.

### Task 4: Operational Docs and Scripts

**Files:**
- Modify: `apps/stock_data_platform/jobs/README.md`
- Create: `apps/stock_data_platform/scripts/run_stock_data_backfill.sh`

**Step 1: Write the failing test**

No dedicated automated test; validate via command rendering and help output.

**Step 2: Write minimal implementation**

Document:
- lane breakdown
- batch sizes
- resume behavior
- production command for full backfill

Add a shell wrapper for the backfill CLI.

**Step 3: Run verification**

Run:
- `python -m apps.stock_data_platform.jobs.backfill_runner --help`
- `bash apps/stock_data_platform/scripts/run_stock_data_backfill.sh --help`

Expected: commands print usable help.

### Task 5: Verification and Controlled Launch

**Files:**
- Modify: none or `apps/stock_data_platform/jobs/README.md` for final notes

**Step 1: Run focused tests**

Run:
- `python -m pytest -q apps/stock_data_platform/tests/test_backfill_runner.py`
- `python -m pytest -q apps/stock_data_platform/tests/test_daily_jobs.py apps/stock_data_platform/tests/test_launchd_scheduler.py`

**Step 2: Run smoke backfill**

Run a narrow batch, for example one day and one week:
- trade-day lane for a single trade date
- announcement lane for a short natural-date window

**Step 3: Start full backfill**

Run the wrapper with checkpointing enabled for 2010-01-01 to 2026-03-16.
