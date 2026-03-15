# StockProject

This repository keeps only the maintained runtime and the shared infrastructure it needs.

## Root Structure

- `apps/`
  - maintained application code
- `shared/stock_core/`
  - shared environment and database helpers used by both apps
- `.env.example`
  - environment variable template
- `pyproject.toml`
  - pytest discovery configuration
- `.gitignore`
  - local artifact ignore rules

## Layout

```text
.
|-- apps/
|   |-- stock_bi/
|   `-- stock_data_platform/
|       |-- .cache/
|       `-- scripts/
|-- shared/
|-- .env.example
|-- .gitignore
|-- README.md
`-- pyproject.toml
```

## Local Configuration

Secrets are expected in environment variables, not in source files. See `.env.example` for the supported variables.

Important variables:

- `TUSHARE_TOKEN`
- `STOCK_DATA_DAILY_SCHEDULE_HOUR`
- `STOCK_DATA_DAILY_SCHEDULE_MINUTE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `MAIL_HOST`
- `MAIL_USER`
- `MAIL_TOKEN`
- `MAIL_RECEIVERS`

## Quick Start

Install stock data platform dependencies:

```bash
pip install -r apps/stock_data_platform/requirements.txt
```

Maintained app runtimes are expected to work on both `x86_64` and `arm64`. Use each app's local virtual environment strategy rather than mixing user-level Python packages across architectures.

Run the stock data platform demo:

```bash
export TUSHARE_TOKEN=your_token
python3 apps/stock_data_platform/main.py
```

Run the BI application:

```bash
cd apps/stock_bi/codex
./run.sh
```

Run the maintained test suite:

```bash
./apps/stock_data_platform/scripts/run_tests.sh
```

## App Notes

- `apps/stock_data_platform/`
  - upstream data fetch and daily write workflows
  - `.cache/` is the app-local transient cache directory
  - `scripts/` contains the maintained test, daily-job, and schedule-install entrypoints
- `apps/stock_bi/codex/`
  - FastAPI backend and frontend BI application
