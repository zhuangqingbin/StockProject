# data_pipeline_ts

`data_pipeline_ts` 是基于 TuShare 的 Python 原生 pipeline，用于生产环境的数据采集、入库、调度与回填。

## 核心职责

- 调用 TuShare fetcher 并写入 MySQL 表
- 跑每日 profile 与历史回填
- 同步基础设施表，例如 `stock_basic`、`stock_company`、`trade_cal`
- 为 `analysis` 提供数据库底座

## 常用命令

跑一次每日 profile：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-03-16
```

跑历史回填：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_post_close_core \
  --start 20250101 \
  --end 20250331
```

同步基础设施表：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company,trade_cal
```

## Analysis 数据约定

新做日级别分析时，把 `stock_stk_factor_pro` 当作主表，按 `(ts_code, trade_date)` 关联其他副表。

涉及价格的研究计算优先使用 `open_qfq`、`high_qfq`、`low_qfq`、`close_qfq` 这一组前复权字段。
