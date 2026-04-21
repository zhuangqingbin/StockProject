# Analysis

`analysis/` 是基于数据库历史数据做分析和研究的脚本目录，主要承载历史分析、信号扫描、分层统计和结果汇总。

## 目录规范

以后 `analysis/` 下每个文件夹都是一个策略大类，通常可以包含一个或多个脚本，以及按结果目录命名约定使用的 `output/` / `outputs/` 和相关 helper modules。

新的策略应继续放进各自独立的文件夹中，不要再持续增加新的顶层脚本。

## 当前目录现状

当前的 `analysis/` 同时包含策略目录和少量顶层历史/通用入口脚本，整体处于过渡状态；其中 `common/` 和 `daily_output/` 这类非策略支持/输出目录也在当前目录结构中。

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
- `share_float`：解禁、流通盘变化与筹码扰动分析。

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
