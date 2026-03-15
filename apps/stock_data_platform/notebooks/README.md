# stock_data_platform notebooks

These notebooks are for exploration only.

They are intentionally outside the production write path:

- use notebooks to inspect existing tables
- use notebooks to probe a candidate upstream data source
- do not treat notebook cells as the maintained way to write production tables

## Files

- `01_job_catalog.ipynb`
  - shows the current configured jobs, target tables, and BI sync flags
- `02_existing_table_preview.ipynb`
  - previews current MySQL tables with the shared runtime DB config
- `10_new_source_probe.ipynb`
  - template for probing a candidate new source and generating a job YAML snippet
- `../templates/new_data_source/`
  - skeleton files for promoting a notebook probe into maintained runtime code
- `notebook_support.py`
  - helper functions reused by the notebooks
- `jupyter_runtime.py`
  - installs the project kernel and launches JupyterLab through the architecture-aware Python dispatcher

## Startup

- preferred:
  - `bash apps/stock_data_platform/scripts/run_jupyterlab.sh`
- this launcher installs both:
  - the dedicated kernel `stock-data-platform`
  - the default `Python 3` kernel pointing at `dispatch_stock_data_python.sh`
- the dispatcher then chooses:
  - `.venv-stock-data-arm64` for `arm64`
  - `.venv-stock-data-x86_64` for `x86_64`
- `.venv-stock-data` is kept as a convenience symlink and prefers `arm64`, so editor-integrated notebook tools resolve to the native GUI architecture by default
- after that, opening these notebooks should run directly without manual kernel switching
- if an old notebook tab was already open before this fix, shut down that kernel once and reopen the notebook

## Minimal path for a new data source

1. Explore the upstream source in `10_new_source_probe.ipynb`.
2. Confirm the data grain, unique key, refresh cadence, and whether BI needs it.
3. Add one new fetcher in `apps/stock_data_platform/DataFetch/`.
4. Export that fetcher from `apps/stock_data_platform/DataFetch/__init__.py`.
5. Add one new job in `apps/stock_data_platform/jobs/daily_jobs.yaml`.
6. Add tests.
7. Let the scheduled runner pick it up.

## Boundary

Notebook code can read the database and prototype fetch logic.
Formal data ingestion still belongs in:

- `DataFetch/`
- `jobs/daily_jobs.yaml`
- `jobs/daily_runner.py`
