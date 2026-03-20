# Python 3.11 Default And Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Python 3.11 the default runtime for this repo and the user's shell, then remove removable Python 3.9-era user-level artifacts without touching protected macOS system Python.

**Architecture:** Keep the repo pinned to Homebrew `python@3.11`, expose unversioned `python`/`python3`/`pip`/`pip3` through `$HOME/.local/bin`, and clean stale shell PATH entries that currently point to missing Conda and Python 3.12 locations. Remove user-owned `~/Library/Python/3.9` artifacts after redirecting all default entrypoints to 3.11 and verifying the repo runtime guards still pass.

**Tech Stack:** Homebrew Python 3.11, zsh/bash shell init files, repo launcher scripts, pytest

### Task 1: Record the cleanup boundaries

**Files:**
- Create: `docs/plans/2026-03-15-python-default-and-cleanup.md`

**Step 1: Write down the safe boundary**

Document that `/usr/bin/python3` is macOS-managed and will not be deleted, only shadowed by user PATH.

**Step 2: Write down the removable targets**

Document that `~/Library/Python/3.9` and stale shell PATH entries are user-owned and safe to remove/update after verification.

### Task 2: Add a repo-side regression for Python resolution

**Files:**
- Modify: `apps/stock_data_platform/tests/test_python_runtime.py`

**Step 1: Write the failing test**

Add a test that simulates PATH preferring `$HOME/.local/bin/python3` and verifies the resolver still lands on a supported 3.11+ interpreter.

**Step 2: Run the test to verify RED**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /usr/local/bin/python3.11 -m pytest -q apps/stock_data_platform/tests/test_python_runtime.py`

Expected: FAIL before resolver/path logic supports the shell-default layout.

### Task 3: Update shell defaults to 3.11

**Files:**
- Modify: `/Users/qingbin.zhuang/.zshrc`
- Modify: `/Users/qingbin.zhuang/.zprofile`
- Modify: `/Users/qingbin.zhuang/.bash_profile`

**Step 1: Remove stale PATH entries**

Delete references to missing `~/opt/anaconda3` and missing `/Library/Frameworks/Python.framework/Versions/3.12/bin` where they are only legacy leftovers.

**Step 2: Add explicit 3.11 shims**

Ensure `$HOME/.local/bin` exposes `python`, `python3`, `pip`, and `pip3` backed by Homebrew `python@3.11`.

**Step 3: Verify interactive shell resolution**

Run: `zsh -lic 'command -v python python3 pip pip3 && python --version && python3 --version && pip --version && pip3 --version'`

Expected: all entrypoints resolve to 3.11-backed shims or Homebrew binaries.

### Task 4: Remove removable Python 3.9 user artifacts

**Files:**
- Delete runtime artifact: `/Users/qingbin.zhuang/Library/Python/3.9`

**Step 1: Verify 3.9 user PATH is no longer referenced**

Run: `rg -n 'Library/Python/3.9|anaconda3|Versions/3.12/bin' ~/.zshrc ~/.zprofile ~/.bash_profile ~/.profile`

Expected: no active shell init path keeps the old Python 3.9 or missing Conda/3.12 locations first in PATH.

**Step 2: Remove the user-level 3.9 tree**

Delete `~/Library/Python/3.9` after the default shell commands are already on 3.11.

### Task 5: Final verification

**Files:**
- Test: `apps/stock_data_platform/tests/test_python_runtime.py`
- Test: `apps/stock_data_platform/tests/test_venv_runtime.py`
- Test: `apps/stock_backtest/tests/test_venv_runtime.py`
- Test: `apps/stock_bi/codex/tests/test_runtime_env.py`
- Test: `apps/stock_bi/codex/tests/test_launch_env.py`

**Step 1: Run fresh repo verification**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /usr/local/bin/python3.11 -m pytest -q apps/stock_bi/codex/tests/test_runtime_env.py apps/stock_bi/codex/tests/test_launch_env.py apps/stock_data_platform/tests/test_python_runtime.py apps/stock_data_platform/tests/test_venv_runtime.py apps/stock_backtest/tests/test_venv_runtime.py`

Expected: PASS.

**Step 2: Run fresh shell verification**

Run: `zsh -lic 'command -v python python3 pip pip3 && python --version && python3 --version'`

Expected: default shell Python entrypoints report 3.11.
