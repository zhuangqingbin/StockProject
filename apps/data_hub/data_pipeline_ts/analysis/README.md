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
- `bottom_val_strategies`：底部价值型策略集合与组合分析。
- `chip_distribution`：筹码分布与赢家率分析。
- `cross_factor`：跨因子组合、信号统计与筛选分析。
- `earnings`：业绩预告、快报与盈利变化分析。
- `holder_number`：股东户数变化与筹码集中度分析。
- `holdertrade`：股东交易行为与增减持分析。
- `limit_board`：涨跌停板、首板与连板信号分析。
- `margin`：融资融券相关信号和统计分析。
- `money_flow`：资金流向和主力净流入分析。
- `northbound`：北向资金持股与变动分析。
- `share_float`：解禁、流通盘变化与筹码扰动分析。
