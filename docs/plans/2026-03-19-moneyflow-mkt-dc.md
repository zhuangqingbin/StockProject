# MoneyFlow Mkt DC Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the TuShare `moneyflow_mkt_dc` money-flow fetcher, expose it through the fetcher registry, and schedule it like the existing DC money-flow job.

**Architecture:** Implement one new `money_flow_data` fetcher module with explicit `fields` and `table_schema`, then wire it into the package exports and `jobs/catalog.py`. Protect the behavior with focused registry/job/doc-contract tests and update the lightweight README counts to keep project summaries consistent.

**Tech Stack:** Python 3.11, pandas, pytest, TuShare, existing `data_pipeline_ts` fetcher/job registry.

### Task 1: Add the failing tests

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py`
- Modify: `apps/data_hub/data_pipeline_ts/tests/test_executor.py`

**Step 1: Write the failing test**

- Add `MoneyFlowMktDCFetch` to the expected registry set.
- Add a job assertion for `money_flow_mkt_dc` using the same profile pattern chosen for the DC money-flow family.
- Add a fetcher-level assertion covering column order/schema for one representative field.
- Add a doc-contract assertion that the new money-flow fetcher is covered.

**Step 2: Run test to verify it fails**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py apps/data_hub/data_pipeline_ts/tests/test_executor.py -k 'money_flow_mkt_dc or MoneyFlowMktDCFetch or money_flow_data_fetchers_are_covered'`

Expected: FAIL because the new fetcher and job are not registered yet.

### Task 2: Implement the fetcher and registry wiring

**Files:**
- Create: `apps/data_hub/data_pipeline_ts/fetchers/money_flow_data/stock_money_flow_mkt_dc.py`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/money_flow_data/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/__init__.py`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/catalog.py`

**Step 1: Write minimal implementation**

- Create `MoneyFlowMktDCFetch` using endpoint `moneyflow_mkt_dc`.
- Keep `read_data()` consistent with other money-flow fetchers: `self.client.call(endpoint, fields=",".join(self.fields), **kwargs)`.
- Define explicit `fields`, `table_schema`, and composite indexes.
- Export it from the package and add it to `JOB_FETCHERS`.
- Register the job in `catalog.py`.

**Step 2: Run targeted tests**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py apps/data_hub/data_pipeline_ts/tests/test_executor.py -k 'money_flow_mkt_dc or MoneyFlowMktDCFetch or money_flow_data_fetchers_are_covered'`

Expected: PASS

### Task 3: Update summaries and verify

**Files:**
- Modify: `apps/data_hub/data_pipeline_ts/README.md`
- Modify: `apps/data_hub/data_pipeline_ts/fetchers/README.md`
- Modify: `apps/data_hub/data_pipeline_ts/jobs/README.md`

**Step 1: Update counts and tables**

- Add the new fetcher to the money-flow tables.
- Increment fetcher/job counts that are affected by the new job.

**Step 2: Run focused verification**

Run:
`python3 -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py apps/data_hub/data_pipeline_ts/tests/test_fetcher_doc_contracts.py apps/data_hub/data_pipeline_ts/tests/test_executor.py`

Expected: PASS
