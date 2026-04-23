# Data Hub

`data_hub` is the repository’s data-production and observability application.

It owns:

- A-share data ingestion and persistence
- daily scheduling and backfill workflows
- read-only exploration and monitoring
- research-facing analysis scripts that read database tables directly

## Components

- `data_pipeline_ts`: TuShare-native production pipeline
- `data_pipeline_ak`: AkShare helper context for calendar and fallback imports
- `data_explorer`: read-only FastAPI + React browsing and monitoring UI
- `analysis`: database-backed research scripts and strategy matrices

## Common Entry Points

- `bash apps/data_hub/setup.sh`
- `bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help`
- `./apps/data_hub/data_explorer/scripts/run.sh backend`
- `./apps/data_hub/data_explorer/scripts/run.sh frontend`
