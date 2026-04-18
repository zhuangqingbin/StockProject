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
- `close_to_low_120 = close_qfq / rolling_low_120`
- `vol_ma_3_prev = 前 3 日 vol 均值`
- `vol_ma_5_prev = 前 5 日 vol 均值`
- `volume_ratio_ma_3_prev = 前 3 日 volume_ratio 均值`
- `prev_volume_ratio = 前 1 日 volume_ratio`
- `volume_expand_ratio_3 = volume_ratio / volume_ratio_ma_3_prev`
- `turnover_rate_f_ma_3_prev = 前 3 日 turnover_rate_f 均值`
- `turnover_jump_3 = turnover_rate_f / turnover_rate_f_ma_3_prev`
- `amount_ma_5_prev = 前 5 日 amount 均值`
- `vol_spike_5 = vol / vol_ma_5_prev`
- `amount_spike_5 = amount / amount_ma_5_prev`

所有“前 N 日均值”都不包含当日，避免信号穿越。

## 信号定义

第一版不再把规则硬编码成少量固定组，而是采用“规则模板 + 阈值网格自动生成”的方式。这样脚本仍然只读一次数据库，但可以在本地批量生成几十组底部定义、几十组放量定义，再做组合回测。

默认配置建议生成：

- `18` 组底部定义
- `18` 组放量定义
- `324` 组组合结果

如果后续还想继续扩容，只需要给模板补阈值，不需要改主流程。

### 底部定义模板

#### `pos120` 低位模板

按 `pos120 <= threshold` 生成 5 组：

- `0.10`
- `0.15`
- `0.20`
- `0.25`
- `0.30`

示例编码：

- `B_pos120_le_10`
- `B_pos120_le_20`
- `B_pos120_le_30`

#### `near_120_low` 贴近阶段低点模板

按 `close_to_low_120 <= threshold` 生成 4 组：

- `1.03`
- `1.05`
- `1.08`
- `1.10`

示例编码：

- `B_near120_low_03`
- `B_near120_low_08`

#### `boll_rsi_oversold` 超跌模板

按 `close_qfq <= boll_lower_qfq * price_mult` 且 `rsi_qfq_6 < rsi_th` 生成 3 组：

- `(1.00, 30)`
- `(1.03, 35)`
- `(1.05, 40)`

示例编码：

- `B_boll_rsi_strict`
- `B_boll_rsi_medium`
- `B_boll_rsi_loose`

#### `below_ma_zone` 弱势均线模板

生成 3 组：

- `close_qfq < ma_qfq_20 and close_qfq < ma_qfq_60`
- `close_qfq < ma_qfq_20 and ma_qfq_20 < ma_qfq_60`
- `close_qfq < ma_qfq_60 and rsi_qfq_12 < 45`

示例编码：

- `B_below_ma_both`
- `B_below_ma_trend_weak`
- `B_below_ma60_rsi45`

#### `exhaustion` 衰竭低位模板

按 `downdays >= d` 且 `rsi_qfq_6 < r` 生成 3 组：

- `(3, 40)`
- `(4, 35)`
- `(5, 30)`

示例编码：

- `B_exhaustion_d3_r40`
- `B_exhaustion_d5_r30`

底部模板合计：`5 + 4 + 3 + 3 + 3 = 18` 组。

### 放量启动模板

#### `volume_ratio` 绝对量比模板

按 `volume_ratio > threshold` 生成 4 组：

- `1.20`
- `1.50`
- `1.80`
- `2.00`

示例编码：

- `V_vr_gt_12`
- `V_vr_gt_15`
- `V_vr_gt_20`

#### `shrink_to_expand` 缩量转放量模板

按 `volume_ratio > now_th` 且 `volume_ratio_ma_3_prev <= prev_th` 生成 3 组：

- `(1.20, 0.80)`
- `(1.50, 1.00)`
- `(1.80, 1.20)`

示例编码：

- `V_shrink_expand_strict`
- `V_shrink_expand_medium`
- `V_shrink_expand_loose`

#### `vol_spike_5` 原始成交量跳升模板

按 `vol_spike_5 >= threshold` 生成 3 组：

- `1.30`
- `1.50`
- `1.80`

示例编码：

- `V_vol_spike5_13`
- `V_vol_spike5_18`

#### `turnover_jump` 换手跳升模板

按 `turnover_rate_f > min_turnover` 且 `turnover_jump_3 >= jump_th` 生成 3 组：

