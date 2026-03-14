# Monorepo Reorganization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize the repository into a clearer monorepo with two maintained applications while fixing the most urgent configuration, entrypoint, and documentation issues.

**Architecture:** Keep `DataStore/` at the root, move maintained apps into `apps/`, classify side content into `experiments/` and `assets/`, and stabilize shared infrastructure before deeper code extraction. The first execution pass focuses on safe structural changes and source correctness, not a full packaging rewrite.

**Tech Stack:** Python, Git worktrees, pytest, shell utilities, TuShare, FastAPI/static frontend code in `Stock_BI`

### Task 1: Baseline Verification

**Files:**
- Inspect: `README.md`
- Inspect: `main.py`
- Inspect: `Stock_BI/codex/tests/`

**Step 1: Run the existing tests**

Run: `pytest -q`
Expected: Either passing tests or a list of pre-existing failures to record before migration.

**Step 2: Run a Python import smoke check**

Run: `python - <<'PY'\nimport DataFetch\nprint('ok')\nPY`
Expected: Either successful import or a concrete import error to fix in the first pass.

### Task 2: Harden Configuration

**Files:**
- Modify: `common/config.py`
- Create: `.env.example`
- Modify: `README.md`

**Step 1: Replace hard-coded secrets with environment lookups**

Implement config loading that reads TuShare, mail, and MySQL settings from environment variables with safe defaults only where appropriate.

**Step 2: Document local configuration**

Add `.env.example` describing required variables without real secrets.

**Step 3: Update docs**

Document the new configuration workflow in the root README.

### Task 3: Fix Root Entrypoints And Imports

**Files:**
- Modify: `main.py`
- Modify: `demo_test.py`
- Modify: `README.md`

**Step 1: Replace broken imports**

Update root scripts to use the current `DataFetch` package instead of removed modules.

**Step 2: Make sample scripts safe**

Ensure root scripts are examples that do not accidentally rely on committed tokens.

### Task 4: Create Monorepo Directory Boundaries

**Files:**
- Create: `apps/.gitkeep`
- Create: `experiments/.gitkeep`
- Create: `assets/.gitkeep`
- Move: `Stock_BI -> apps/stock_bi`
- Move: maintained root stock code into `apps/stock_data_platform` in a later pass

**Step 1: Scaffold the target directories**

Create top-level directories that represent the final monorepo layout.

**Step 2: Move the long-term BI app**

Move `Stock_BI/` into `apps/stock_bi/` and repair any obvious path references.

**Step 3: Prepare the stock data app boundary**

Do not perform the full root-to-app move yet if it would cause broad import churn. Instead, document and scaffold the target.

### Task 5: Classify Experiments And Assets

**Files:**
- Move: `Backtrader/`, `Research/`, `CodeX/`, `cursor/` into `experiments/`
- Move: loose images and PDFs into `assets/`
- Modify: `README.md`

**Step 1: Move obvious experiments**

Relocate directories that are clearly prototypes or learning material.

**Step 2: Move obvious assets**

Relocate screenshots, PDFs, and generated output files that do not belong at the root.

**Step 3: Update references**

Refresh docs so users can still find these materials after the move.

### Task 6: Clean Up Shared Utilities

**Files:**
- Modify: `common/utils.py`
- Create: `common/db.py` or `shared/stock_core/...` in a later pass

**Step 1: Fix missing imports and hidden runtime errors**

Add or remove imports so utility functions are internally consistent.

**Step 2: Narrow responsibilities**

Remove the worst cross-domain coupling where possible without forcing a full package split in this pass.

### Task 7: Verification

**Files:**
- Verify: `README.md`
- Verify: `main.py`
- Verify: `apps/stock_bi`

**Step 1: Re-run tests**

Run: `pytest -q`
Expected: No new failures introduced by the reorganization pass.

**Step 2: Re-run import smoke checks**

Run import checks for the maintained Python modules.

**Step 3: Review git diff**

Confirm the changes are scoped to the agreed first-pass reorganization.
