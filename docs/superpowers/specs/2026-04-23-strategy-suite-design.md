# Strategy Suite Runner Design

## Goal

新增一个统一的策略调度入口，把当前已经稳定的矩阵脚本通过一个总脚本串起来执行。

第一版目标不是替代各策略脚本，而是在保留每个子策略独立执行能力的前提下，补一个统一的 suite 入口，支持：

- 一次性运行多个策略
- 统一传递日期和统计参数
- 汇总每个策略的执行状态
- 汇总所有成功策略的主结果表
- 生成 suite 级别的总览输出

第一版默认串行执行，但结构上要为后续并行执行预留清晰边界。

## Directory And Entry Points

新增两个文件：

- `apps/data_hub/data_pipeline_ts/analysis/strategy_registry.py`
- `apps/data_hub/data_pipeline_ts/analysis/run_strategy_suite.py`

其中：

`strategy_registry.py`

- 只负责维护稳定策略注册表
- 不负责执行、不负责汇总、不负责 CLI

`run_strategy_suite.py`

- 负责统一 CLI
- 负责选择策略集合
- 负责创建 suite 输出目录
- 负责逐个加载并执行策略
- 负责捕获错误并继续执行后续策略
- 负责生成 suite 级别输出文件

第一版不新增自动发现逻辑，不扫描目录，不做插件系统。

## Registered Strategies

第一版固定注册以下 5 个已稳定脚本：

- `bottom_volume_matrix`
- `flow_chip_northbound_matrix`
- `limit_inst_matrix`
- `supply_shock_matrix`
- `top_list_matrix`

### Registry Fields

注册表每个策略至少包含：

- `strategy_name`
- `strategy_description`
- `module_path`

建议结构示意：

```python
STRATEGY_REGISTRY = {
    "bottom_volume_matrix": {
        "strategy_name": "bottom_volume_matrix",
        "strategy_description": "底部放量策略矩阵",
        "module_path": "apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix",
    },
    "limit_inst_matrix": {
        "strategy_name": "limit_inst_matrix",
        "strategy_description": "涨跌停 + 龙虎榜事件矩阵",
        "module_path": "apps.data_hub.data_pipeline_ts.analysis.event_price_action_strategies.limit_inst_matrix",
    },
}
```

### Invalid Strategy Handling

如果用户通过 `--strategies` 传入不存在的策略名：

- 立即报错退出
- 不进入执行阶段
- 不写 suite 输出文件

第一版不支持忽略无效项，也不把无效项写入 `suite_summary.csv`。

## Execution Model

第一版采用：

- 固定注册表
- `import` 模块
- 直接调用模块内的 `run_analysis()`
- 默认串行执行

### Why Import Instead Of Subprocess

第一版选择 `import + run_analysis()`，原因是：

- 现有矩阵脚本已经基本统一了 `run_analysis()` 接口
- 可以直接获取返回值做汇总，不需要再读回子进程输出
- 错误处理更清晰
- 不需要额外处理 subprocess 的 stdout / stderr / exit code 协议

第一版不做 subprocess 调度。

### Parallelism Preparation

第一版虽然只做串行执行，但执行层需要保持一个清晰边界：

- 解析并校验策略集合
- 单策略执行函数
- suite 汇总函数

这样第二版如果要加并行执行，只替换调度层，不需要修改各策略脚本。

## Required Strategy Interface

被注册到 suite 中的策略模块，需要暴露：

- `STRATEGY_NAME`
- `STRATEGY_DESCRIPTION`
- `run_analysis(start_date, end_date, min_sample, top_n, output_dir, show_progress)`

第一版 `run_analysis()` 调用参数统一为：

- `start_date`
- `end_date`
- `min_sample`
- `top_n`
- `output_dir`
- `show_progress`

Suite 统一把这组参数广播给所有子策略，不支持按策略单独覆盖参数。

## CLI Contract

`run_strategy_suite.py` 第一版支持以下参数：

- `--start-date`
  - 默认 `20180101`
- `--end-date`
  - 可选，不传表示统计到数据库最新交易日
- `--strategies`
  - 可选，逗号分隔
  - 不传表示执行注册表内全部策略
- `--min-sample`
  - 默认 `30`
- `--top-n`
  - 默认 `20`
- `--output-dir`
  - 可选
  - 不传时使用 suite 默认输出目录

### Strategy Selection Rules

如果不传 `--strategies`：

- 执行全部已注册策略

如果传入 `--strategies bottom_volume_matrix,limit_inst_matrix`：

- 只执行这两个策略
- 执行顺序按用户输入顺序保留

第一版不支持通配符，不支持分组名，不支持 `all` 之外的特殊别名。

## Output Directory Layout

第一版统一输出到：

- `apps/data_hub/data_pipeline_ts/analysis/outputs/strategy_suite/mmdd_hhmm/`

如果显式传入 `--output-dir`，则以传入目录为根。

### Suite-Level Files

suite 根目录下生成：

- `suite_summary.csv`
- `suite_compact_ranking.csv`
- `suite_compact_by_strategy.csv`

