# Research

The `apps/quant_platform/research/` area is the factor, ranking, and backtest workflow for the repo.

## Common Research Entrypoints

Run factor research directly from the database with `research-factor --from-db`:

```bash
bash apps/quant_platform/scripts/run.sh research-factor \
  --from-db \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output-dir apps/quant_platform/research/output/full_research
```

Run the full pipeline:

```bash
apps/.venv/bin/python -m apps.quant_platform.research.scripts.run_full_pipeline \
  --start-date 2023-01-01 \
  --end-date 2025-12-31 \
  --max-factors 60
```

## Published Surface

- frontend route: `/research`
- API docs from the backend app
- static outputs served through `research-assets`
