# data_pipeline_ts

`data_pipeline_ts` is the Python-native TuShare pipeline used for production ingestion, persistence, scheduling, and backfill.

## Core Responsibilities

- call TuShare fetchers and write MySQL tables
- run daily profiles and historical backfills
- sync infrastructure tables such as `stock_basic`, `stock_company`, and `trade_cal`
- provide the database base used by `analysis`

## Common Commands

Run one daily profile:

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-03-16
```

Run a backfill:

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_post_close_core \
  --start 20250101 \
  --end 20250331
```

Sync infrastructure tables:

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company,trade_cal
```

## Analysis Data Convention

For new daily analysis work, treat `stock_stk_factor_pro` as the primary base table and join side tables by `(ts_code, trade_date)`.

Prefer `open_qfq`, `high_qfq`, `low_qfq`, and `close_qfq` for price-based research calculations.
