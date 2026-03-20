# Financial Dividend And Fina Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `dividend` and `fina_audit` financial-data fetchers to `data_pipeline_ts`, register them in the scheduled financial catalog, and cover the new behavior with focused regression tests.

**Architecture:** Implement two new fetcher classes under `fetchers/financial_data` following the existing explicit `fields` + `TableSchema` pattern. `DividendFetch` is a standard ann-date financial fetcher; `FinaAuditFetch` keeps the same scheduled `ann_date` entrypoint as other financial jobs but internally fans out by stock code because TuShare requires `ts_code`.

**Tech Stack:** Python 3.11, pandas, pytest, TuShare client wrapper, existing `BaseFetcher` and `JobSpec` wiring.

### Task 1: Add failing registration and contract tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`

**Step 1: Write the failing tests**

Add tests that:
- include `DividendFetch` and `FinaAuditFetch` in the expected job fetcher registry
- verify the registry count/message matches the expanded job set
- assert `DividendFetch.fields` and `FinaAuditFetch.fields` stay aligned with the TuShare reference docs

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py
```

Expected: FAIL because the new fetcher classes and catalog wiring do not exist yet.

### Task 2: Add failing fetcher behavior tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`

**Step 1: Write the failing tests**

Add tests that:
- verify `DividendFetch.read_data(ann_date=...)` calls `dividend` with the declared fields and preserves column order
- verify `FinaAuditFetch.read_data(ann_date=...)` resolves stock codes, calls `fina_audit` once per code, concatenates rows, and returns the declared column order
- verify `FinaAuditFetch.read_data(ts_code=..., ann_date=...)` skips fan-out and queries the explicit code directly

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py -k 'dividend or fina_audit'
```

Expected: FAIL because the new fetcher implementations do not exist yet.

### Task 3: Implement the two financial fetchers

**Files:**
- Create: `apps/data_hub/data_pipeline_ts/fetchers/financial_data/stock_dividend.py`
- Create: `apps/data_hub/data_pipeline_ts/fetchers/financial_data/stock_fina_audit.py`

**Step 1: Write minimal implementation**

Implement `DividendFetch` with:
- explicit docstring, `fields`, and `TableSchema`
- `read_data()` that delegates to `self.client.call("dividend", ...)`

Implement `FinaAuditFetch` with:
- explicit docstring, `fields`, and `TableSchema`
- `_resolve_stock_codes()` that accepts explicit `ts_code`/`stock_codes` and otherwise fetches stock codes from `stock_basic`
- `_fetch_by_stock_codes()` that calls `fina_audit` once per code and concatenates non-empty frames
- `read_data()` that preserves the scheduled `ann_date` contract while performing internal fan-out

**Step 2: Run targeted tests**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py -k 'dividend or fina_audit'
```

Expected: PASS for the new behavior tests.

### Task 4: Register exports and scheduled jobs

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/financial_data/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/catalog.py`

**Step 1: Write minimal implementation**

Register:
- `DividendFetch`
- `FinaAuditFetch`

Add both jobs to `FINANCIAL_JOBS` using the same `ProfileId.FINANCIAL_CALENDAR_NIGHTLY` scheduling style as the other financial fetchers with `params={"ann_date": "{current_date}"}` and `scope_columns=("ann_date",)`.

**Step 2: Run focused tests**

Run:

```bash
python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py
```

Expected: PASS for registry and contract coverage.

### Task 5: Verify broader regressions

**Files:**
- Test: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Test: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`
- Test: `apps/data_hub/data_pipeline_ts/tests/test_module_boundaries.py`
- Test: `apps/data_hub/data_pipeline_ts/tests/test_scripts.py`

**Step 1: Run verification**

Run:

```bash
python3 -m pytest -q \
  apps/data_hub/data_pipeline_ts/tests/test_fetchers.py \
  apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py \
  apps/data_hub/data_pipeline_ts/tests/test_module_boundaries.py \
  apps/data_hub/data_pipeline_ts/tests/test_scripts.py
```

Expected: PASS with no new contract or wiring regressions.
