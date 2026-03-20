# StockProject

This repository currently centers on `apps/data_hub`, a Python-first A-share data platform for fetch, write, scheduling, read-only exploration, and monitoring.

## Active Layout

```text
.
|-- apps/
|   `-- data_hub/
|       |-- data_pipeline_ts/   # TuShare fetchers, jobs, notebooks, execution
|       |-- data_pipeline_ak/   # AkShare-side helpers and imports
|       |-- data_explorer/      # read-only data explorer backend + frontend
|       `-- tests/              # app-level composition tests
|-- shared/
|   |-- scripts/
|   |   `-- resolve_project_python.sh
|   `-- stock_core/             # shared env, db, python runtime helpers
|-- docs/                       # plans and design documents
|-- experiments/                # exploratory notebooks, prototypes, notes
|-- env.example
|-- .gitignore
|-- pyproject.toml
`-- README.md
```

Detailed app structure and commands live in [apps/data_hub/README.md](apps/data_hub/README.md).

## Key Directories

- `apps/data_hub/data_pipeline_ts/`: TuShare daily jobs, backfill, infrastructure sync, notebooks, and related tests.
- `apps/data_hub/data_pipeline_ak/`: AkShare-side imports and auxiliary data flows.
- `apps/data_hub/data_explorer/`: read-only schema/data explorer and monitoring UI.
- `shared/stock_core/`: shared env loading, DB helpers, and Python runtime resolution.
- `docs/`: durable plans and design notes.
- `experiments/`: non-canonical experiments and research material.

## Local Configuration

Copy `env.example` to `.env` and fill in the required variables:

- `TUSHARE_TOKEN`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `TS_MYSQL_DATABASE`
- `AK_MYSQL_DATABASE`
- `MYSQL_CHARSET`

There are no code defaults for these values.

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

Run daily jobs:

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help
```

Run a backfill:

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh --help
```

Run the data explorer:

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

Run the maintained tests:

```bash
python -m pytest -q
```

## Generated Local Artifacts

The following are local, reproducible artifacts and are usually safe to delete when cleaning disk usage:

- `.pytest_cache/`
- `.omc/`
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