- `(1.5, 1.30)`
- `(2.0, 1.50)`
- `(3.0, 2.00)`

示例编码：

- `V_turnover_jump_15_13`
- `V_turnover_jump_30_20`

#### `amount_spike_5` 成交额跳升模板

按 `amount_spike_5 >= threshold` 生成 3 组：

- `1.30`
- `1.50`
- `2.00`

示例编码：

- `V_amount_spike5_13`
- `V_amount_spike5_20`

#### `consecutive_expand` 连续放量模板

生成 2 组：

- `volume_ratio > 1.20 and prev_volume_ratio > 1.00`
- `volume_ratio > 1.50 and prev_volume_ratio > 1.20`

示例编码：

- `V_consecutive_expand_loose`
- `V_consecutive_expand_strict`

放量模板合计：`4 + 3 + 3 + 3 + 3 + 2 = 18` 组。

### 组合方式

执行 `底部定义 x 放量定义` 的全组合矩阵，默认共 `324` 组：

- `signal = bottom_mask & volume_mask`

每条结果保留：

- `bottom_family`
- `bottom_code`
- `volume_family`
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
- 终端默认只展示 `top_n`，完整结果全部写入文件

## 输出形式

### 终端输出

脚本运行后打印：

- 回测区间
- 股票样本总行数
- 可用于 `ret_1d` / `ret_3d` 的有效样本数
- 各模板家族生成的规则数量
- Top N 组合
- 分 `bottom_family` 的最佳组合
- 分 `volume_family` 的最佳组合
- 样本量不足但收益显著的组合提醒

### 落盘文件

建议输出到：

- `analysis/output/bottom_volume_matrix_summary.csv`
- `analysis/output/bottom_volume_matrix_summary.md`
- `analysis/output/bottom_volume_matrix_bottom_family_summary.csv`
- `analysis/output/bottom_volume_matrix_volume_family_summary.csv`
- `analysis/output/bottom_volume_matrix_triggers.csv`

其中：

- `summary.csv` 保存完整组合统计
- `summary.md` 便于直接阅读
- `bottom_family_summary.csv` 汇总每个底部模板家族的最优组合
- `volume_family_summary.csv` 汇总每个放量模板家族的最优组合
- `triggers.csv` 保存命中的逐条明细，便于后续复盘

## 命令行参数

建议支持：

- `--start-date`
- `--end-date`
- `--min-sample`
- `--top-n`
- `--bottom-mode`
- `--volume-mode`
- `--output-dir`

默认行为：

- 若未传日期，则默认从 `20180101` 分析到库中最新交易日
- `--bottom-mode all`，即启用全部底部模板
- `--volume-mode all`，即启用全部放量模板
- 若未传输出目录，则落到 `analysis/output`

## 实现结构

脚本内部建议拆成以下函数，保持清晰但不额外抽象成新模块：

- `load_base_frame(...)`
- `build_features(...)`
- `build_bottom_rule_defs(...)`
- `build_volume_rule_defs(...)`
- `build_bottom_masks(...)`
- `build_volume_masks(...)`
- `summarize_signal_matrix(...)`
- `write_outputs(...)`
- `main()`

信号定义采用模板配置：

```python
BOTTOM_RULE_TEMPLATES = [
    {
        "family": "pos120",
        "thresholds": [0.10, 0.15, 0.20, 0.25, 0.30],
        "builder": build_pos120_rules,
    },
]
```

这样后续新增规则只改模板参数，不改主流程。

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
- 同时输出 `bottom_family` / `volume_family` 维度汇总，避免只看单条组合

### 风险 2：小样本导致均值失真

处理：

- 默认最小样本阈值
- 同时展示均值、中位数、胜率，避免只看均值
- 终端只展示 Top N，全量矩阵交给文件，避免人工误读长尾噪声

### 风险 3：滚动窗口引入前视偏差

处理：

- 所有滚动特征严格只用当日及历史数据
- 所有前 N 日均值特征使用 shift 后再 rolling

## 推荐结论

推荐按这个设计实现第一版：

- 单脚本
- 主表直查
- 基于模板自动生成 18 组底部定义
- 基于模板自动生成 18 组放量定义
- 324 组组合一次性评估
- 终端摘要 + CSV/Markdown 明细双输出

这样能最快得到一版可解释、可扩展、可复盘的研究结果，并且后续要继续加定义组时不会破坏已有结构。
