# Orchestrator V2 Models Merge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the standalone `models.py` from `orchestrator_v2` by merging its dataclasses into `registry.py`.

**Architecture:** `registry.py` becomes the single source of truth for job metadata and registration. `executor.py`, `runtime.py`, and tests import `JobSpec`, `InfrastructureSpec`, and `JobRunResult` from `registry.py`, while runtime and execution behavior remain unchanged.

**Tech Stack:** Python 3.11, dataclasses, pytest

### Task 1: Write the failing import test

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

**Step 1: Change test imports**

Update imports to:

```python
from apps.stock_data_platform_v1.orchestrator_v2.registry import InfrastructureSpec, JobSpec
```

**Step 2: Run the test to verify it fails**

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q \
  apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py
```

Expected: import failure because `registry.py` does not yet export these names.

### Task 2: Move dataclasses into registry.py

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/runtime.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/executor.py`

**Step 1: Add dataclasses to registry.py**

Move `JobSpec`, `InfrastructureSpec`, and `JobRunResult` into `registry.py` near the top of the file.

**Step 2: Update imports**

Change `runtime.py` and `executor.py` to import those names from `registry.py`.

**Step 3: Run tests**

```bash
apps/stock_data_platform_v1/.venv-$(uname -m)/bin/python -m pytest -q \
  apps/stock_data_platform_v1/orchestrator_v2/tests
```

Expected: all tests pass.

### Task 3: Delete models.py and refresh docs

**Files:**
- Delete: `apps/stock_data_platform_v1/orchestrator_v2/models.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`

**Step 1: Remove stale references**

Replace README mentions of `models.py` with `registry.py` as the metadata/type entrypoint.

**Step 2: Verify no stale imports remain**

```bash
rg -n "orchestrator_v2\\.models|models.py" apps/stock_data_platform_v1/orchestrator_v2
```

Expected: no code references remain.

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
