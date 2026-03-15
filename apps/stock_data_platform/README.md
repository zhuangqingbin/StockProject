# stock_data_platform

Minimal upstream writer app for this repository.

## What Lives Here

- `DataFetch/`
  - maintained TuShare fetchers used by the demo entrypoint and daily jobs
- `common/`
  - small runtime helpers for database access, trade calendar lookup, and timing
- `jobs/`
  - config-driven daily runner and BI sync integration
- `scripts/`
  - shell entrypoints for tests and daily-job execution
- `notebooks/`
  - exploratory Jupyter notebooks for reading current data and probing a candidate new source
- `templates/`
  - skeleton files for adding one new maintained data source with minimal edits
- `.cache/`
  - app-local transient cache directory for TuShare responses
- `tests/`
  - maintained automated tests for this app

## Main Entry Points

- Demo entrypoint:
  - `python3 apps/stock_data_platform/main.py`
- Test runner:
  - `./apps/stock_data_platform/scripts/run_tests.sh`
- Daily job runner:
  - `bash apps/stock_data_platform/scripts/run_stock_data_daily.sh`
- Daily schedule installer:
  - `bash apps/stock_data_platform/scripts/install_stock_data_daily_schedule.sh --hour 18 --minute 30`
  - if `STOCK_DATA_DAILY_SCHEDULE_HOUR` and `STOCK_DATA_DAILY_SCHEDULE_MINUTE` are set in `.env`, the installer can run without flags
- Notebook index:
  - `apps/stock_data_platform/notebooks/README.md`
- JupyterLab launcher:
  - `bash apps/stock_data_platform/scripts/run_jupyterlab.sh`
- Python dispatcher:
  - `apps/stock_data_platform/scripts/dispatch_stock_data_python.sh`

## Daily Jobs

- Job config file:
  - `apps/stock_data_platform/jobs/daily_jobs.yaml`
- Runtime module:
  - `apps/stock_data_platform/jobs/runtime.py`
- CLI entry:
  - `apps/stock_data_platform/jobs/daily_runner.py`
- Default retry behavior:
  - `run_stock_data_daily.sh` first runs all selected jobs once
  - any failed job is retried on its own after 600 seconds
  - retries continue until every selected job succeeds
  - `stock_bi` sync only runs after the full selected job set succeeds
  - `stock_bi_v1` precompute only runs after the full configured daily job set succeeds; partial `--jobs` runs do not trigger it
- Useful CLI flags:
  - `--as-of <YYYY-MM-DD>`
    resolves the latest trade date on or before the given calendar date
  - `--jobs <job1,job2,...>`
    when omitted, all configured jobs in `daily_jobs.yaml` run
  - `--retry-delay-sec <seconds>`
  - `--max-retry-rounds <count>`
    `0` means unlimited retry rounds
- Run all configured tables for a specific trade date:
  - `bash apps/stock_data_platform/scripts/run_stock_data_daily.sh --as-of 2026-03-13`
- `--as-of` uses calendar-date resolution:
  - `bash apps/stock_data_platform/scripts/run_stock_data_daily.sh --as-of 2026-03-14`
  - if `2026-03-14` is not a trade date, jobs write `trade_date=20260313`
- Backfill all configured tables without triggering `stock_bi` sync:
  - `STOCK_BI_SYNC_ENABLED=0 bash apps/stock_data_platform/scripts/run_stock_data_daily.sh --as-of 2026-03-13`
- Backfill all configured tables without triggering `stock_bi_v1` precompute:
  - `STOCK_BI_V1_PRECOMPUTE_ENABLED=0 bash apps/stock_data_platform/scripts/run_stock_data_daily.sh --as-of 2026-03-13`
- V1 precompute defaults:
  - target URL base: `http://127.0.0.1:8100/api/precompute`
  - env overrides: `STOCK_BI_V1_PRECOMPUTE_URL`, `STOCK_BI_V1_PRECOMPUTE_TIMEOUT_SEC`, `STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT`

## Notebook Workflow

- notebooks are for exploration, not the maintained production write path
- always start Jupyter with `bash apps/stock_data_platform/scripts/run_jupyterlab.sh`
- the launcher rewires the default `Python 3` kernel to `dispatch_stock_data_python.sh`
- kernel startup then picks the matching managed venv for the current CPU architecture automatically
- managed venv directories are:
  - `.venv-stock-data-arm64`
  - `.venv-stock-data-x86_64`
- `.venv-stock-data` is a convenience symlink that prefers `arm64` when available, so GUI notebook tools resolve to the native Apple Silicon environment by default
- if a notebook tab was already open before the kernel fix, shut down that old kernel once and reopen the notebook
- inspect current configured jobs in `notebooks/01_job_catalog.ipynb`
- preview existing tables in `notebooks/02_existing_table_preview.ipynb`
- probe a new source and generate a job snippet in `notebooks/10_new_source_probe.ipynb`
- once the source is validated, move the real implementation into:
  - `DataFetch/`
  - `jobs/daily_jobs.yaml`
  - tests

## Daily Scheduling

- Recommended on macOS:
  - `launchd`
- Install a daily schedule:
  - `bash apps/stock_data_platform/scripts/install_stock_data_daily_schedule.sh --hour 18 --minute 30`
  - or set `STOCK_DATA_DAILY_SCHEDULE_HOUR` / `STOCK_DATA_DAILY_SCHEDULE_MINUTE` in `.env` and run:
    `bash apps/stock_data_platform/scripts/install_stock_data_daily_schedule.sh`
- Remove the schedule:
  - `bash apps/stock_data_platform/scripts/uninstall_stock_data_daily_schedule.sh`
- Generated launch agent:
  - `~/Library/LaunchAgents/com.stockproject.stock-data-daily.plist`
- Runtime logs:
  - `apps/stock_data_platform/.logs/stock_data_daily.launchd.out.log`
  - `apps/stock_data_platform/.logs/stock_data_daily.launchd.err.log`
- Schedule env vars:
  - `STOCK_DATA_DAILY_SCHEDULE_HOUR`
  - `STOCK_DATA_DAILY_SCHEDULE_MINUTE`

## Current Runtime Scope

The maintained runtime only keeps fetchers and helpers required by:

- `main.py`
- `common/market_calendar.py`
- `jobs/daily_jobs.yaml`

Everything else from the old stock project has been removed from this app boundary.

## Architecture Compatibility

- `setup_stock_data_daily_env.sh` builds separate managed environments for `arm64` and `x86_64` when both are available
- `run_stock_data_daily.sh` and Jupyter kernels both dispatch to the matching environment automatically
- this avoids mixing `x86_64` wheels into an `arm64` kernel process or the reverse
