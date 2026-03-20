# Orchestrator V2 Layer Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce `orchestrator_v2` top-level module sprawl while preserving behavior and keeping the new scheduler self-contained.

**Architecture:** Keep the public shape small: `main.py` handles CLI, `executor.py` handles orchestration, `registry.py` holds Python-native job registration, and a single `runtime.py` owns execution context, DB access, validation, write semantics, and post-run hook logic. Tests move to the new import surface first, then implementation is simplified under that contract.

**Tech Stack:** Python 3.11, pytest, pandas, SQLAlchemy, shell scripts

### Task 1: Lock the new module boundary with failing tests

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py`

**Step 1: Write the failing test**

Change test imports to:

```python
from apps.stock_data_platform_v1.orchestrator_v2.runtime import DatabaseWriter, ExecutionContext
```

Keep the legacy-runtime guard in place.

**Step 2: Run test to verify it fails**

Run:

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q \
  apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py
```

Expected: fail with `ModuleNotFoundError` for `orchestrator_v2.runtime`

### Task 2: Implement the merged runtime module

**Files:**
- Create: `apps/stock_data_platform_v1/orchestrator_v2/runtime.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/executor.py`

**Step 1: Write minimal implementation**

Move these responsibilities into `runtime.py`:
- trade calendar access
- `ExecutionContext`
- MySQL engine builder
- DataFrame/schema validation
- `DatabaseWriter`
- precompute hook trigger

Update `executor.py` to import only from `runtime.py`.

**Step 2: Run tests to verify they pass**

Run:

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q \
  apps/stock_data_platform_v1/orchestrator_v2/tests
```

Expected: all `orchestrator_v2` tests pass.

### Task 3: Remove old split files and refresh docs

**Files:**
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/calendar.py`
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/context.py`
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/database.py`
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/validator.py`
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/hook.py`
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/writer.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`

**Step 1: Update docs**

Document that runtime concerns are consolidated into `runtime.py`.

**Step 2: Verify no stale imports remain**

Run:

```bash
rg -n "orchestrator_v2\\.(calendar|context|database|validator|hook|writer)" \
  apps/stock_data_platform_v1/orchestrator_v2
```

Expected: only plan/history or deleted-file references remain.

### Task 4: Final verification

**Files:**
- None

**Step 1: Run test suite**

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q \
  apps/stock_data_platform_v1/orchestrator_v2/tests
```

Expected: all tests pass.

**Step 2: Run CLI and script smoke**

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m \
  apps.stock_data_platform_v1.orchestrator_v2.main --help

bash apps/stock_data_platform_v1/orchestrator_v2/scripts/run_daily.sh --help
```

Expected: both commands exit 0 and print help text.
