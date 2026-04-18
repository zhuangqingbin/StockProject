# 底部放量策略紧凑输出设计

## 背景

现有 `bottom_volume_matrix.py` 已经可以基于主表 `stock_stk_factor_pro` 生成底部放量组合策略，并输出多份中间结果文件。但当前输出过多，且不符合本轮分析需求。

这次改动的目标是把输出契约收敛为两份文件：

- 一份 `mmdd_hhmm.csv`
- 一份 `mmdd_hhmm.md`

其中 `csv` 直接给出策略表现排名与最新交易日命中股票集合，`md` 只负责解释策略编码含义。

## 目标与非目标

### 目标

- 继续只依赖 `stock_stk_factor_pro`
- 保持现有底部规则与放量规则生成逻辑
- 每行只保留一个唯一策略编码 `signal_code`
- 输出每个策略的样本数、1 日与 3 日收益/胜率/方差
- 输出最新交易日该策略命中的股票集合
- 落盘时只生成一份 `csv` 和一份 `md`

### 非目标

- 不引入新的数据表或实时接口
- 不新增前端页面
- 不输出 family 汇总、trigger 明细、latest hits 明细等额外文件
- 不改单策略定义数量和阈值网格

## 现有实现保持不变的部分

以下能力继续沿用当前脚本：

- 数据源：`stock_stk_factor_pro`
- 收益口径：`close_qfq`
- 特征工程：
  - `ret_1d`
  - `ret_3d`
  - `rolling_low_120`
  - `rolling_high_120`
  - `pos120`
  - `close_to_low_120`
  - 量能、换手、成交额相关前置均值与跳升指标
- 规则生成：
  - `18` 组底部规则
  - `18` 组放量规则
  - 共 `324` 组 `signal_code = bottom_code__volume_code`

## 输出方案

### 方案对比

#### 方案 A：只调整落盘层

- 内部仍然保留 `summary_df`、`trigger_df` 等中间数据结构
- 仅在最终输出前合成一张紧凑汇总表
- 只把这张汇总表写入 `csv`
- 只把策略编码释义写入 `md`

优点：

- 复用现有计算链路最多
- 改动面最小
- 回归风险最低

缺点：

- 内部仍有部分不再对外暴露的中间结构

#### 方案 B：彻底改成单表驱动

- 删除原有 ranking/latest hits/family summary 概念
- 所有处理都围绕最终单表组织

优点：

- 结构更纯粹

缺点：

- 重构范围偏大
- 容易引入回归

#### 方案 C：增加输出模式参数

- 支持 `compact/full`

优点：

- 灵活

缺点：

- 复杂度增加
- 当前需求明确只要紧凑版，额外模式没有必要

### 采用方案

采用 `方案 A：只调整落盘层`。

## CSV 输出定义

`csv` 文件名格式：

- `mmdd_hhmm.csv`

每行代表一个唯一 `signal_code`，列固定为：

- `signal_code`
- `sample_count`
- `win_rate_1d`
- `avg_ret_1d`
- `var_ret_1d`
- `win_rate_3d`
- `avg_ret_3d`
- `var_ret_3d`
- `latest_trade_date`
- `latest_hit_stocks`

列含义：

- `signal_code`
  - 组合策略唯一编码
  - 格式：`bottom_code__volume_code`
- `sample_count`
  - 历史上该策略触发的样本数
- `win_rate_1d`
  - `ret_1d > 0` 的占比
- `avg_ret_1d`
  - `ret_1d` 的均值
- `var_ret_1d`
  - `ret_1d` 的样本方差
- `win_rate_3d`
  - `ret_3d > 0` 的占比
- `avg_ret_3d`
  - `ret_3d` 的均值
- `var_ret_3d`
  - `ret_3d` 的样本方差
- `latest_trade_date`
  - 分析样本里的最新交易日
  - 该列在整张表中是统一日期
- `latest_hit_stocks`
  - 在 `latest_trade_date` 当天触发该策略的 `ts_code` 集合
  - 多个股票用英文逗号拼接
  - 若当日未触发则为空字符串

### 排序规则

`csv` 按如下优先级排序：

1. `win_rate_1d` 降序
2. `avg_ret_1d` 降序
3. `win_rate_3d` 降序
4. `avg_ret_3d` 降序
5. `sample_count` 降序
6. `signal_code` 升序

## MD 输出定义

`md` 文件名格式：

- `mmdd_hhmm.md`

文件内容只用于解释策略编码，不再输出排行榜表格。

建议结构：

## Signal Codes

- `B_pos120_le_10__V_vr_gt_15`
  - 底部规则：`pos120` 家族，收盘价位于 120 日区间位置 `<= 0.10`
  - 放量规则：`volume_ratio` 家族，当日量比 `> 1.50`
