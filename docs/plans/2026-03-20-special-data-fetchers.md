# Special Data Fetchers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 10 TuShare special-data fetchers under `apps/data_hub/data_pipeline_ts/fetchers/special_data`, register them as `trade_date`-driven jobs, and wire tests/docs.

**Architecture:** Create a new `special_data` fetcher package, add one fetcher per TuShare endpoint, and register a new `SPECIAL_DATA_JOBS` group in `jobs/catalog.py`. Most endpoints call `self.client.call(...)` directly; `report_rc` maps external `trade_date` to `report_date`, and `cyq_chips` fans out by stock list because the API requires `ts_code`.

**Tech Stack:** Python 3.11, pandas, TuShare Pro, pytest.

### Task 1: Add failing catalog and registry tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_executor.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`

### Task 2: Add `special_data` fetcher package

**Files:**
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/__init__.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_report_rc.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_cyq_perf.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_cyq_chips.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_factor_pro.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_ccass_hold.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_hk_hold.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_auction_o.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_auction_c.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_ah_comparison.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_surv.py`

### Task 3: Register the new directory and jobs

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/catalog.py`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/__init__.py`

### Task 4: Update docs and counts

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/README.md`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/README.md`
- Modify: `apps/data_hub/data_pipeline_ts/README.md`

### Task 5: Verify

**Files:**
- Run: `python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_executor.py apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py apps/data_hub/data_pipeline_ts/tests/test_module_boundaries.py`
