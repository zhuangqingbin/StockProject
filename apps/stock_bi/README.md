# stock_bi

Minimal BI application boundary for this repository.

## What Lives Here

- `codex/backend/`
  - FastAPI application, infrastructure layer, routers, and read-model modules
- `codex/frontend/`
  - React + Vite frontend source and built assets
- `codex/tests/`
  - maintained automated tests for backend and frontend behavior
- `codex/run.py`
  - Python runtime entrypoint
- `codex/run.sh`
  - shell launch entrypoint
- `codex/launch_env.py`
  - local runtime bootstrap and architecture-safe environment handling

## Main Entry Points

- App launch:
  - `cd apps/stock_bi/codex && ./run.sh`
- Frontend install:
  - `npm --prefix apps/stock_bi/codex/frontend install`
- Frontend build:
  - `npm --prefix apps/stock_bi/codex/frontend run build`
- Direct Python launch:
  - `python3 apps/stock_bi/codex/run.py`
- Test runner:
  - `./apps/stock_data_platform/scripts/run_tests.sh apps/stock_bi/codex/tests`

## Current Runtime Scope

The maintained runtime keeps only:

- `backend/` for API, realtime updates, and read-model logic
- `frontend/` for the React UI source and shipped build output
- runtime bootstrap files needed for `x86_64` and `arm64`

Legacy compatibility shims and standalone helper documents are intentionally removed from this app boundary.

## Frontend Runtime

- FastAPI serves `codex/frontend/dist/index.html` once the Vite build is present.
- Built frontend assets are exposed from `codex/frontend/dist/assets/`.
- Legacy imperative frontend assets are removed; the maintained UI now lives entirely in `codex/frontend/src/`.
