# Data Hub Design

## 1. Current Architecture

`data_hub` 的数据任务架构已经收敛到一条运行时链路：

- `data_pipeline_ts/fetchers/base.py` 提供 fetcher 基类与表结构定义，供 TS / AK pipeline 复用
- `data_pipeline_ts/jobs/` 负责 profile、job spec 和 catalog
- `data_pipeline_ts/fetchers/` 负责 TuShare 取数和表结构声明
- `data_pipeline_ts/fetchers/client.py` 负责 TuShare client 集成
- `data_pipeline_ts/notebooks/` 负责 TuShare 数据巡检 notebook
- `data_pipeline_ts/calendar.py` 和 `context.py` 负责交易日和执行上下文
- `data_pipeline_ts/persistence.py` 负责数据库写入和 schema 演进
- `data_pipeline_ts/execution/` 负责任务筛选、参数渲染、运行编排和 infrastructure sync
- `data_pipeline_ak/` 负责 AkShare provider 和取数入口
- `data_pipeline_ts/registry.py` 和 `runtime.py` 保留兼容导出层
- `data_pipeline_ts/executor.py` 保留兼容导出层
- `data_pipeline_ts/main.py` 负责 CLI 模式分发
- `data_pipeline_ts/scripts/` 负责 shell 入口和 launchd 安装

## 2. Directory Layout

```text
apps/data_hub/
├── data_pipeline_ak/
│   ├── fetchers/
│   ├── provider/
│   └── tests/
├── data_explorer/
├── docs/
├── data_pipeline_ts/
│   ├── __init__.py
│   ├── calendar.py
│   ├── context.py
│   ├── executor.py
│   ├── execution/
│   ├── fetchers/
│   ├── jobs/
│   ├── main.py
│   ├── notebooks/
│   ├── persistence.py
│   ├── provider/
│   ├── registry.py
│   ├── runtime.py
│   ├── scripts/
│   └── tests/
├── tests/
└── requirements.txt
```

## 3. Runtime Model

### 3.1 Registry

任务定义已经拆到 `data_pipeline_ts/jobs/`：

核心对象：

- `JobSpec`
- `InfrastructureSpec`
- `JobRunResult`
- `ALL_JOBS`
- `INFRASTRUCTURE_TARGETS`
- `PROFILE_NAMES`

模块归属：

- `jobs/specs.py`：spec dataclass
- `jobs/profiles.py`：profile 和调度元信息
- `jobs/catalog.py`：具体 job / infrastructure catalog
- `registry.py`：对旧导入面的兼容层

设计原则：

- 常规任务和基础设施目标分开建模
- 每个任务定义直接引用 fetcher class，不再经过字符串解析
- 参数模板和 `scope_columns` 与运行时定义放在同一处维护

### 3.2 ExecutionContext

`data_pipeline_ts/context.py::ExecutionContext` 负责：

- 计算 `as_of_date`
- 根据交易日历推导 `trade_date`
- 渲染 `{trade_date}`、`{current_date}` 等模板变量

`data_pipeline_ts/calendar.py::get_trade_cal` 负责：

- 调用 `TradeCalFetch`
- 过滤开市日列表
- 为上下文和 provider 测试提供统一交易日服务

### 3.3 DatabaseWriter

`data_pipeline_ts/persistence.py::DatabaseWriter` 负责：

- `build_mysql_url()` / `get_engine()`
- 列校验
- 自动建表
- 缺列补齐
- 复合索引补齐
- 按 `scope_columns` 删除旧切片
- append 新数据
- 记录 `job_run_log`

## 4. Data Flow

执行编排已经拆到 `data_pipeline_ts/execution/`：

- `execution/selection.py`：job / infrastructure target 选择和 CSV 参数解析
- `execution/rendering.py`：context 驱动的参数渲染和 fetch 结果标准化
- `execution/runner.py`：`run_once()`、`run_backfill()` 和 profile 内执行策略
- `execution/infrastructure.py`：`run_infrastructure()` 和基础设施抓取参数
- `executor.py`：对旧导入面的兼容层

### 4.1 Once

`run_daily.sh` -> `main.py --mode once` -> `select_job_specs()` -> `ExecutionContext.for_as_of()` -> `_run_grouped_jobs()` -> `DatabaseWriter`

### 4.2 Backfill

`run_backfill.sh` -> `main.py --mode backfill` -> `_iter_calendar_days()` -> `ExecutionContext.for_as_of()` -> 交易日过滤 -> `_run_grouped_jobs()`

### 4.3 Infrastructure

`sync_infrastructure.sh` -> `main.py --mode infrastructure` -> `select_infrastructure_specs()` -> `DatabaseWriter`

## 5. Execution Rules

- 同一 profile 内并发执行，默认最多 8 个 worker
- 单任务失败不阻断同 profile 其他任务
- 回溯逐日执行，非交易日跳过
- 空结果不写表，但仍记录运行日志
- 当前链路只负责抓取、写库和记录日志
- 不再触发任何外部 precompute 或 post-sync hook

## 6. Scheduling

macOS 定时调度通过 `data_pipeline_ts/scripts/install_launchd.sh` 安装。

固定调度对象：

- `trade_day_pre_open`
- `trade_day_post_close_core`
- `trade_day_post_close_extended`
- `reference_trade_day_post_close`
- `financial_calendar_nightly`
- `reference_calendar_nightly`

手工任务：

- `reference_manual_snapshot`
- `manual_special`
- `manual_infrastructure`

## 7. data_explorer Integration

`data_explorer` 不再从外部 job 配置读取任务信息。

当前依赖关系是：

- 表目录：`data_pipeline_ts/fetchers/*`
- 任务绑定：`data_pipeline_ts/jobs/catalog.py`
- 运行状态：`job_run_log`
- 数据库结构：实时 MySQL introspection

## 8. Extending The System

新增常规表时：

1. 在对应 pipeline 的 `fetchers/` 下新增 fetcher 文件
2. 在类体内声明 `fields` 和 `table_schema`
3. 在对应 pipeline 的 `fetchers/__init__.py` 导出
4. 在对应 pipeline 的 `jobs/catalog.py` 增加任务定义
5. 补充对应 pipeline 测试
6. 如需在 `data_explorer` 中展示中文说明，更新 `data_explorer/config/table_catalog.yaml`

新增基础设施目标时：

1. 新增 fetcher
2. 在 `data_pipeline_ts/jobs/catalog.py::INFRASTRUCTURE_TARGETS` 注册
3. 验证 `sync_infrastructure.sh` 命令路径

## 9. Key Constraints

- 只使用 `data_pipeline_ts` 作为运行入口
- 任务定义只维护在 `data_pipeline_ts/jobs/`
- shell 入口只维护在 `data_pipeline_ts/scripts/`
- 写入语义统一通过 `data_pipeline_ts/persistence.py::DatabaseWriter`
