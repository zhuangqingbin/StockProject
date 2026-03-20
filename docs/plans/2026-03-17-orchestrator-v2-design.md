# Orchestrator V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a new Python-native scheduler under `apps/stock_data_platform_v1/orchestrator_v2/` that replaces YAML-driven orchestration with a single Python entrypoint while preserving backfill, infrastructure sync, idempotent writes, run logging, and optional precompute hook behavior.

**Architecture:** Keep fetchers, `ExecutionContext`, `DatabaseWriter`, and `trigger_stock_bi_v1_precompute` as the stable runtime core. Implement a thin orchestrator layer with Python-native job registration, selection, execution, and CLI parsing entirely inside the new folder, without modifying the existing pipeline or scripts.

**Tech Stack:** Python 3.11+, `argparse`, `dataclasses`, `ThreadPoolExecutor`, existing fetchers/context/writer/hook modules, `pytest`.

### Task 1: Create failing tests for the new orchestrator runtime

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`
- Create: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_main.py`

**Step 1: Write failing test for single-run execution**

Cover:
- selecting a job by name
- rendering params from `ExecutionContext`
- writing data through `DatabaseWriter`
- recording `job_run_log`
- optional post-hook invocation only when rows are written

**Step 2: Run test to verify it fails**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py -k run_once`

Expected: FAIL because orchestrator_v2 modules do not exist yet.

**Step 3: Write failing test for backfill and infrastructure modes**

Cover:
- iterating date ranges
- skipping non-trade days
- validating `trade_cal` requires `start` and `end`
- resolving infrastructure target kwargs

**Step 4: Run test to verify it fails**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: FAIL with missing imports / missing functions.

### Task 2: Implement orchestrator_v2 domain models and Python registry

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/__init__.py`
- Create: `apps/stock_data_platform_v1/orchestrator_v2/models.py`
- Create: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`

**Step 1: Define `JobSpec` and `InfrastructureSpec`**

Include:
- `name`
- `fetcher_cls`
- `table_name`
- `profile`
- `params`
- `scope_columns`
- `source`
- `table_schema`

**Step 2: Encode all current jobs in Python**

Port the current YAML definitions into Python-native lists and dicts:
- daily jobs
- financial jobs
- reference jobs
- special jobs
- infrastructure targets

**Step 3: Add helpers**

Include:
- all jobs list
- job lookup by name
- infrastructure lookup by target
- selection by profile / name

### Task 3: Implement orchestrator_v2 execution runtime

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/executor.py`

**Step 1: Implement job selection and validation**

Cover:
- all jobs when no selector is passed
- unknown job name validation
- unknown profile validation

**Step 2: Implement single-job execution**

Behavior:
- create fetcher instance
- render params
- normalize return to DataFrame
- convert `JobSpec` to existing `JobDefinition`
- write through existing `DatabaseWriter`
- return existing `JobRunResult`

**Step 3: Implement grouped profile execution**

Behavior:
- group selected jobs by `profile`
- run jobs in parallel within a profile
- record run result after each future completes
- collect changed tables for optional hook

**Step 4: Implement `run_once`, `run_backfill`, and `run_infrastructure`**

Behavior:
- `run_once`: use `ExecutionContext.for_as_of()`
- `run_backfill`: iterate date range and skip non-trade days
- `run_infrastructure`: bypass `ExecutionContext` except trade calendar ranges

### Task 4: Implement single Python CLI entrypoint

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/main.py`

**Step 1: Add CLI parser**

Support:
- `--mode once|backfill|infrastructure`
- `--profiles`
- `--jobs`
- `--targets`
- `--as-of`
- `--start`
- `--end`
- `--disable-hook`
- `--max-workers`

**Step 2: Wire parser to runtime**

Behavior:
- `once` -> `run_once`
- `backfill` -> `run_backfill`
- `infrastructure` -> `run_infrastructure`

### Task 5: Document the new orchestrator

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/README.md`

**Step 1: Document architecture and commands**

Include:
- why this folder exists
- runtime structure
- supported modes
- example commands
- what is intentionally reused from old pipeline

### Task 6: Verify implementation

**Files:**
- Verify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`
- Verify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_main.py`

**Step 1: Run targeted orchestrator tests**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests`

Expected: PASS

**Step 2: Run a basic CLI smoke check**

Run: `apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m apps.stock_data_platform_v1.orchestrator_v2.main --help`

Expected: exit 0 and show orchestrator_v2 options.
