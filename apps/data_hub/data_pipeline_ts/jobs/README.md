# `jobs/`

`jobs` 目录负责维护 `data_pipeline_ts` 的静态任务定义。这里不直接执行抓取或写库，而是回答三个问题：

1. 有哪些调度分组可以跑
2. 每个任务长什么样
3. 哪些 fetcher、表名、参数模板、执行分组应该绑定在一起

换句话说，`execution/` 负责“怎么跑”，`jobs/` 负责“跑什么”。

## 目录内文件

| 文件 | 作用 | 被谁依赖 |
| --- | --- | --- |
| `profiles.py` | 定义 profile 枚举和调度配置，例如 cron、并发模式、回补模式 | `specs.py`、`catalog.py`、`execution/runner.py`、`scripts/install_launchd.sh` |
| `specs.py` | 定义 `JobSpec`、`InfrastructureSpec`、`JobRunResult` 三个核心 dataclass | `catalog.py`、`execution/runner.py`、`execution/infrastructure.py`、`execution/persistence.py` |
| `catalog.py` | 组装所有业务 job 和基础设施同步目标，是本目录最核心的注册表 | `execution/selection.py`、`tests/*`、`data_explorer/*` |
| `__init__.py` | 对外统一导出公共符号，方便从 `jobs` 包直接 import | `main.py`、`tests/*` 或其他上层直接引用 |

## 文件之间的依赖关系

```text
profiles.py
  └── 提供 ProfileId / ProfileSpec / PROFILE_SPECS
        │
        ├── specs.py 使用 ProfileId 作为 JobSpec.profile 的类型
        └── catalog.py 使用 ProfileId 为每个任务分组

specs.py
  └── 提供 JobSpec / InfrastructureSpec / JobRunResult
        │
        └── catalog.py 通过 _job() / _infra() 构造具体定义

catalog.py
  └── 产出 ALL_JOBS / JOBS_BY_PROFILE / INFRASTRUCTURE_TARGETS 等注册结果
        │
        ├── execution/selection.py 用它做任务筛选
        ├── execution/runner.py 间接消费筛选后的 JobSpec
        └── execution/infrastructure.py 间接消费 InfrastructureSpec

__init__.py
  └── 只做聚合导出，不包含业务逻辑
```

## 运行时调用关系

日常任务链路：

```text
main.py
  └── execution/runner.py::run_once() / run_backfill()
        ├── execution/selection.py::select_job_specs()
        │     └── 读取 catalog.py::ALL_JOBS
        ├── 按 JobSpec.profile 分组
        ├── 读取 profiles.py::PROFILE_SPECS 判断并行/串行与 backfill 规则
        ├── 渲染 JobSpec.params
        ├── 实例化 JobSpec.fetcher_cls 并执行 fetch()
        └── 用 JobSpec.table_name / scope_columns 写库并记录 JobRunResult
```

单 job 显式参数链路（用于特殊回溯、手工快照和不适合走 profile 回放的任务）：

```text
scripts/run_job.sh
  └── data_pipeline_ts.run_job::main()
        ├── 解析重复的 --param key=value
        ├── execution/selection.py::select_job_specs(job_names=[...])
        ├── 实例化 JobSpec.fetcher_cls 并执行 fetch(**params)
        ├── 用 JobSpec.table_name / scope_columns 写库
        └── 生成 run_mode=direct 的 JobRunResult 并写入 job_run_log
```

基础设施同步链路：

```text
main.py --mode infrastructure
  └── execution/infrastructure.py::run_infrastructure()
        ├── execution/selection.py::select_infrastructure_specs()
        │     └── 读取 catalog.py::INFRASTRUCTURE_TARGETS
        ├── 实例化 InfrastructureSpec.fetcher_cls 并执行 fetch()
        └── 生成 JobRunResult 并写入 job_run_log
```

调度安装链路：

```text
scripts/install_launchd.sh
  └── 读取 profiles.py::PROFILE_SPECS
        └── 把 cron 转成 launchd 的 Hour / Minute
```

## 各文件内容说明

### `profiles.py`

这个文件只定义“调度分组”，不关心具体表和 fetcher。

核心对象：

- `ProfileId`
  7 个 profile 的枚举值，分别对应盘前、盘后主链路、盘后扩展、参考数据、财务夜跑和手工任务
- `ProfileSpec`
  每个 profile 的配置，包含：
  - `id`
  - `cron`
  - `execution_mode`
  - `backfill_mode`
- `PROFILE_SPECS`
  profile 到 `ProfileSpec` 的映射，是调度时间与回补策略的唯一真源
- `SCHEDULED_PROFILES`
  从 `PROFILE_SPECS` 派生出的“有 cron 的 profile”集合
- `PROFILE_NAMES`
  所有 profile 名称字符串，通常用于参数校验或 CLI 展示

当前 profile 一览：

