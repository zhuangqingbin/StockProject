# `execution`

`execution/` 是 `apps/data_hub/data_pipeline_ts` 的执行编排层，负责把外部传入的模式、任务选择条件和日期上下文，转换成真正的抓取、写库与运行日志记录流程。

它本身不维护任务清单，也不关心具体 API 细节，而是把职责拆成 4 个小模块：

- `selection.py`：选任务
- `rendering.py`：渲染运行参数
- `runner.py`：执行普通 job
- `infrastructure.py`：执行基础设施同步任务

## 目录职责

| 文件 | 作用 | 对外暴露 |
| --- | --- | --- |
| `__init__.py` | 包级门面，统一 re-export 主要函数，供 `main.py` 和兼容层导入 | `run_once`、`run_backfill`、`run_infrastructure`、`select_*`、`_parse_csv_values` |
| `selection.py` | 根据 `job_names` / `profiles` / `target_names` 从 catalog 中筛选出要跑的 spec，并做参数校验 | `select_job_specs`、`select_infrastructure_specs`、`_parse_csv_values` |
| `rendering.py` | 将 `JobSpec.params` 里的模板参数按 `ExecutionContext` 渲染成真正传给 fetcher 的参数；同时把 fetch 结果统一转成 `DataFrame` | `_render_params`、`_ensure_dataframe` |
| `runner.py` | 普通 job 的核心执行器，覆盖 `once` 和 `backfill` 两种模式；负责串并行调度、参数渲染、调用 fetcher、写库、记录运行结果 | `run_once`、`run_backfill` |
| `infrastructure.py` | 基础表同步执行器，独立处理 `stock_basic`、`stock_company`、`trade_cal` 等基础设施目标 | `run_infrastructure` |

## 每个文件在做什么

### `__init__.py`

这个文件没有业务逻辑，只做一层统一出口：

- 从 `runner.py` 暴露 `run_once`、`run_backfill`
- 从 `infrastructure.py` 暴露 `run_infrastructure`
- 从 `selection.py` 暴露筛选函数和 CSV 参数解析函数

这样上层只需要依赖 `apps.data_hub.data_pipeline_ts.execution`，不需要关心实现拆在哪个文件里。

### `selection.py`

这个模块只负责“挑选要执行的 spec”。

- `_parse_csv_values(raw_values)`：把 CLI 传入的逗号分隔字符串转换成 `list[str]`
- `select_job_specs(...)`
  - 默认从 `jobs.catalog.ALL_JOBS` 读取所有 `JobSpec`
  - 用 `job_names` 过滤具体任务
  - 用 `profiles` 过滤 profile
  - 若传入不存在的 job 或 profile，会直接抛 `ValueError`
- `select_infrastructure_specs(...)`
  - 默认从 `jobs.catalog.INFRASTRUCTURE_TARGETS` 读取基础设施目标
  - 校验 target 是否存在
  - 返回有序的 `InfrastructureSpec` 列表

可以把它理解成执行前的“白名单解析层”。

### `rendering.py`

这个模块只做两件事：

- `_ensure_dataframe(value)`
  - fetcher 返回 `None` 时转成空 `DataFrame`
  - 已经是 `DataFrame` 时原样返回
  - 其他结构尝试包成 `DataFrame`
- `_render_params(params, context)`
  - 遍历 `JobSpec.params`
  - 把 `{trade_date}`、`{current_date}`、`{trade_dt}`、`{current_dt}` 这类模板变量渲染成运行时值
  - 实际渲染逻辑交给 `ExecutionContext.render_value()`

它是执行层和 `ExecutionContext` 之间的薄适配器。

### `runner.py`

这是普通 job 的主执行器，内部可以拆成 3 层：

1. 单任务执行

- `_run_single_job(spec, context, writer)`
  - 先通过 `_render_params()` 解析运行参数
  - 实例化 `spec.fetcher_cls`
  - 调用 `fetcher.fetch(**resolved_params)`
  - 用 `_ensure_dataframe()` 统一结果格式
  - 有数据时调用 `DatabaseWriter.write(spec, frame)` 落库
  - 无论成功还是失败，都封装成 `JobRunResult`

2. 一批任务的调度执行

- `_run_grouped_jobs(specs, context, writer, max_workers)`
  - 先按 `spec.profile` 分组
  - 再读取 `jobs.profiles.PROFILE_SPECS[profile].execution_mode`
  - `serial` profile 逐个执行
  - `parallel` profile 用 `ThreadPoolExecutor` 并发执行
  - 每个结果都会调用 `_record_result()` 写入 `job_run_log`
  - 最终再按原始 `specs` 顺序排回去，避免并发打乱输出顺序

3. 两种运行模式入口

- `run_once(...)`
  - 用 `select_job_specs()` 先选出任务
  - 用 `ExecutionContext.for_as_of(as_of)` 生成上下文
  - 调用 `_run_grouped_jobs()`
