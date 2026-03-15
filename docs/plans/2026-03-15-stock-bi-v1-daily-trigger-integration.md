# Stock BI V1 Daily Trigger Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire `stock_data_platform` daily jobs to call the new `stock_bi_v1` precompute endpoint at the correct end-of-run timing.

**Architecture:** Keep the legacy `stock_bi` sync path intact, add a separate HTTP trigger for `stock_bi_v1` precompute, and invoke it from `daily_runner` only after the full configured daily job set finishes successfully. Reuse the same local-port-scan HTTP pattern already used by the old BI sync so local multi-port development remains frictionless.

**Tech Stack:** Python job runner, urllib-based HTTP trigger, pytest

### Task 1: Record the integration scope

**Files:**
- Create: `docs/plans/2026-03-15-stock-bi-v1-daily-trigger-integration.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Step 1: Save the plan**

Capture that this slice belongs in `apps/stock_data_platform`, not `apps/stock_bi_v1`, and that the trigger must happen after all jobs complete rather than on a single job flag.

### Task 2: Add failing trigger regressions

**Files:**
- Create: `apps/stock_data_platform/tests/test_stock_bi_v1_sync.py`
- Modify: `apps/stock_data_platform/tests/test_daily_jobs.py`
- Modify: `apps/stock_data_platform/tests/test_smoke.py`

**Step 1: Write the failing tests**

Add coverage for:
- HTTP trigger port-scan fallback on the default local `8100` target
- `daily_runner` invoking V1 precompute after a full run succeeds
- `daily_runner` skipping V1 precompute for partial `--jobs` runs
- shell script exporting the new V1 precompute env vars

**Step 2: Run the targeted tests to verify RED**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_data_platform/tests/test_stock_bi_v1_sync.py apps/stock_data_platform/tests/test_daily_jobs.py apps/stock_data_platform/tests/test_smoke.py -q`

Expected: FAIL because the V1 trigger module and runner integration do not exist yet.

### Task 3: Implement the V1 trigger and runner wiring

**Files:**
- Create: `apps/stock_data_platform/jobs/stock_bi_v1_sync.py`
- Modify: `apps/stock_data_platform/jobs/daily_runner.py`
- Modify: `apps/stock_data_platform/jobs/__init__.py`
- Modify: `apps/stock_data_platform/scripts/run_stock_data_daily.sh`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Add the HTTP trigger**

Implement a focused `trigger_stock_bi_v1_precompute(trade_date, ...)` helper with env-driven enable/url/timeout/port-scan settings and the same localhost port-scan resilience as the old BI sync.

**Step 2: Wire the end-of-run trigger**

Call the V1 precompute trigger only when `daily_runner` is executing the full configured job set. Preserve the existing old-BI sync behavior and do not move it onto the new V1 path.

**Step 3: Pass env vars through the shell launcher**

Expose V1 precompute env vars from `run_stock_data_daily.sh` so scheduled runs can override URL, timeout, and port scan count without editing the script.

### Task 4: Verify and document

**Files:**
- Modify as needed: touched files above

**Step 1: Run targeted stock-data tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_data_platform/tests/test_stock_bi_v1_sync.py apps/stock_data_platform/tests/test_daily_jobs.py apps/stock_data_platform/tests/test_smoke.py -q`

**Step 2: Update the local app README**

Document that the full daily run now triggers both the legacy BI sync and the V1 precompute endpoint, with separate env toggles.
