# data_pipeline_ts Fetcher Full Fields Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make every `data_pipeline_ts` fetcher request the full documented Tushare output field set, preserving the field order from the corresponding API document.

**Architecture:** Keep the current explicit-fetcher structure. Lock the contract with a doc-driven regression test that maps each fetcher to a local Tushare reference, then expand the mismatched fetchers so `fields` and `table_schema.columns` cover the full documented output. Preserve fetcher-specific internal fields such as `snapshot_date` by appending them after documented API fields.

**Tech Stack:** Python 3.11, pytest, pandas, local Tushare markdown references under `/Users/qingbin.zhuang/.agents/skills/tushare/references`

### Task 1: Lock the doc contract in tests

**Files:**
- Create or modify: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`
- Read: `/Users/qingbin.zhuang/.agents/skills/tushare/references/**/*.md`

**Step 1: Write the failing test**

- Add a regression test that:
  - maps each fetcher class to the correct Tushare API reference
  - parses the documented output field order from the local markdown file
  - asserts `fetcher.fields` equals the documented field order
  - asserts `table_schema.columns` covers every field in `fetcher.fields`
- Handle documented aliases such as `income_vip -> income`, `balancesheet_vip -> balancesheet`, `stock_st -> st`
- Handle `PledgeDetailFetch` as “documented API fields + appended internal `snapshot_date`”

**Step 2: Run test to verify it fails**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py -k documented`

Expected: FAIL because multiple fetchers currently request only subsets of documented fields or use a different order.

### Task 2: Expand mismatched fetchers

**Files:**
- Modify the mismatched fetchers under `apps/data_hub/data_pipeline_ts/fetchers/`
- Likely targets:
  - `basic_data/stock_basic.py`
  - `basic_data/stock_company.py`
  - `basic_data/stock_st.py`
  - `basic_data/trade_cal.py`
  - `board_data/stock_hm_list.py`
  - `board_data/stock_kpl_concept_cons.py`
  - `board_data/stock_kpl_list.py`
  - `board_data/stock_limit_list_d.py`
  - `board_data/stock_top_inst.py`
  - `financial_data/stock_balancesheet_vip.py`
  - `financial_data/stock_cashflow_vip.py`
  - `financial_data/stock_express_vip.py`
  - `financial_data/stock_fina_indicator_vip.py`
  - `financial_data/stock_forecast_vip.py`
  - `financial_data/stock_income_vip.py`
  - `money_flow_data/stock_money_flow_dc.py`
  - `reference_data/stock_pledge_detail.py`
  - `reference_data/stock_stk_holdertrade.py`
  - `reference_data/stock_top10_floatholders.py`
  - `reference_data/stock_top10_holders.py`

**Step 1: Update `fields`**

- Replace subset field lists with the full documented output fields in documented order.
- Preserve existing fetcher-specific behavior.
- For augmented fetchers, keep internal fields after the documented API fields.

**Step 2: Expand `table_schema`**

- Ensure every field in `fields` exists in `table_schema.columns`
- Preserve existing indexed field types
- Prefer:
  - `CHAR(8)` for compact date fields
  - `VARCHAR(16)` for `ts_code`-style identifiers
  - `DOUBLE` for documented numeric fields
  - `TEXT` for long descriptive strings unless an indexed column requires a bounded `VARCHAR`

**Step 3: Keep current behavior green**

- Do not change fetcher parameter semantics
- Do not reintroduce schema builder helpers
- Keep `snapshot_date` and similar internal enrichment behavior intact

### Task 3: Verify and stabilize

**Files:**
- Modify if needed: `apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`

**Step 1: Run focused tests**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py`

Expected: PASS

**Step 2: Run broader pipeline coverage**

Run: `apps/data_hub/.venv-x86_64/bin/python -m pytest -q apps/data_hub/data_pipeline_ts/tests`

Expected: PASS

**Step 3: Document any residual caveats**

- Note any fetchers whose API docs and runtime augmentation intentionally differ
- Note any field type compromises taken to keep write-path safety
