# Stock Data Platform

The stock data platform is now located under `apps/stock_data_platform/`.

## Main Contents

- `DataFetch/`
  - TuShare client, fetcher base class, and market data endpoint wrappers
- `common/`
  - configuration, utilities, and auxiliary helpers
- `main.py`
  - simple fetch demo entrypoint
- `demo_test.py`
  - ad hoc API demo script
- `requirements.txt`
  - Python dependencies for this app

## Runtime Notes

- shared data still lives at the repository root in `DataStore/`
- shared config and database helpers live in `shared/stock_core/`
- app-local config re-exports shared settings via `common/config.py`
- legacy root imports continue to work through compatibility wrappers

## Run

From the repository root:

```bash
python3 main.py
```

Or from this app directory:

```bash
python3 apps/stock_data_platform/main.py
```