- `run_backfill(...)`
  - 同样先选任务
  - 用 `_iter_calendar_days(start, end)` 逐天展开自然日
  - 每一天都构造一个 `ExecutionContext`
  - 用 `_should_run_spec_for_backfill_date(...)` 判断该 job 在这一天是否应该执行
    - `trade_day`：只在 `context.trade_date == current_date` 时运行
    - `calendar_day`：每天都运行
    - `manual`：回溯时不运行
  - 把当天可执行的任务交给 `_run_grouped_jobs()`

补充一点：`_record_result()` 虽然带下划线，但它被 `infrastructure.py` 复用，用于统一写运行日志。

### `infrastructure.py`

这个模块负责基础表同步，逻辑比 `runner.py` 更直接：

- `_build_infrastructure_fetch_kwargs(target_name, start, end)`
  - 目前只有 `trade_cal` 需要强制传入 `start_date` 和 `end_date`
  - 其他基础目标使用空参数
- `run_infrastructure(...)`
  - 用 `select_infrastructure_specs()` 先挑出要同步的 target
  - 为每个 target 实例化 fetcher 并执行 `fetch()`
  - 用 `_ensure_dataframe()` 统一返回值
  - 调用 `DatabaseWriter.write()` 写表
  - 复用 `runner._record_result()` 写运行日志
  - 返回 `list[JobRunResult]`

它和 `runner.py` 的差别在于：

- 不走 profile 分组
- 不走参数模板渲染
- 只处理 `InfrastructureSpec`
- 对 `trade_cal` 有额外的日期参数要求

## 调用关系

### 1. CLI 主链路

```text
main.py
  -> execution.__init__
    -> run_once() / run_backfill() / run_infrastructure()
```

说明：

- `main.py` 是真正的 CLI 入口
- `apps.data_hub.data_pipeline_ts` 包级导出直接来自 `execution`
- 测试 `tests/test_executor_module_boundaries.py` 明确约束了这种分层，避免逻辑重新长回顶层模块

### 2. `once` 模式

```text
main.py --mode once
  -> execution.run_once()
    -> selection.select_job_specs()
    -> ExecutionContext.for_as_of()
    -> runner._run_grouped_jobs()
      -> runner._run_single_job()
        -> rendering._render_params()
          -> ExecutionContext.render_value()
        -> spec.fetcher_cls().fetch(**resolved_params)
        -> rendering._ensure_dataframe()
        -> DatabaseWriter.write()
        -> runner._record_result()
          -> DatabaseWriter.record_run_result()
```

### 3. `backfill` 模式

```text
main.py --mode backfill
  -> execution.run_backfill()
    -> selection.select_job_specs()
    -> runner._iter_calendar_days()
    -> ExecutionContext.for_as_of() for each day
    -> runner._should_run_spec_for_backfill_date()
    -> runner._run_grouped_jobs()
      -> 后续执行路径与 run_once 基本一致
```

关键差异：

- `backfill` 先按自然日展开
- 每天会重新计算 `trade_date`
- 是否执行某个 job，要看它所属 profile 的 `backfill_mode`

### 4. `infrastructure` 模式

```text
main.py --mode infrastructure
  -> execution.run_infrastructure()
    -> selection.select_infrastructure_specs()
    -> infrastructure._build_infrastructure_fetch_kwargs()
    -> spec.fetcher_cls().fetch(**fetch_kwargs)
    -> rendering._ensure_dataframe()
    -> DatabaseWriter.write()
    -> runner._record_result()
      -> DatabaseWriter.record_run_result()
```

## 关键依赖

`execution/` 自己不维护业务元数据，主要依赖下面几个模块：

- `apps.data_hub.data_pipeline_ts.execution.context`
  - 提供 `ExecutionContext`
  - 负责把 `as_of_date` 转成 `trade_date`
  - 负责模板变量渲染
- `apps.data_hub.data_pipeline_ts.jobs.catalog`
  - 提供 `ALL_JOBS` 和 `INFRASTRUCTURE_TARGETS`
  - 是选择层的默认数据源
- `apps.data_hub.data_pipeline_ts.jobs.profiles`
  - 提供 `PROFILE_SPECS`
  - 决定 profile 是串行还是并行，以及 backfill 的运行语义
- `apps.data_hub.data_pipeline_ts.jobs.specs`
  - 定义 `JobSpec`、`InfrastructureSpec`、`JobRunResult`
- `apps.data_hub.data_pipeline_ts.execution.persistence`
  - 提供 `DatabaseWriter`
  - 负责建表、补列、按 scope 删除旧切片、写入新数据、记录 `job_run_log`

## 可以怎么理解这一层

如果按职责拆分，`execution/` 相当于一个很薄的 orchestration layer：

- `selection.py` 决定“跑谁”
- `rendering.py` 决定“参数长什么样”
- `runner.py` / `infrastructure.py` 决定“怎么跑”
- `execution/persistence.py` 决定“怎么落库和记日志”

因此这里最重要的不是业务规则本身，而是执行顺序和模块边界。
