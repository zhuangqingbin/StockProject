# Common Commands

## Environment And Setup

```bash
./shared/scripts/resolve_project_python.sh
bash apps/setup.sh
```

## Data Hub

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help
./apps/data_hub/data_explorer/scripts/run.sh backend
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

## Quant Platform

```bash
bash apps/quant_platform/scripts/run.sh backend
bash apps/quant_platform/scripts/run.sh frontend
```

## Docs Portal

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m mkdocs serve

PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m mkdocs build --strict
```
