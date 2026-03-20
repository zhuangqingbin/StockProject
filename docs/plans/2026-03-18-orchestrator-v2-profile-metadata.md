# Orchestrator V2 Profile Metadata Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Centralize orchestrator profile behavior in Python metadata so cron scheduling, execution mode, and backfill mode are defined once and reused by runtime and launchd installation.

**Architecture:** Keep job-to-profile assignment inside `registry.py`, but replace raw profile strings with a typed `ProfileId` enum plus `ProfileSpec` metadata. Generate reverse lookup and scheduled-profile data from that single source so `executor.py` and `install_launchd.sh` stop hardcoding profile behavior.

**Tech Stack:** Python 3.11, dataclasses, `StrEnum`, pytest, bash launchd installer

### Task 1: Lock expected profile metadata behavior with tests

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py`

**Step 1: Write the failing test**

Add assertions that:
- registry exposes typed profile metadata
- scheduled profiles carry cron strings
- jobs reference `ProfileId` instead of raw strings
- launchd installation script no longer hardcodes profile/time pairs

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py`

Expected: FAIL because profile metadata and launchd indirection do not exist yet.

### Task 2: Add typed profile metadata in registry

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/registry.py`

**Step 1: Write minimal implementation**

Add:
- `ProfileId(StrEnum)`
- `ProfileSpec`
- `PROFILE_SPECS`
- `SCHEDULED_PROFILES`
- helper(s) to build reverse job lookup by profile

Update `JobSpec.profile` to use `ProfileId`, and update all `_job(...)` calls to reference enum members.

**Step 2: Run tests to verify they pass**

Run: `python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py`

Expected: Remaining failures should move to executor or script integration gaps.

### Task 3: Move runtime behavior to profile metadata

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/executor.py`

**Step 1: Write minimal implementation**

Replace raw string checks with profile metadata lookups:
- serial execution uses `execution_mode`
- backfill filtering uses `backfill_mode`

**Step 2: Run tests to verify they pass**

Run: `python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py`

Expected: PASS.

### Task 4: Make launchd installation consume cron metadata

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/scripts/install_launchd.sh`
- Optionally create: `apps/stock_data_platform_v1/orchestrator_v2/schedules.py`

**Step 1: Write minimal implementation**

Stop hardcoding `install_plan ... hour minute profile`. Read scheduled profiles from Python metadata, parse cron, and emit launchd jobs from that source.

**Step 2: Run tests to verify they pass**

Run: `python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py`

Expected: PASS.

### Task 5: Update docs and run focused verification

**Files:**
- Modify: `apps/stock_data_platform_v1/orchestrator_v2/README.md`

**Step 1: Update docs**

Describe:
- `ProfileId`
- `cron`
- `execution_mode`
- `backfill_mode`
- launchd reading profile schedule metadata from Python

**Step 2: Run verification**

Run: `python -m pytest -q apps/stock_data_platform_v1/orchestrator_v2/tests/test_executor.py apps/stock_data_platform_v1/orchestrator_v2/tests/test_scripts.py apps/stock_data_platform_v1/tests/test_context.py apps/stock_data_platform_v1/tests/test_writer.py`

Expected: PASS.