- `B_boll_rsi_medium__V_shrink_expand_medium`
  - 底部规则：布林下轨附近且 RSI 超跌
  - 放量规则：前 3 日缩量后当日重新放量

文档应覆盖全部生成出来的 `signal_code`，每个 code 一条说明。

## 最新交易日命中集合口径

最新交易日定义为：

- `analysis_df["trade_date"].max()`

不是“每个策略最近一次触发日”，也不是“数据库全局最新日但忽略 `end_date`”。

当脚本传入 `--end-date` 时：

- 统计样本仍然只使用 `trade_date <= end_date`
- `latest_trade_date` 也以这个截断后的分析样本为准

这样用户看到的“最新这个交易日触发的股票集合”始终和本次分析区间一致。

## 代码层设计

### 保留的函数

- `build_features()`
- `build_bottom_rule_defs()`
- `build_volume_rule_defs()`
- `summarize_signal_matrix()`
- `load_base_frame()`
- `run_analysis()`

### 需要新增或重写的函数

#### `build_compact_summary(summary_df, trigger_df) -> pd.DataFrame`

职责：

- 基于现有 `summary_df` 补充 `var_ret_1d` 和 `var_ret_3d`
- 从 `trigger_df` 中提取最新交易日命中股票集合
- 合成最终落盘用的紧凑汇总表
- 执行最终排序

建议实现：

1. 先从 `trigger_df` 计算每个 `signal_code` 的 `ret_1d` / `ret_3d` 方差
2. 取 `latest_trade_date = trigger_df["trade_date"].max()`
3. 过滤出该日期的触发行
4. 对每个 `signal_code` 聚合 `ts_code`
   - 去重
   - 排序
   - 用逗号拼接
5. 回填到 `summary_df`
6. 为未命中的策略填充空字符串
7. 输出固定列顺序

#### `build_signal_code_markdown(bottom_rules, volume_rules) -> str`

职责：

- 为全部 `signal_code` 生成说明文档
- 根据 `RuleDef.description` 组合出可读描述

建议实现：

- 遍历全部底部规则和放量规则
- 生成 `signal_code`
- 生成两段释义：
  - 底部规则含义
  - 放量规则含义
- 以 Markdown 列表落盘

### 需要删除的对外输出

脚本不再写出以下文件：

- `*_bottom_family.csv`
- `*_volume_family.csv`
- `*_triggers.csv`
- `*_strategy_ranking.csv`
- `*_latest_hits.csv`

对应地，`write_outputs()` 的返回值也只保留：

- `summary_csv`
- `summary_md`

## 统计口径

### 收益定义

- `ret_1d = close_qfq[t+1] / close_qfq[t] - 1`
- `ret_3d = close_qfq[t+3] / close_qfq[t] - 1`

### 胜率定义

- `win_rate_1d = mean(ret_1d > 0)`
- `win_rate_3d = mean(ret_3d > 0)`

### 方差定义

- `var_ret_1d = ret_1d` 的样本方差
- `var_ret_3d = ret_3d` 的样本方差

若有效样本数不足 2 条，方差允许为 `NaN`。

## 测试设计

需要更新或新增的测试点：

1. `build_compact_summary()`：
   - 能输出固定列
   - 能按最新交易日拼接股票集合
   - 能生成 `var_ret_1d` / `var_ret_3d`
   - 能按 `win_rate_1d`、`avg_ret_1d` 降序排序
2. `write_outputs()`：
   - 只创建 `mmdd_hhmm.csv` 和 `mmdd_hhmm.md`
   - 不再断言其他 `csv` 存在
3. `run_analysis()`：
   - 返回的结果对象中包含新的紧凑汇总表
   - 输出路径只有两项
4. `md` 内容：
   - 包含 `signal_code`
   - 包含底部与放量规则解释文本

## 风险与处理

### 风险 1：方差列全是空

原因：

- 某些策略命中数过少

处理：

- 接受 `NaN`
- 不因为方差为空而丢弃策略

### 风险 2：最新交易日没有任何策略命中

处理：

- `latest_trade_date` 仍写入统一最新日期
- `latest_hit_stocks` 全部为空字符串

### 风险 3：股票集合顺序不稳定

处理：

- 聚合前对 `ts_code` 去重并排序

## 实施边界

这次实现只改：

- `apps/data_hub/data_pipeline_ts/analysis/bottom_val_strategies/bottom_volume_matrix.py`
- `apps/data_hub/data_pipeline_ts/tests/test_bottom_volume_matrix.py`

不触碰其他分析脚本，不改数据库结构，不改 CLI 参数语义。
