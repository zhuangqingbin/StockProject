# 底部放量信号矩阵分析设计

## 背景

目标是在 `apps/data_hub/data_pipeline_ts` 中新增一个单独的 Python 分析脚本，只使用主表 `stock_stk_factor_pro`，批量评估“底部开始放量”股票在信号当日后的次日和第 3 个交易日收益表现。

这次不预设唯一正确口径，而是同时定义多组“底部”条件和多组“放量启动”条件，做笛卡尔组合后统一输出结果，避免因为先验定义过强而错过有效区间。

## 目标与非目标

### 目标

- 只依赖 `stock_stk_factor_pro`
- 单脚本执行，一次性输出全部定义组组合结果
- 统一使用前复权价格 `close_qfq`
- 输出次日收益和第 3 个交易日收益
- 输出每组组合的样本数、均值、中位数、胜率
- 保留可扩展配置，后续可继续增加定义组

### 非目标

- 不接入 TuShare/AkShare 实时接口
- 不依赖 `stock_daily`、`stock_daily_basic` 或其他侧表
- 第一版不做机器学习排序，不做复杂打分模型
- 第一版不做前端展示，只做命令行和文件输出

## 单脚本方案

建议新增脚本：

- `analysis/bottom_volume_matrix.py`

脚本职责：

1. 从 `stock_stk_factor_pro` 查询所需列
2. 在 pandas 内计算滚动底部位置和放量特征
3. 定义多组底部条件和多组放量条件
4. 对全部组合做信号筛选和收益统计
5. 输出终端摘要和落盘文件

## 数据来源与字段

查询字段仅来自主表：

- 标识字段：`ts_code`, `trade_date`
- 价格字段：`open_qfq`, `high_qfq`, `low_qfq`, `close_qfq`
- 日线字段：`pct_chg`, `vol`, `amount`
- 量能字段：`turnover_rate`, `turnover_rate_f`, `volume_ratio`
- 技术字段：`boll_lower_qfq`, `boll_mid_qfq`, `boll_upper_qfq`, `rsi_qfq_6`, `rsi_qfq_12`, `ma_qfq_20`, `ma_qfq_60`, `downdays`, `updays`

注意：

- 主表没有现成的 `rolling_low_120` / `rolling_high_120` 字段，脚本需要基于 `low_qfq`、`high_qfq` 在股票维度自行滚动计算
- 所有收益口径都以 `close_qfq` 为准，不使用 `pre_close`

## 派生特征

脚本在按 `ts_code, trade_date` 排序后，按股票分组派生：

- `ret_1d = close_qfq[t+1] / close_qfq[t] - 1`
- `ret_3d = close_qfq[t+3] / close_qfq[t] - 1`
- `rolling_low_120 = 过去 120 个交易日 low_qfq 最小值`
- `rolling_high_120 = 过去 120 个交易日 high_qfq 最大值`
- `pos120 = (close_qfq - rolling_low_120) / (rolling_high_120 - rolling_low_120)`
- `vol_ma_3_prev = 前 3 日 vol 均值`
- `vol_ma_5_prev = 前 5 日 vol 均值`
- `volume_ratio_ma_3_prev = 前 3 日 volume_ratio 均值`
- `turnover_rate_f_ma_3_prev = 前 3 日 turnover_rate_f 均值`
- `vol_spike_5 = vol / vol_ma_5_prev`

所有“前 N 日均值”都不包含当日，避免信号穿越。

## 信号定义

第一版默认提供 5 组底部定义和 5 组放量定义。具体阈值集中写在脚本顶部字典中，后续直接加组即可。

### 底部定义组

- `B1_pos120_low`
  - `pos120 <= 0.20`
  - 表示股价位于过去 120 日区间底部 20% 以内

- `B2_near_120_low`
  - `close_qfq <= rolling_low_120 * 1.08`
  - 表示现价距离 120 日低点不超过 8%

- `B3_boll_rsi_oversold`
  - `close_qfq <= boll_lower_qfq * 1.03` 且 `rsi_qfq_6 < 35`
  - 表示短期技术超跌

- `B4_below_ma20_ma60`
  - `close_qfq < ma_qfq_20` 且 `close_qfq < ma_qfq_60`
  - 表示仍在中短期弱势区

