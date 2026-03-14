# Stock BI Modular Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the `stock_bi` backend into a modular monolith while preserving the existing frontend API and MySQL schema semantics.

**Architecture:** Keep a single FastAPI application, but move business logic behind module-local application/query layers and a small infrastructure layer. Use branch-by-abstraction so existing routers keep their routes while delegating to new modules incrementally.

**Tech Stack:** Python 3.9, FastAPI, SQLAlchemy, pytest, unittest, MySQL, httpx

### Task 1: Stabilize Test And Import Baseline

**Files:**
- Modify: `pytest.ini`
- Modify: `scripts/run_tests.sh`
- Test: `apps/stock_data_platform/tests/test_smoke.py`

**Step 1: Write the failing test command**

Run: `./scripts/run_tests.sh`
Expected: Fail during collection because `apps` is not on `PYTHONPATH`.

**Step 2: Add repository-local pytest path configuration**

Update `pytest.ini` so `pytest` resolves repository packages without shell-specific `PYTHONPATH` setup.

**Step 3: Keep test runner deterministic**

Update `scripts/run_tests.sh` to preserve `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and run the same repository-local import path as the direct pytest invocation.

**Step 4: Re-run the baseline**

Run: `./scripts/run_tests.sh`
Expected: Existing test suite passes.

### Task 2: Extract Stable Backend Infrastructure

**Files:**
- Create: `apps/stock_bi/codex/backend/infrastructure/__init__.py`
- Create: `apps/stock_bi/codex/backend/infrastructure/cache.py`
- Create: `apps/stock_bi/codex/backend/infrastructure/database.py`
- Create: `apps/stock_bi/codex/backend/infrastructure/settings.py`
- Modify: `apps/stock_bi/codex/backend/cache.py`
- Modify: `apps/stock_bi/codex/backend/config.py`
- Modify: `apps/stock_bi/codex/backend/database.py`
- Modify: `shared/stock_core/config.py`
- Modify: `shared/stock_core/db.py`
- Test: `apps/stock_bi/codex/tests/test_backend_infrastructure.py`

**Step 1: Write focused behavior tests**

Add tests for pure infrastructure behavior such as:
- shared MySQL URL construction
- stock BI API host/port defaults
- in-memory cache TTL semantics that do not require FastAPI import

**Step 2: Create infrastructure wrappers**

Move stable configuration, cache, and database helpers into `backend/infrastructure/` while keeping the old modules as compatibility shims.

**Step 3: Re-run targeted tests**

Run: `./scripts/run_tests.sh apps/stock_bi/codex/tests/test_backend_infrastructure.py`
Expected: Pass with compatibility imports still working.

### Task 3: Introduce Precompute Read Model Module

**Files:**
- Create: `apps/stock_bi/codex/backend/modules/precompute_read_model/__init__.py`
- Create: `apps/stock_bi/codex/backend/modules/precompute_read_model/repository.py`
- Create: `apps/stock_bi/codex/backend/modules/precompute_read_model/service.py`
- Modify: `apps/stock_bi/codex/backend/precompute.py`
- Test: `apps/stock_bi/codex/tests/test_precompute_service.py`

**Step 1: Write tests for pure helper behavior**

Cover:
- `convert_decimal` recursion
- summary cache key generation
- JSON payload decoding from summary rows

**Step 2: Extract repository and service boundaries**

Move raw SQL execution into a repository object and orchestration into a service module. Keep `precompute.py` exporting the old function names by delegating to the new service.

**Step 3: Re-run tests**

Run: `./scripts/run_tests.sh apps/stock_bi/codex/tests/test_precompute_service.py`
Expected: Pass with old import locations preserved.

### Task 4: Migrate Market Routes Behind Module APIs

**Files:**
- Create: `apps/stock_bi/codex/backend/modules/market_summary/__init__.py`
- Create: `apps/stock_bi/codex/backend/modules/market_summary/application.py`
- Create: `apps/stock_bi/codex/backend/modules/market_summary/api.py`
- Create: `apps/stock_bi/codex/backend/modules/ranking_kline/__init__.py`
- Create: `apps/stock_bi/codex/backend/modules/ranking_kline/application.py`
- Create: `apps/stock_bi/codex/backend/modules/ranking_kline/api.py`
- Modify: `apps/stock_bi/codex/backend/routers/market.py`
- Test: `apps/stock_bi/codex/tests/test_market_helpers.py`

**Step 1: Write tests around extracted helper behavior**

Cover:
- date normalization/formatting
- numeric conversion
- market filter predicates

**Step 2: Extract application functions first**

Create pure functions for summary, overview, ranking, and trend use cases. Keep the existing router functions and have them call the new application layer.

**Step 3: Re-run targeted tests and full suite**

Run: `./scripts/run_tests.sh`
Expected: Pass with route paths and response shapes unchanged.

### Task 5: Migrate Chat And WebSocket To Shared Application Services

**Files:**
- Create: `apps/stock_bi/codex/backend/modules/chat_query/__init__.py`
- Create: `apps/stock_bi/codex/backend/modules/chat_query/application.py`
- Create: `apps/stock_bi/codex/backend/modules/chat_query/llm_service.py`
- Create: `apps/stock_bi/codex/backend/modules/realtime_updates/__init__.py`
- Create: `apps/stock_bi/codex/backend/modules/realtime_updates/service.py`
- Modify: `apps/stock_bi/codex/backend/routers/chat.py`
- Modify: `apps/stock_bi/codex/backend/routers/websocket.py`
- Modify: `apps/stock_bi/codex/backend/services/llm.py`
- Test: `apps/stock_bi/codex/tests/test_chat_rules.py`

**Step 1: Write tests for rule-based parsing**

Cover:
- overview intent
- ranking intent with market extraction
- fallback response shape

**Step 2: Move behavior behind new modules**

Keep prompt text and API behavior unchanged, but route chat/websocket logic through dedicated module services instead of direct SQL helpers scattered in routers.

**Step 3: Re-run the suite**

Run: `./scripts/run_tests.sh`
Expected: Pass without route or schema changes.

### Task 6: Cleanup And Diff Review

**Files:**
- Modify: `apps/stock_bi/codex/backend/main.py`
- Modify: `apps/stock_bi/codex/backend/routers/__init__.py`
- Verify: `docs/plans/2026-03-14-stock-bi-modular-refactor-implementation.md`

**Step 1: Thin composition root**

Ensure `main.py` only wires routers and startup tasks, with module imports coming from the new structure.

**Step 2: Remove dead compatibility code where safe**

Keep only the shims still needed by unchanged imports. Do not remove public import paths still referenced elsewhere in the repository.

**Step 3: Final verification**

Run:
- `./scripts/run_tests.sh`
- `git diff --stat`

Expected: Tests pass and the diff is limited to the planned refactor scope.
