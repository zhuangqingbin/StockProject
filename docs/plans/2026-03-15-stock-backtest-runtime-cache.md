# Stock Backtest Runtime Cache Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add high-value backend runtime improvements to `apps/stock_backtest`: cache identical completed runs, expose execution diagnostics, and publish a runtime summary API.

**Architecture:** Keep the current FastAPI plus SQLAlchemy shape, but enrich `BacktestRunModel` with deterministic request signatures, cache metadata, and diagnostic events. On submit, compute a stable signature from the strategy definition plus run request; if a completed run already exists, create a lightweight cache-hit run that points at the original result. Diagnostics remain on the run record as JSON events, while analysis repositories transparently resolve reused runs back to the source run for daily/trade queries.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Backtrader, Python stdlib hashing/JSON.

### Task 1: Add Failing API Tests

**Files:**
- Modify: `apps/stock_backtest/tests/test_api_flows.py`

**Step 1: Write the failing test**
- Extend the API flow test to submit the same completed backtest twice.
- Assert that the second submit returns a cache-hit signal and a different run id linked back to the original completed run.
- Assert that diagnostics and runtime summary endpoints exist and return meaningful payloads.

**Step 2: Run test to verify it fails**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_api_flows.py -q`

**Step 3: Write minimal implementation**
- Only add the fields/endpoints needed to satisfy the test contract.

**Step 4: Run test to verify it passes**
- Re-run the same command and confirm green.

### Task 2: Persist Cache and Diagnostic Metadata

**Files:**
- Modify: `apps/stock_backtest/backend/models/db_models.py`
- Modify: `apps/stock_backtest/backend/models/api_models.py`
- Modify: `apps/stock_backtest/backend/modules/backtest/repository.py`
- Modify: `apps/stock_backtest/backend/modules/analysis/repository.py`
- Modify: `apps/stock_backtest/backend/engine/runner.py`

**Step 1: Write the failing test**
- Covered by Task 1.

**Step 2: Run test to verify it fails**
- Covered by Task 1.

**Step 3: Write minimal implementation**
- Add `request_signature`, `cache_hit`, `reused_from_run_id`, `started_at`, and `diagnostics` fields to runs.
- Record lifecycle events during execution (`submitted`, `running`, `data_loaded`, `completed`, `failed`, `cache_hit`).
- Resolve analysis reads through `reused_from_run_id` when present.

**Step 4: Run test to verify it passes**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_api_flows.py -q`

### Task 3: Add Runtime Summary and Diagnostics APIs

**Files:**
- Modify: `apps/stock_backtest/backend/modules/backtest/service.py`
- Modify: `apps/stock_backtest/backend/modules/backtest/router.py`
- Modify: `apps/stock_backtest/backend/modules/backtest/websocket.py`

**Step 1: Write the failing test**
- Covered by Task 1.

**Step 2: Run test to verify it fails**
- Covered by Task 1.

**Step 3: Write minimal implementation**
- Expose `GET /api/backtest/runtime` with execution mode, worker limit, inflight run ids, and DB status counters.
- Expose `GET /api/backtest/runs/{run_id}/diagnostics` returning the run’s diagnostic event list and cache metadata.
- Keep websocket broadcast payloads compatible, only enriching them if needed.

**Step 4: Run test to verify it passes**
- Run: `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests/test_api_flows.py -q`

### Task 4: Full Verification

**Files:**
- Update: `task_plan.md`
- Update: `findings.md`
- Update: `progress.md`

**Step 1: Run verification**
- `./.venv-stock-backtest-x86_64/bin/python -m pytest apps/stock_backtest/tests -q`
- `cd apps/stock_backtest/frontend && npm test`
- `cd apps/stock_backtest/frontend && npm run build`

**Step 2: Record results**
- Note the new API capabilities and any frontend build impact in the planning files.
