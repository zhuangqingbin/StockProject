# StockProject

This repository is a monorepo with two independent projects:

- `apps/data_hub`: A-share data ingestion, persistence, scheduling, read-only exploration, and monitoring
- `apps/quant_platform`: Quant research, backtesting, visualization, and application APIs

They are related through data usage, not through shared application ownership:

- data_hub produces and manages market datasets
- quant_platform consumes some of those datasets for research and product workflows

The repository also contains `shared/stock_core`, a minimal shared infrastructure layer for env loading, DB helpers, and Python runtime resolution.

## Repository Layout

```text
.
|-- apps/
|   |-- data_hub/
|   `-- quant_platform/
|-- shared/
|   `-- stock_core/
|-- docs/
|-- experiments/
|-- env.example
|-- .gitignore
|-- pyproject.toml
`-- README.md
```

## Project Entry Points

### `apps/data_hub`

- Scope: data ingestion, persistence, scheduling, exploration, monitoring
- Docs: `apps/data_hub/README.md`
- Example commands:
  - `bash apps/data_hub/setup.sh`
  - `bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help`
  - `./apps/data_hub/data_explorer/scripts/run.sh backend`
  - `python -m pytest -q apps/data_hub/tests apps/data_hub/data_explorer/tests apps/data_hub/data_pipeline_ts/tests apps/data_hub/data_pipeline_ak/tests`

### `apps/quant_platform`

- Scope: quant visualization, strategy workflows, research tooling, application APIs
- Docs: `apps/quant_platform/README.md`
- Example commands:
  - `bash apps/quant_platform/scripts/run.sh backend`
  - `bash apps/quant_platform/scripts/run.sh frontend`
  - `bash apps/quant_platform/scripts/run.sh init`
  - `python -m pytest -q apps/quant_platform/tests`

## Shared Infrastructure

- `shared/stock_core`: env loading, DB URL construction, Python runtime helpers
- `docs/`: repo-level governance and cross-project plans
- `experiments/`: exploratory, non-canonical work

## Configuration Overview

Common infrastructure variables:

- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_CHARSET`

`data_hub` variables:

- `TUSHARE_TOKEN`
- `TS_MYSQL_DATABASE`
- `AK_MYSQL_DATABASE`

`quant_platform` variables:

- `QV_MYSQL_DATABASE`
- `QV_API_PORT` (optional; default defined in `apps/quant_platform/README.md`)
- `QV_API_HOST` (optional; default defined in `apps/quant_platform/README.md`)
- `QV_DEBUG` (optional; default defined in `apps/quant_platform/README.md`)

See the project READMEs for project-specific setup details.

## Quick Start

Python baseline: `3.11+`

Resolve the project Python:

```bash
./shared/scripts/resolve_project_python.sh
```

Create the shared `apps/.venv` and install dependencies:

```bash
bash apps/setup.sh
```

For project-specific workflows, use the project READMEs:

- `apps/data_hub/README.md`
- `apps/quant_platform/README.md`

## Docs Portal

This repository includes a MkDocs portal with repo-level entrypoints for `Data Hub`, `Analysis`, `Quant Platform`, and `Ops / Dev`.

The source pages live under `site_docs/`.

Preview the docs locally with the shared project Python:

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m mkdocs serve
```

Run the maintained tests:

```bash
python -m pytest -q
```

## Generated Local Artifacts

The following are local, reproducible artifacts and are usually safe to delete when cleaning disk usage:

- `.pytest_cache/`
- `.omc/sessions/`
- `.omc/state/`
- `.superpowers/`
- `.venv-*`
- `apps/.venv/`
- `node_modules/`
- `dist/`
- `.cache/`
- `__pycache__/`
- `task_plan.md`
- `findings.md`
- `progress.md`

Keep `apps/`, `shared/`, `docs/`, `.env`, and `.git` unless you intentionally want to remove source, documentation, config, or repository history.