| Profile | Cron | Execution Mode | Backfill Mode | 说明 |
| --- | --- | --- | --- | --- |
| `trade_day_pre_open` | `25 9 * * *` | `parallel` | `trade_day` | 盘前链路 |
| `trade_day_post_close_core` | `0 18 * * *` | `parallel` | `trade_day` | 盘后主链路 |
| `trade_day_post_close_extended` | `35 18 * * *` | `parallel` | `trade_day` | 盘后扩展链路 |
| `reference_trade_day_post_close` | `40 18 * * *` | `parallel` | `trade_day` | 交易日参考数据 |
| `financial_calendar_nightly` | `30 21 * * *` | `parallel` | `calendar_day` | 财务公告夜跑 |
| `reference_calendar_nightly` | `45 21 * * *` | `parallel` | `calendar_day` | 参考数据夜跑 |
| `manual` | `None` | `serial` | `manual` | 手工触发任务 |

### `specs.py`

这个文件只定义结构，不注册任何具体任务。

核心 dataclass：

- `JobSpec`
  日常/回补任务定义。关键字段包括：
  - `name`：CLI 里的任务名
  - `table_name`：写入的目标表
  - `fetcher_cls`：真正执行取数的 fetcher 类
  - `description`：中文说明
  - `profile`：所属调度分组
  - `params`：运行时模板参数，例如 `{"trade_date": "{trade_date}"}`
  - `scope_columns`：写库覆盖范围
  - `table_schema`：从 fetcher 上读取的 schema 元数据
- `InfrastructureSpec`
  基础设施同步任务定义，例如 `stock_basic`、`trade_cal`
- `JobRunResult`
  单次执行结果的统一结构，供 `execution/runner.py` 与 `execution/infrastructure.py` 记录运行结果

### `catalog.py`

这是 `jobs` 目录的核心文件，负责把 fetcher 和业务语义装配成可运行的任务注册表。

内部辅助函数：

- `_job(...)`
  把输入参数封装为 `JobSpec`，并自动从 fetcher 上读取 `table_schema`
- `_infra(...)`
  把输入参数封装为 `InfrastructureSpec`
- `_group_jobs_by_profile(...)`
  按 `profile` 聚合任务，生成 `JOBS_BY_PROFILE`

对外导出的主要对象：

| 符号 | 含义 | 当前数量 |
| --- | --- | --- |
| `BASIC_DATA_JOBS` | `fetchers/basic_data/` 对应 job | 3 |
| `BOARD_DATA_JOBS` | `fetchers/board_data/` 对应 job | 6 |
| `FINANCIAL_DATA_JOBS` | `fetchers/financial_data/` 对应 job | 9 |
| `MARGIN_DATA_JOBS` | `fetchers/margin_data/` 对应 job | 4 |
| `MONEY_FLOW_DATA_JOBS` | `fetchers/money_flow_data/` 对应 job | 4 |
| `REFERENCE_DATA_JOBS` | `fetchers/reference_data/` 对应 job | 9 |
| `SPECIAL_DATA_JOBS` | `fetchers/special_data/` 对应 job | 8 |
| `STOCK_MARKET_DATA_JOBS` | `fetchers/stock_market_data/` 对应 job | 7 |
| `ALL_JOBS` | 所有 `JobSpec` 汇总 | 50 |
| `INFRASTRUCTURE_TARGETS` | 基础设施同步目标 | 3 |
| `JOBS_BY_PROFILE` | 按 profile 分组后的任务视图 | 7 个 profile |

当前 `JOBS_BY_PROFILE` 统计：

| Profile | Job 数量 |
| --- | --- |
| `trade_day_post_close_core` | 4 |
| `trade_day_post_close_extended` | 19 |
| `trade_day_pre_open` | 5 |
| `financial_calendar_nightly` | 8 |
| `reference_calendar_nightly` | 7 |
| `manual` | 6 |
| `reference_trade_day_post_close` | 1 |

当前 `manual` profile 实际包含 6 个 job：

- `hm_list`
- `pledge_detail`
- `cyq_chips`
- `fina_audit`
- `stock_daily`（已弃用，历史回溯不再单独跑）
- `stock_daily_basic`（已弃用，历史回溯不再单独跑）

这个文件也是新增任务时最常改动的位置。典型方式是：

1. 先在 `fetchers/` 下实现新的 fetcher
2. 在 `catalog.py` 顶部引入 fetcher 类
3. 用 `_job(...)` 或 `_infra(...)` 注册到对应目录分组列表
4. 让 `ALL_JOBS` 或 `INFRASTRUCTURE_TARGETS` 自动被执行层消费

### `__init__.py`

这个文件没有自己的业务逻辑，只负责把 `catalog.py`、`profiles.py`、`specs.py` 里的公共符号集中导出，方便外部统一 import，例如：

```python
from apps.data_hub.data_pipeline_ts.jobs import ALL_JOBS, PROFILE_SPECS, JobSpec
```

当前真正的任务定义就在 `jobs/` 目录中，没有额外兼容层。

因此，后续如果要改任务、profile 或基础设施目标，应该直接修改本目录里的文件。

## 读这个目录时可以把它理解成什么

可以把 `jobs/` 看成一个“静态注册中心”：

- `profiles.py` 定义调度维度
- `specs.py` 定义数据结构
- `catalog.py` 填充注册内容
- `__init__.py` 暴露公共 API

执行层不会自己发明任务，只会消费这里定义好的对象。