- `B5_exhaustion_bottom`
  - `downdays >= 3` 且 `rsi_qfq_6 < 40`
  - 表示连续回落后的衰竭式低位

### 放量启动定义组

- `V1_volume_ratio_gt_1_5`
  - `volume_ratio > 1.5`

- `V2_turnover_gt_3`
  - `turnover_rate_f > 3`

- `V3_from_shrink_to_expand`
  - `volume_ratio > 1.5` 且 `volume_ratio_ma_3_prev <= 1.0`
  - 表示前期缩量后当日开始放量

- `V4_raw_vol_spike`
  - `vol_spike_5 >= 1.5`
  - 表示原始成交量明显高于前 5 日水平

- `V5_expand_with_positive_price`
  - `volume_ratio > 1.5` 且 `pct_chg > 0`
  - 表示放量伴随价格确认

### 组合方式

执行 `底部定义 x 放量定义` 的全组合矩阵，默认共 25 组：

- `signal = bottom_mask & volume_mask`

每条结果保留：

- `bottom_code`
- `volume_code`
- `signal_code`
- `sample_count`
- `avg_ret_1d`
- `median_ret_1d`
- `win_rate_1d`
- `avg_ret_3d`
- `median_ret_3d`
- `win_rate_3d`

## 数据过滤

基础过滤：

- `close_qfq` 非空
- `vol > 0`
- 未来 1 日或未来 3 日价格存在时才纳入对应收益统计

结果过滤：

- 默认增加 `min_sample` 参数，初始值建议为 `30`
- 摘要输出按 `avg_ret_3d` 或 `win_rate_3d` 降序展示，但不隐藏低样本组合，只单独标注

## 输出形式

### 终端输出

脚本运行后打印：

- 回测区间
- 股票样本总行数
- 可用于 `ret_1d` / `ret_3d` 的有效样本数
- 所有组合的摘要表
- Top 10 组合
- 样本量不足但收益显著的组合提醒

### 落盘文件

建议输出到：

- `analysis/output/bottom_volume_matrix_summary.csv`
- `analysis/output/bottom_volume_matrix_summary.md`
- `analysis/output/bottom_volume_matrix_triggers.csv`

其中：

- `summary.csv` 保存完整组合统计
- `summary.md` 便于直接阅读
- `triggers.csv` 保存命中的逐条明细，便于后续复盘

## 命令行参数

建议支持：

- `--start-date`
- `--end-date`
- `--min-sample`
- `--top-n`
- `--output-dir`

默认行为：

- 若未传日期，则默认从 `20180101` 分析到库中最新交易日
- 若未传输出目录，则落到 `analysis/output`

## 实现结构

脚本内部建议拆成以下函数，保持清晰但不额外抽象成新模块：

- `load_base_frame(...)`
- `build_features(...)`
- `build_bottom_masks(...)`
- `build_volume_masks(...)`
- `summarize_signal_matrix(...)`
- `write_outputs(...)`
- `main()`

信号定义采用字典配置：

```python
BOTTOM_RULES = {
    "B1_pos120_low": lambda df: df["pos120"] <= 0.20,
}
```

这样后续新增规则只改配置，不改主流程。

## 验证与测试

第一版至少补两类验证：

- 单元测试：用小样本 DataFrame 校验 `pos120`、`vol_spike_5`、`ret_1d`、`ret_3d` 计算没有穿越和错位
- 回归测试：用构造数据校验规则矩阵输出列完整、样本数正确、排序稳定

建议新增测试文件：

- `tests/test_bottom_volume_matrix.py`

## 风险与处理

### 风险 1：底部定义之间高度重叠

处理：

- 输出每组样本数
- 保留逐条命中明细，后续可分析组合重叠度

### 风险 2：小样本导致均值失真

处理：

- 默认最小样本阈值
- 同时展示均值、中位数、胜率，避免只看均值

### 风险 3：滚动窗口引入前视偏差

处理：

- 所有滚动特征严格只用当日及历史数据
- 所有前 N 日均值特征使用 shift 后再 rolling

## 推荐结论

推荐按这个设计实现第一版：

- 单脚本
- 主表直查
- 5 组底部定义
- 5 组放量定义
- 25 组组合一次性评估
- 终端摘要 + CSV/Markdown 明细双输出

这样能最快得到一版可解释、可扩展、可复盘的研究结果，并且后续要加定义组时不会破坏已有结构。
