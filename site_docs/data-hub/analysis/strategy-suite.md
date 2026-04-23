# Strategy Suite

The Strategy Suite is the unified entrypoint for running the stable matrix scripts together.

## Entry Point

Use `run_strategy_suite.py`:

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite \
  --start-date 20240101 \
  --strategies bottom_volume_matrix,limit_inst_matrix,top_list_matrix
```

## Shared Parameters

- `--start-date`
- `--end-date`
- `--strategies`
- `--min-sample`
- `--top-n`
- `--output-dir`

## Output Layout

The suite writes a timestamped root under `analysis/outputs/strategy_suite/` and produces:

- `suite_summary.csv`
- `suite_compact_ranking.csv`
- `suite_compact_by_strategy.csv`

Each child strategy still writes its own timestamped CSV and Markdown summary under its suite subdirectory.
