# Analysis

`analysis/` 是基于数据库历史数据做分析和研究的脚本目录，主要承载历史分析、信号扫描、分层统计和结果汇总。

## 目录规范

以后 `analysis/` 下每个文件夹都是一个策略大类，通常可以包含一个或多个脚本，以及按结果目录命名约定使用的 `output/` / `outputs/` 和相关 helper modules。

新的策略应继续放进各自独立的文件夹中，不要再持续增加新的顶层脚本。

## 当前目录现状

当前的 `analysis/` 同时包含策略目录和少量顶层历史/通用入口脚本，整体处于过渡状态；其中 `common/` 和 `daily_output/` 这类非策略支持/输出目录也在当前目录结构中。`run_strategy_suite.py` 是当前统一批量执行多个矩阵脚本的总入口。

`daily_signal_scan.py` 仍然有效，但它属于这类历史/通用入口，不是新的组织方式。

## 当前已有策略目录

- `block_trade`：大宗交易相关信号和统计分析。
- `bottom_val_strategies`：聚焦底部放量、底部反转和底部相关策略研究。
- `chip_distribution`：筹码分布与赢家率分析。
- `cross_factor`：跨因子组合、信号统计与筛选分析。
- `earnings`：业绩预告、快报与盈利变化分析。
- `event_price_action_strategies`：涨跌停、炸板、跌停、龙虎榜事件与主表状态的矩阵分析。
- `holder_number`：股东户数变化与筹码集中度分析。
- `holdertrade`：股东交易行为与增减持分析。
- `limit_board`：涨跌停板、首板与连板信号分析。
- `margin`：融资融券相关信号和统计分析。
- `money_flow`：资金流向和主力净流入分析。
- `northbound`：北向资金持股与变动分析。
- `flow_chip_northbound_strategies`：资金流、筹码和北向资金联合矩阵分析。
- `supply_shock_strategies`：解禁、增减持、供给冲击与吸收修复矩阵分析。
- `share_float`：解禁、流通盘变化与筹码扰动分析。
- `top_list_strategies`：龙虎榜、机构净买卖、连续上榜与底部吸筹矩阵分析。

## 可直接执行的矩阵脚本

当前已经落地、可以直接从命令行执行的矩阵脚本有：

- `bottom_val_strategies/bottom_volume_matrix.py`：底部放量、底部反转和底部价值型信号矩阵。
- `flow_chip_northbound_strategies/flow_chip_northbound_matrix.py`：资金流、筹码和北向资金的联合矩阵。
- `event_price_action_strategies/limit_inst_matrix.py`：涨跌停、炸板、跌停与机构龙虎榜事件矩阵。
- `supply_shock_strategies/supply_shock_matrix.py`：解禁、增减持、供给压力与吸收修复矩阵。
- `top_list_strategies/top_list_matrix.py`：龙虎榜净买入延续、净卖出反抽和低位吸筹矩阵。

这些脚本有几个共性：

- 默认都以数据库中的 `stock_stk_factor_pro` 为主表，再按 `(ts_code, trade_date)` 关联各自需要的侧表。
- 都支持 `--start-date`、`--end-date`、`--min-sample`、`--top-n`、`--output-dir`。
- 运行时会先打印策略名、数据表和日期范围，再显示阶段日志与进度条。
- 结果默认写到各脚本目录下自己的 `outputs/`，文件名按 `mmdd_hhmm.csv` 和 `mmdd_hhmm.md` 生成。

## 统一批量执行

如果要把多个策略一次性串起来跑，使用顶层入口 `run_strategy_suite.py`。

以下命令请在仓库根目录执行。

推荐命令：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)"
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite --start-date 20240101
```

已进入正确虚拟环境时的简写：

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite --start-date 20240101
```

只跑部分策略时，可以显式传 `--strategies`：

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite \
  --start-date 20240101 \
  --strategies bottom_volume_matrix,limit_inst_matrix,top_list_matrix
```

当前 suite 注册的策略有：

- `bottom_volume_matrix`
- `flow_chip_northbound_matrix`
- `limit_inst_matrix`
- `supply_shock_matrix`
- `top_list_matrix`

常见参数说明：

- `--start-date`：统计起始日期，格式为 `YYYYMMDD`。
- `--end-date`：统计结束日期，格式为 `YYYYMMDD`；不传则默认到数据库最新交易日。
- `--strategies`：逗号分隔的策略名列表；不传则跑全部已注册策略。
- `--min-sample`：统一广播给所有子策略的最小样本阈值。
- `--top-n`：统一广播给所有子策略的终端摘要参数。
- `--output-dir`：suite 总输出目录；不传则默认输出到 `analysis/outputs/strategy_suite/mmdd_hhmm/`。

suite 会额外生成三份总表：

- `suite_summary.csv`：每个策略一行，记录执行状态、耗时、结果路径和错误摘要。
- `suite_compact_ranking.csv`：把所有成功且有结果的策略主结果表纵向合并后做全局排序。
- `suite_compact_by_strategy.csv`：同样是合并结果，但先按 `strategy_name` 分组再做组内排序。

## bottom_val_strategies

当前目录下的主脚本是 `bottom_val_strategies/bottom_volume_matrix.py`，主要用于底部放量、底部反转和底部相关策略研究。

这个脚本直接读取数据库中的 `stock_stk_factor_pro`，再把底部定义和成交量定义组合成唯一的 `signal_code`，用于做底部价值型信号的分组统计。

运行后会把以下结果写入带时间戳的 CSV / `outputs/`，作为主要结果产物：

- 样本数
- 1d / 3d 胜率
- 1d / 3d 平均收益
- 1d / 3d 方差
- 最新交易日命中的股票集合

执行时会显示进度条，结束后会打印 `summary_csv`、`summary_md` 和 `rows`。

常用命令：

以下命令请在仓库根目录执行。

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)"
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix \
  --start-date 20240101
```

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix --start-date 20240101
```

上面的短命令仅适用于已经进入正确的项目虚拟环境时。

常见参数说明：

- `--start-date`：统计起始日期，格式为 `YYYYMMDD`。
- `--end-date`：统计结束日期，格式为 `YYYYMMDD`。
- `--min-sample`：低样本判定阈值；低于该阈值的策略仍保留在结果中，不会被从 CSV 中过滤掉。
- `--top-n`：保留参数，当前未用于控制输出。
- `--output-dir`：结果文件输出目录。

输出文件说明：

- 结果默认输出到脚本本地的 `outputs/` 目录。
- `mmdd_hhmm.csv`：主结果文件；低样本策略会保留在其中。
- `mmdd_hhmm.md`：`signal_code` 的含义和定义说明指南。
