# Analysis

`apps/data_hub/data_pipeline_ts/analysis/` is the database-backed research and strategy-matrix area inside `data_hub`.

## What Lives Here

- strategy-family directories such as `bottom_val_strategies`
- top-level orchestration such as `run_strategy_suite.py`
- findings summaries derived from historical research output

## Stable Matrix Entrypoints

- `bottom_volume_matrix`
- `flow_chip_northbound_matrix`
- `limit_inst_matrix`
- `supply_shock_matrix`
- `top_list_matrix`

## Common Commands

Run the unified suite:

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite \
  --start-date 20240101
```

Run one matrix directly:

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix \
  --start-date 20240101
```
