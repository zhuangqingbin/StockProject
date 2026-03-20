# Data Hub — Requirements

## 1. Scope

`data_hub` 的数据任务只走 `data_pipeline_ts` 链路。

系统范围包括：

- TuShare / AkShare fetcher
- `data_pipeline_ts` 任务选择、执行、回溯和基础设施同步
- MySQL 写入和 `job_run_log`
- `data_explorer` 只读浏览与监控
- notebook 巡检支持

系统范围不包括：

- 任意 SQL 执行或写操作界面

## 2. Runtime Requirements

### 2.1 Sole Runtime

- 唯一任务入口是 `apps/data_hub/data_pipeline_ts/main.py`
- 唯一 shell 入口位于 `apps/data_hub/data_pipeline_ts/scripts/`
- 运行模式只有三种：
  - `once`
  - `backfill`
  - `infrastructure`

### 2.2 Job Registry

- 所有常规任务定义在 `data_pipeline_ts/registry.py::ALL_JOBS`
- 所有基础设施目标定义在 `data_pipeline_ts/registry.py::INFRASTRUCTURE_TARGETS`
- 每个任务定义必须包含：
  - `name`
  - `fetcher_cls`
  - `table_name`
  - `profile`
  - `params`
  - `scope_columns`

### 2.3 Execution Semantics

- 同一 `profile` 内通过 `ThreadPoolExecutor` 并发执行
- 单个任务失败不阻断同 profile 其他任务
- 每个任务都记录 `job_run_log`
- 回溯按自然日迭代，并只在交易日实际执行
- 基础设施同步不经过常规 job 列表

### 2.4 Write Semantics

- 写入前必须校验 DataFrame 列与 `TableSchema`
- 首次写入自动建表
- 线上缺列时自动补列
- 按 `scope_columns` 先删旧切片，再 append 新数据
- 不做 mirror table 双写

### 2.5 Observability

- 成功与失败都记录到 `job_run_log`
- 必须记录：
  - `job_name`
  - `status`
  - `rows_fetched`
  - `rows_written`
  - `duration_seconds`
  - `error`
  - `executed_at`

## 3. Data Requirements

### 3.1 Sources

- TuShare 是主数据源
- AkShare 当前只保留交易日历兜底能力和后续扩展位

### 3.2 Inventory

- 常规任务 39 个
- 基础设施目标 3 个：
  - `stock_basic`
  - `stock_company`
  - `trade_cal`

### 3.3 Trigger Profiles

保留以下 profile：

| Profile | 说明 |
| --- | --- |
| `trade_day_pre_open` | 盘前 |
| `trade_day_post_close_core` | 盘后核心 |
| `trade_day_post_close_extended` | 盘后扩展 |
| `financial_calendar_nightly` | 财务夜间 |
| `reference_calendar_nightly` | 参考数据夜间 |
| `reference_trade_day_post_close` | 交易日参考数据 |
| `reference_manual_snapshot` | 手工快照 |
| `manual_special` | 手工特殊任务 |

## 4. Interface Requirements

### 4.1 CLI

`data_pipeline_ts/main.py` 需要支持：

- `--mode`
- `--profiles`
- `--jobs`
- `--targets`
- `--as-of`
- `--start`
- `--end`
- `--max-workers`

### 4.2 Scripts

需要保留：

- `data_pipeline_ts/scripts/run_daily.sh`
- `data_pipeline_ts/scripts/run_backfill.sh`
- `data_pipeline_ts/scripts/sync_infrastructure.sh`
- `data_pipeline_ts/scripts/install_launchd.sh`

### 4.3 launchd

- 通过 `install_launchd.sh` 安装固定时刻的 profile 调度
- launchd 只调用 `data_pipeline_ts/scripts/run_daily.sh`
- 不再注入或区分任何 precompute 开关

## 5. Environment Requirements

必须支持以下环境变量：

- `TUSHARE_TOKEN`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `TS_MYSQL_DATABASE`
- `AK_MYSQL_DATABASE`
- `MYSQL_CHARSET`

数据库连接配置不再带代码默认值，必须在 `.env` / `.env.local` 中显式提供。

## 6. data_explorer Requirements

- `data_explorer` 需要从 `data_pipeline_ts` 的任务与表绑定信息读取表目录
- `data_explorer` 通过 `TS_MYSQL_DATABASE` 和 `AK_MYSQL_DATABASE` 的只读连接实时读取表规模、日期范围、DDL、索引和运行状态

## 7. Non-Functional Requirements

- Python 3.11+
- 支持 `arm64` / `x86_64` app-local venv
- 测试覆盖 fetcher、runtime、executor、data_explorer 服务和 notebook 支撑层
- 文档与代码说明统一以 `data_pipeline_ts` 为准
