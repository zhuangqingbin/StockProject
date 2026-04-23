# Testing

## Python Test Suite

Run the maintained Python tests:

```bash
python -m pytest -q
```

## Focused App Commands

`data_hub` tests:

```bash
python -m pytest -q \
  apps/data_hub/tests \
  apps/data_hub/data_explorer/tests \
  apps/data_hub/data_pipeline_ts/tests \
  apps/data_hub/data_pipeline_ak/tests
```

`data_explorer` frontend tests:

```bash
npm --prefix apps/data_hub/data_explorer/frontend test
```

`quant_platform` tests:

```bash
python -m pytest -q apps/quant_platform/tests
```
