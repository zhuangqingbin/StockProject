# Python 3.11 Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the maintained repository runtime from the current `python3`/3.9 bootstrap assumptions to an explicit Python 3.11+ baseline and align dependency manifests and docs with that baseline.

**Architecture:** Introduce one shared interpreter-resolution helper in `shared/stock_core/` that is safe to import from a bootstrap Python and returns a validated 3.11+ interpreter path. Point shell launchers, venv bootstraps, and runtime tests at that helper so the whole repo consistently prefers `python3.11` instead of the macOS CLT `python3`.

**Tech Stack:** Python 3.11, stdlib `subprocess`/`shutil`, pytest, FastAPI, SQLAlchemy, pandas, numpy, Jupyter

### Task 1: Lock the new interpreter selection behavior with tests

**Files:**
- Create: `shared/stock_core/python_runtime.py`
- Create: `apps/stock_data_platform/tests/test_python_runtime.py`
- Modify: `apps/stock_data_platform/tests/test_venv_runtime.py`
- Modify: `apps/stock_backtest/tests/test_venv_runtime.py`

**Step 1: Write the failing tests**

- Add tests for a shared helper that:
  - prefers `python3.11` when available
  - rejects interpreters below 3.11
  - honors an explicit override only when the override is executable and version-compatible
- Update the existing venv-runtime tests so they no longer assume `/Library/Developer/CommandLineTools/usr/bin/python3` is the desired system runtime.

**Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest -q apps/stock_data_platform/tests/test_python_runtime.py apps/stock_data_platform/tests/test_venv_runtime.py apps/stock_backtest/tests/test_venv_runtime.py
```

Expected:
- FAIL because the shared runtime helper does not exist yet
- FAIL because the current tests still encode the legacy CLT bootstrap path

**Step 3: Write the minimal implementation**

- Implement the shared resolver with stdlib-only logic.
- Update tests to target the new helper behavior.

**Step 4: Re-run the focused tests**

Run the same `python3 -m pytest ...` command and expect PASS.

### Task 2: Switch maintained shell entrypoints to Python 3.11 resolution

**Files:**
- Modify: `apps/stock_bi/codex/run.sh`
- Modify: `apps/stock_bi_v1/run.sh`
- Modify: `apps/stock_backtest/run.sh`
- Modify: `apps/stock_data_platform/scripts/setup_stock_data_daily_env.sh`
- Modify: `apps/stock_data_platform/scripts/dispatch_stock_data_python.sh`
- Modify: `apps/stock_data_platform/scripts/run_jupyterlab.sh`
- Modify: `apps/stock_data_platform/scripts/run_tests.sh`
- Modify: `apps/stock_data_platform/scripts/install_stock_data_daily_schedule.sh`
- Modify: `apps/stock_data_platform/scripts/uninstall_stock_data_daily_schedule.sh`

**Step 1: Replace `python3` and hardcoded CLT Python defaults**

- Use a bootstrap snippet that imports `shared.stock_core.python_runtime`.
- Resolve the preferred 3.11+ interpreter once per script.
- Preserve environment-variable overrides, but validate them through the shared resolver.

**Step 2: Keep existing app behavior unchanged**

- `stock_bi` still executes `run.py`
- `stock_bi_v1` still launches `apps.stock_bi_v1.run`
- `stock_backtest` still builds the correct arch-specific venv and launches uvicorn
- `stock_data_platform` still dispatches per-arch venvs and launchd jobs

### Task 3: Align dependency manifests and project metadata with Python 3.11

**Files:**
- Modify: `pyproject.toml`
- Create: `.python-version`
- Modify: `apps/stock_bi/codex/requirements.txt`
- Modify: `apps/stock_bi_v1/requirements.txt`
- Modify: `apps/stock_data_platform/requirements.txt`
- Modify: `apps/stock_backtest/requirements.txt`

**Step 1: Declare the baseline**

- Add repository-level metadata that states Python 3.11 is the minimum supported version.
- Add a `.python-version` file for local tooling.

**Step 2: Refresh runtime dependency floors where needed**

- Raise dependency lower bounds or pins only where the manifest is still effectively anchored to older 3.9-era baselines.
- Avoid speculative major-version jumps that are not needed for 3.11 compatibility.

### Task 4: Update docs and verification instructions

**Files:**
- Modify: `README.md`
- Modify: `apps/stock_bi/README.md`
- Modify: `apps/stock_data_platform/README.md`

**Step 1: Replace user-facing `python3` guidance**

- Update commands and prose to say Python 3.11+ explicitly.
- Point users toward the maintained scripts where that is the safer path.

### Task 5: Verify the upgrade

**Files:**
- No code changes expected

**Step 1: Run targeted Python tests**

Run:

```bash
python3 -m pytest -q apps/stock_data_platform/tests/test_python_runtime.py apps/stock_data_platform/tests/test_venv_runtime.py apps/stock_backtest/tests/test_venv_runtime.py apps/stock_bi/codex/tests/test_runtime_env.py apps/stock_bi/codex/tests/test_launch_env.py
```

Expected: PASS

**Step 2: Run the maintained repo test entrypoint**

Run:

```bash
bash apps/stock_data_platform/scripts/run_tests.sh apps/stock_data_platform/tests/test_python_runtime.py
```

Expected: PASS under a resolved Python 3.11+ interpreter

**Step 3: Sanity-check script resolution**

Run:

```bash
bash apps/stock_data_platform/scripts/dispatch_stock_data_python.sh --print-python
```

Expected: an executable Python 3.11+ path

**Step 4: Review the diff**

Run:

```bash
git diff -- shared/stock_core apps/stock_bi/codex apps/stock_bi_v1 apps/stock_backtest apps/stock_data_platform README.md pyproject.toml .python-version docs/plans/2026-03-15-python-311-upgrade.md
```

Expected: only Python runtime/dependency/docs upgrade changes
