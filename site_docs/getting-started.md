# Getting Started

## Environment Baseline

- Python `3.11+`
- Node.js `18+` for frontend development
- MySQL with credentials loaded from `.env` or `.env.local`

## Shared Python Runtime

Resolve the project Python:

```bash
./shared/scripts/resolve_project_python.sh
```

Create the shared `apps/.venv` and install dependencies:

```bash
bash apps/setup.sh
```

## Common Startup Commands

Start the `data_explorer` backend and frontend:

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

Start the `quant_platform` backend and frontend:

```bash
bash apps/quant_platform/scripts/run.sh backend
bash apps/quant_platform/scripts/run.sh frontend
```

## Preview The Docs Portal

Use the shared project Python:

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m mkdocs serve
```
