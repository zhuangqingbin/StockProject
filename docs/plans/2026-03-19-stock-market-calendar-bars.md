# Stock Market Calendar Bars Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add six new `stock_market_data` fetchers for weekly, monthly, suspend, and qfq bar data, then register them as calendar-nightly jobs in `data_pipeline_ts`.

**Architecture:** Implement explicit one-class-per-file fetchers following the existing `fields` + `TableSchema` pattern. Direct TuShare endpoints (`weekly`, `monthly`, `suspend_d`) will call `self.client.call(...)`; qfq fetchers will call `pro_bar` with fixed `asset='E'`, `adj='qfq'`, and the corresponding `freq`, internally fanning out by stock code because `pro_bar` requires `ts_code`.

**Tech Stack:** Python 3.11, pandas, pytest, TuShare client wrapper, `BaseFetcher`, `JobSpec`.

### Task 1: Add failing registry, catalog, and contract tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`

**Step 1: Write the failing test**

Add tests that:
- include the six new fetchers in `EXPECTED_JOB_FETCHERS`
- assert the six new jobs are present in `ALL_JOBS`
- assert they use `financial_calendar_nightly`
- assert direct endpoint fetchers keep the expected column order
- assert qfq fetchers are covered by the TuShare contract lookup

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py
```

Expected: FAIL because the new fetchers and jobs do not exist yet.

### Task 2: Add failing qfq fan-out and client tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_provider_client.py`

**Step 1: Write the failing test**

Add tests that:
- verify a qfq fetcher fans out by stock code and fixes `asset='E'`, `adj='qfq'`, and `freq`
- verify explicit `ts_code` bypasses stock list fan-out
- verify `TuShareClient.pro_bar(...)` delegates to `tushare.pro_bar(...)` with `pro_api=self.pro`

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_provider_client.py -k 'qfq or weekly or monthly or suspend or pro_bar'
```

Expected: FAIL because the qfq fetchers and `TuShareClient.pro_bar` support are missing.

### Task 3: Implement the new fetchers and client support

**Files:**
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_weekly.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_monthly.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_suspend_d.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_daily_qfq.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_weekly_qfq.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/stock_monthly_qfq.py`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/client.py`

**Step 1: Write minimal implementation**

Implement:
- three direct fetchers for `weekly`, `monthly`, `suspend_d`
- three qfq fetchers with fixed `asset='E'`, `adj='qfq'`, `freq in {'D','W','M'}`
- `TuShareClient.pro_bar(...)` wrapper with the same cache/retry behavior as `call(...)`

**Step 2: Run focused tests**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_provider_client.py -k 'qfq or weekly or monthly or suspend or pro_bar'
```

Expected: PASS for the new fetcher and client behavior.

### Task 4: Wire exports and jobs

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/stock_market_data/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/catalog.py`

**Step 1: Write minimal implementation**

Export the six new fetchers and register six new jobs:
- `stock_weekly`
- `stock_monthly`
- `stock_suspend_d`
- `stock_daily_qfq`
- `stock_weekly_qfq`
- `stock_monthly_qfq`

Use `ProfileId.FINANCIAL_CALENDAR_NIGHTLY` for all six. Direct endpoint jobs should pass `trade_date={current_date}`; qfq jobs should pass `start_date={current_date}` and `end_date={current_date}`. Keep `scope_columns=("trade_date",)`.

**Step 2: Run focused tests**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py apps/data_hub/data_pipeline_ts/tests/test_provider_client.py
```

Expected: PASS for registry, catalog, client, and contract coverage.

### Task 5: Verify with live TuShare samples

**Files:**
- Test: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Test: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`
- Test: `apps/data_hub/data_pipeline_ts/tests/test_provider_client.py`

**Step 1: Run verification**

Run:

```bash
python3 -m pytest -q \
  apps/data_hub/data_pipeline_ts/tests/test_fetchers.py \
  apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py \
  apps/data_hub/data_pipeline_ts/tests/test_provider_client.py \
  apps/data_hub/data_pipeline_ts/tests/test_module_boundaries.py \
  apps/data_hub/data_pipeline_ts/tests/test_scripts.py
```

Then run a small live check using real TuShare samples for:
- `weekly`
- `monthly`
- `suspend_d`
- `pro_bar` qfq for `D/W/M`

Expected: PASSing tests plus live samples returning the expected columns.
