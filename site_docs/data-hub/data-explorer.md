# data_explorer

`data_explorer` is the read-only data catalog, preview, and monitoring application for the `data_hub` databases.

## Features

- table directory browsing
- schema and index inspection
- paginated data preview
- task and run monitoring
- database-level metadata views

## Run Commands

Start the backend:

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
```

Start the frontend:

```bash
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

Run tests:

```bash
python -m pytest -q apps/data_hub/data_explorer/tests
npm --prefix apps/data_hub/data_explorer/frontend test
```
