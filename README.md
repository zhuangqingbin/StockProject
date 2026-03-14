# StockProject

This repository now uses a monorepo layout with two maintained applications.

## Applications

- `apps/stock_data_platform/`
  - TuShare-based stock data fetching, utility code, and local data workflows.
- `apps/stock_bi/`
  - A-share market BI application with FastAPI backend and frontend assets.

## Shared Root Areas

- `DataStore/`
  - Shared local data storage used by the maintained applications.
- `shared/stock_core/`
  - Shared configuration and database helpers reused by both maintained applications.
- `docs/`
  - Design notes, implementation plans, and project documentation.
- `experiments/`
  - Research notebooks, backtesting studies, prototypes, and historical side work.
- `assets/`
  - Books, screenshots, generated charts, and other non-code artifacts.

## Compatibility Layer

The root `DataFetch/`, `common/`, `main.py`, and `demo_test.py` remain as thin compatibility entrypoints so older imports still resolve while the repository settles into the new layout.

## Layout

```text
.
|-- apps/
|   |-- stock_bi/
|   `-- stock_data_platform/
|-- DataFetch/
|-- common/
|-- DataStore/
|-- assets/
|-- docs/
|-- experiments/
|-- shared/
|-- main.py
`-- requirements.txt
```

## Local Configuration

Secrets are expected in environment variables, not in source files. See `.env.example` for the supported variables.

Important variables:

- `TUSHARE_TOKEN`
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
pip install -r requirements.txt
```

Run the stock data platform demo:

```bash
export TUSHARE_TOKEN=your_token
python3 main.py
```

Run the BI application:

```bash
cd apps/stock_bi/codex
./run.sh
```

Run the maintained test suite:

```bash
./scripts/run_tests.sh
```
