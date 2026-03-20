# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python monorepo for Chinese A-share market tooling. The active code lives under `apps/data_hub/`, sharing `shared/stock_core/` for environment resolution, database access, and Python runtime discovery.

**Python baseline**: 3.11+
**Database**: MySQL (shared server, multiple schemas)

## Apps

| App | Purpose | Port | Entry Point |
|-----|---------|------|-------------|
| `data_hub/data_pipeline_ts` | TuShare data ingestion, daily jobs, backfill, infrastructure sync | N/A | `bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh` |
| `data_hub/data_pipeline_ak` | AkShare-side helpers and imports | N/A | — |
| `data_hub/data_explorer` | Read-only schema explorer and monitoring UI (FastAPI + React) | 8201 | `./apps/data_hub/data_explorer/scripts/run.sh backend` |

## Build & Test Commands

```bash
# Run all tests
python -m pytest -q

# Run tests for a specific app area
pytest apps/data_hub/tests
pytest apps/data_hub/data_pipeline_ts/tests
pytest apps/data_hub/data_pipeline_ak/tests
pytest apps/data_hub/data_explorer/tests

# Daily jobs (with optional date/job filters)
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --as-of 2026-03-13 --profiles trade_day_post_close_core

# Frontend dev
cd apps/data_hub/data_explorer/frontend && npm run dev
```

## Architecture

### Shared Apps Virtualenv
`apps/` uses a shared virtualenv at `apps/.venv`. Prefer `bash apps/setup.sh` plus the app launch scripts over mixing user-level Python packages into the runtime.

### Shared Infrastructure (`shared/stock_core/`)
- `config.py` — env var access helpers (`get_env`, `get_int`, `get_csv`)
- `env.py` — `.env` / `.env.local` file discovery (supports git worktrees)
- `db.py` — `build_mysql_url()`, `create_mysql_engine()` for MySQL connections
- `python_runtime.py` — Python 3.11+ resolution logic

### Data Pipeline (`data_hub/data_pipeline_ts`)
TuShare-based ingestion: 39 job fetchers across 7 profiles (pre-open, post-close core/extended, nightly, manual), plus 3 infrastructure targets (stock_basic, stock_company, trade_cal). Supports `once`, `backfill`, and `infrastructure` execution modes.

### Data Explorer (`data_hub/data_explorer`)
Read-only FastAPI + React app for browsing table catalogs, previewing data, and monitoring job/table health. Frontend uses Ant Design + TanStack Query + Zustand.

### Frontend Pattern
Current frontends use React + Vite + TypeScript. Built assets live in each app-local `frontend/` directory.

## Environment Configuration

Copy `env.example` to `.env` (or `.env.local` for overrides). Key variables are `TUSHARE_TOKEN`, `MYSQL_*`, `TS_MYSQL_DATABASE`, and `AK_MYSQL_DATABASE`. Resolution order: `.env.local` > `.env` > shell environment. There are no code defaults for database selection.

## Pytest Configuration

Defined in `pyproject.toml`: uses `--import-mode=importlib`, `pythonpath=["."]`, and discovers `test_*.py` files in `apps/data_hub/tests`, `apps/data_hub/data_pipeline_ts/tests`, `apps/data_hub/data_pipeline_ak/tests`, and `apps/data_hub/data_explorer/tests`.