### Per-Strategy Subdirectories

每个子策略单独一个目录：

- `bottom_volume_matrix/`
- `flow_chip_northbound_matrix/`
- `limit_inst_matrix/`
- `supply_shock_matrix/`
- `top_list_matrix/`

每个子目录交给对应子策略自己写入：

- `mmdd_hhmm.csv`
- `mmdd_hhmm.md`

也就是说，suite 不重写子策略输出格式，只负责把子策略的 `output_dir` 指到自己的子目录。

## Suite Output Contract

### `suite_summary.csv`

每个策略一行，至少包含：

- `strategy_name`
- `strategy_description`
- `status`
- `rows`
- `summary_csv`
- `summary_md`
- `elapsed_seconds`
- `error_message`

字段含义：

`status`

- `success`
- `failed`

`rows`

- 成功时取子策略 `compact_df` 的行数
- 失败时记为 `0`

`summary_csv`

- 成功时写子策略输出的主 `csv` 路径
- 失败时留空

`summary_md`

- 成功时写子策略输出的主 `md` 路径
- 失败时留空

`error_message`

- 成功时留空
- 失败时写一行错误摘要

### `suite_compact_ranking.csv`

把所有成功且 `rows > 0` 的子策略主结果表纵向合并。

需要补充以下列：

- `strategy_name`
- `strategy_description`

排序规则：

1. `win_rate_1d` 降序
2. `avg_ret_1d` 降序
3. `win_rate_3d` 降序
4. `avg_ret_3d` 降序
5. `sample_count` 降序

这份文件只保留成功且有结果的策略行：

- `status = success`
- `rows > 0`

失败策略和空结果策略不进入这份表。

### `suite_compact_by_strategy.csv`

也是所有成功且 `rows > 0` 的子策略主结果表纵向合并，但排序口径不同：

1. `strategy_name` 升序
2. `win_rate_1d` 降序
3. `avg_ret_1d` 降序
4. `win_rate_3d` 降序
5. `avg_ret_3d` 降序

这份文件用于按策略分组查看各策略内部表现最好的 `signal_code`。

## Failure Handling

第一版采用“失败继续跑”策略：

- 某个策略执行失败
- 记录失败摘要
- 继续执行后续策略

### Failure Summary

失败时，`suite_summary.csv` 中：

- `status = failed`
- `rows = 0`
- `summary_csv = ""`
- `summary_md = ""`
- `error_message = "<ExceptionType>: <message>"`

例如：

- `ValueError: unknown strategy foo`
- `OperationalError: table stock_top_list not found`

第一版不把完整 traceback 写入 CSV。

终端中允许正常打印 Python 异常信息，但 suite 汇总层只保存一行摘要。

## Console Output

第一版采用“总控日志 + 子脚本完整输出”混合模式。

### Suite Context

启动时先打印：

- `suite = strategy_suite`
- `requested_date_range = 20240101 -> latest`
- `strategies = bottom_volume_matrix,limit_inst_matrix`
- `output_dir = apps/data_hub/data_pipeline_ts/analysis/outputs/strategy_suite/0423_1030`

### Per-Strategy Logs

每个策略执行前打印：

- `==> running strategy = <strategy_name>`

执行期间：

- 保留子策略自己的 stdout 输出
- 保留子策略自己的进度条输出

执行结束后打印：

- 成功：
  - `==> done strategy = <strategy_name> | status = success | rows = <n> | elapsed = <seconds>s`
- 失败：
  - `==> failed strategy = <strategy_name> | error = <summary>`

### Suite Summary

全部策略结束后打印：

- 成功策略数
- 失败策略数
- suite 根输出目录

## Data And Result Expectations

这个 suite 脚本不直接查询数据库，也不自己做特征工程。

第一版只做 orchestration：

- 参数广播
- 输出目录组织
- 状态汇总
- 结果合并

具体的数据读取和计算仍然由各子策略脚本完成。

这保证：

- 子策略依旧可单独运行
- suite 只是薄调度层
- 不会把多个策略的业务逻辑重新混进一个大文件

## Testing Expectations

第一版需要至少覆盖以下测试点：

- 注册表内容和策略选择逻辑
- `--strategies` 无效名称时报错
- 单个策略成功时，summary 行正确
- 单个策略失败时，summary 行正确且不阻断后续策略
- 多策略执行后，`suite_compact_ranking.csv` 和 `suite_compact_by_strategy.csv` 正确生成
- 自定义 `--output-dir` 时，suite 根目录和子策略目录路径正确

另外需要有一个真实 smoke run：

- 选少量已稳定策略
- 用短日期区间执行
- 验证 suite 输出目录和 3 份总文件真实落盘

## Non-Goals

第一版明确不做：

- 自动发现策略目录
- subprocess 调度
- 多进程并行
- 按策略单独覆盖参数
- 将失败 traceback 持久化到 CSV
- 统一改造所有旧脚本的内部实现

这些都属于后续可扩展项，不进入第一版范围。
