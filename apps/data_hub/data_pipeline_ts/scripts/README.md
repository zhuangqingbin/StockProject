# `scripts/`

`scripts/` 是 `data_pipeline_ts` 的 Shell 入口层，负责解析 Python 路径并把参数转发给 `main.py`。

## 文件说明

| 脚本 | 作用 |
|------|------|
| `run_daily.sh` | 主入口脚本，解析 Python 后调用 `main.py`，默认模式为 `once` |
| `run_backfill.sh` | 便捷包装，等价于 `run_daily.sh --mode backfill "$@"` |
| `run_job.sh` | 单 job 显式参数入口，等价于 `python -m apps.data_hub.data_pipeline_ts.run_job "$@"` |
| `sync_infrastructure.sh` | 便捷包装，等价于 `run_daily.sh --mode infrastructure "$@"` |
| `install_launchd.sh` | macOS launchd 定时任务安装器 |

## `run_daily.sh`

主入口，所有其他脚本最终都通过它调用 `main.py`。

**Python 路径解析顺序**：

1. `apps/.venv/bin/python`（apps 共享 venv）
2. `shared/scripts/resolve_project_python.sh`（系统回退）

**使用方式**：

```bash
# 默认 once 模式，跑今天的盘后主链路
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core

# 指定日期
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-03-17

# 跑单个任务
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --jobs stock_daily --as-of 2026-03-17
```

## `run_backfill.sh`

回填模式的便捷入口，内部直接调用 `run_daily.sh --mode backfill`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_post_close_core \
  --start 20260101 --end 20260317
```

## `run_job.sh`

单 job 显式参数入口，适合：

- `manual` profile 下的快照或全市场 fan-out 任务
- `kpl_list` / `report_rc` 这类不适合混入统一 profile 回放的范围补数
- 需要直接传 `start_date` / `end_date` / `snapshot_date` 的一次性任务

参数通过重复的 `--param key=value` 传入；数组/对象/布尔值支持 JSON 解析，其余值按字符串传递。

```bash
# 触发一次 hm_list 快照
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job hm_list \
  --param snapshot_date=20260318

# 单独回补 report_rc 的一个时间窗口
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job report_rc \
  --param start_date=20260101 \
  --param end_date=20260317
```

## `sync_infrastructure.sh`

基础设施同步的便捷入口，内部直接调用 `run_daily.sh --mode infrastructure`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company,trade_cal \
  --start 20260101 --end 20261231
```

## `install_launchd.sh`

macOS launchd 定时任务安装器，自动为所有有 cron 的 profile 生成 plist 并注册。

**工作原理**：

1. 通过 Python 读取 `jobs/profiles.py` 中的 `PROFILE_SPECS`
2. 筛选出有 `cron` 的 profile，解析为 `Hour/Minute`
3. 为每个 profile 生成 `~/Library/LaunchAgents/com.stockproject.stock-data-v1-orchestrator-v2.{profile}.plist`
4. 用 `launchctl bootstrap` 注册到当前用户

**可选参数**：

- `--max-workers N`
  - 给每个定时 profile 追加 `--max-workers N`
  - 不传时保持旧行为，仍使用运行时代码默认并发

**产出**：

| Profile | Plist Label | 触发时间 |
|---------|-------------|----------|
| `trade_day_pre_open` | `...trade-day-pre-open` | 每天 09:25 |
| `trade_day_post_close_core` | `...trade-day-post-close-core` | 每天 18:00 |
| `trade_day_post_close_extended` | `...trade-day-post-close-extended` | 每天 18:35 |
| `reference_trade_day_post_close` | `...reference-trade-day-post-close` | 每天 18:40 |
| `financial_calendar_nightly` | `...financial-calendar-nightly` | 每天 21:30 |
| `reference_calendar_nightly` | `...reference-calendar-nightly` | 每天 21:45 |

日志输出到 `apps/data_hub/data_pipeline_ts/.logs/`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh

# 让所有定时 profile 都以单 worker 运行
bash apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh --max-workers 1
```
