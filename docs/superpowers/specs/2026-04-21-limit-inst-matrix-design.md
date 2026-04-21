# Limit Inst Matrix Design

## Goal

新增一个和 `bottom_volume_matrix.py`、`flow_chip_northbound_matrix.py` 风格一致的可直接执行脚本，用于研究：

- 涨停 / 连板 / 一字板 / 炸板 / 跌停
- 龙虎榜机构净买入 / 净卖出
- 上述事件与主表状态信号的交叉效果

脚本需要一次性输出历史 `1d / 3d` 表现排名，以及最新交易日命中这些事件策略的股票集合。

## Directory And Entry Point

新增一个新的策略大类目录：

- `apps/data_hub/data_pipeline_ts/analysis/event_price_action_strategies/`

主脚本：

- `apps/data_hub/data_pipeline_ts/analysis/event_price_action_strategies/limit_inst_matrix.py`

这个脚本的执行方式、启动日志、进度条、输出文件命名，保持和现有矩阵脚本一致。

## Data Sources

主表：

- `stock_stk_factor_pro`

侧表：

- `stock_limit_list_d`
- `stock_top_inst`

统一按 `(ts_code, trade_date)` 左连接。

### Required Fields

`stock_stk_factor_pro` 至少读取：

- `ts_code`, `trade_date`
- `open_qfq`, `high_qfq`, `low_qfq`, `close_qfq`
- `pct_chg`, `vol`, `amount`, `turnover_rate_f`, `volume_ratio`
- `boll_lower_qfq`, `rsi_qfq_6`, `rsi_qfq_12`
- `ma_qfq_5`, `ma_qfq_20`, `ma_qfq_60`
- `downdays`, `updays`

`stock_limit_list_d` 至少读取：

- `ts_code`, `trade_date`
- ``limit`` as `limit_type`
- `open_times`
- `fd_amount`
- `limit_times`

`stock_top_inst` 需要先按 `(ts_code, trade_date)` 聚合：

- `inst_buy`
- `inst_sell`
- `inst_net_buy`

聚合方式沿用现有 `daily_signal_scan.py` 的口径：

- `SUM(CASE WHEN side = '0' THEN buy ELSE 0 END) AS inst_buy`
- `SUM(CASE WHEN side = '1' THEN sell ELSE 0 END) AS inst_sell`
- `SUM(net_buy) AS inst_net_buy`

## Research Shape

这类脚本不是单纯做“事件统计表”，而是做“事件模板 x 主表状态模板”的交叉矩阵。

统一采用：

- `plain_*`：只看事件本身
- `state_*`：事件叠加主表状态

同时覆盖两类研究目标：

- 强事件延续：追涨确认、强势延续
- 反转事件修复：炸板、跌停、机构净卖出后的修复机会

## Strategy Families

第一版包含 6 个策略家族：

- `plain_momentum_event`
- `state_momentum_event`
- `plain_reversal_event`
- `state_reversal_event`
- `plain_inst_event`
- `state_inst_event`

### Family Meanings

`plain_momentum_event`

- 强事件本身，不叠加主表状态
- 关注涨停、连板、一字板、龙虎榜净买入等事件后续表现

`state_momentum_event`

- 强事件叠加主表状态
- 关注低位、放量、强趋势、均线站回等状态是否改善强事件效果

`plain_reversal_event`

- 反转候选事件本身，不叠加主表状态
- 关注炸板、跌停、机构净卖出等事件后的修复表现

`state_reversal_event`

- 反转候选事件叠加主表状态
- 关注低位、超跌、强势回踩等状态是否提高反弹成功率

`plain_inst_event`

- 机构龙虎榜净买入 / 净卖出单独作为事件源

`state_inst_event`

- 机构龙虎榜事件与主表状态组合

## Event Templates

第一版事件模板按 3 组组织。

### Momentum Event Templates

- `limit_up_first`
  - `limit_type == 'U' and limit_times == 1`
- `limit_up_multi`
  - `limit_type == 'U' and limit_times >= 2`
- `limit_up_one_word`
  - `limit_type == 'U' and open_times == 0`
- `limit_up_open_board`
  - `limit_type == 'U' and open_times > 0`

### Reversal Event Templates

- `limit_down`
  - `limit_type == 'D'`
- `open_board_heavy`
  - `limit_type == 'U' and open_times >= 2`
- `open_board_fd_large`
  - `limit_type == 'U' and fd_amount` 高于阈值

### Institution Event Templates

- `inst_net_buy_pos`
  - `inst_net_buy > 0`
- `inst_net_buy_strong`
  - `inst_net_buy` 高于较强阈值
- `inst_net_sell_strong`
  - `inst_net_buy` 低于较强负阈值

### Threshold Grids

为了保证组合多样性，事件模板需要做适度阈值网格，而不是只保留一条固定规则。

建议阈值网格：

- `fd_amount >= {2e7, 5e7, 1e8}`
- `inst_net_buy >= {0, 2e7, 5e7, 1e8}`
- `inst_net_buy <= {-2e7, -5e7, -1e8}`
- `open_times >= {1, 2, 3}`
- `limit_times >= {1, 2, 3}`

## State Templates

第一版只用主表状态，不再叠加其他侧表，避免和 `flow_chip_northbound_matrix.py` 重叠过多。

### Recommended State Templates

- `bottom_zone`
  - 统一低位区定义，口径对齐现有脚本
- `oversold`
  - `close_qfq <= boll_lower_qfq * 1.03` and `rsi_qfq_6 < 35`
- `volume_expand`
  - `volume_ratio` 高于阈值
- `high_turnover`
  - `turnover_rate_f` 高于阈值
- `ma_reclaim`
  - `close_qfq >= ma_qfq_5` 且前一阶段处于均线下方
- `weak_trend`
  - `close_qfq < ma_qfq_20` and `close_qfq < ma_qfq_60`
- `strong_trend`
  - `close_qfq >= ma_qfq_20` and `ma_qfq_20 >= ma_qfq_60`
- `pullback_state`
  - 中期仍偏强，但短期回踩到 `ma_qfq_20` 一带

### Threshold Grids

建议状态模板也做有限阈值网格：

- `volume_ratio >= {1.2, 1.5, 2.0}`
- `turnover_rate_f >= {2, 4, 6}`
- `rsi_qfq_6 < {30, 35, 40}`
- `close_qfq >= ma_qfq_5 * {1.00, 1.01}`

## Signal Construction

### Unique Signal Code

每个策略必须对应唯一 `signal_code`。

建议命名结构：

- 纯事件：
  - `plain_momentum_event__limit_up_first`
  - `plain_inst_event__inst_net_buy_ge_5000w`
- 事件 + 状态：
  - `state_momentum_event__limit_up_first__bottom_zone`
  - `state_reversal_event__limit_down__oversold`
  - `state_inst_event__inst_net_sell_le_neg5000w__bottom_zone`

### Expansion Strategy

第一版采用模板化生成，不手写几十条固定策略。

预期规模：

- 事件模板基础规则：`20-40`
- 状态模板基础规则：`15-30`
- 交叉后总 `signal_code`：`120-300`

这个规模足够大，适合先做效果筛选，但仍保持可解释性。

## Feature Engineering

脚本内部需要补齐以下派生字段：

- `ret_1d`
- `ret_3d`
- `rolling_low_120`
- `rolling_high_120`
- `pos120`
- `close_to_low_120`
- `is_bottom_zone`

事件侧字段派生：

- `is_limit_up`
- `is_limit_down`
- `is_open_board`
- `is_one_word_board`
- `inst_net_buy`
- `inst_abs_buy_sell_ratio` 或同类标准化字段

这些字段只需要服务于本脚本的模板生成和统计，不需要额外产出 family summary 文件。

## Output Contract

沿用现有矩阵脚本的紧凑输出约定，只输出两份最终文件：

- `mmdd_hhmm.csv`
- `mmdd_hhmm.md`

### CSV Columns

主结果 `csv` 每行一个 `signal_code`，包含：

- `strategy_family`
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

排序规则：

1. `win_rate_1d` 降序
2. `avg_ret_1d` 降序
3. `win_rate_3d` 降序
4. `avg_ret_3d` 降序
5. `sample_count` 降序
6. `signal_code` 升序

### Markdown

`md` 文件只做 `signal_code` 说明，不重复输出大表。

建议格式：

- `signal_code`
- `strategy_family`
- 事件规则说明
- 状态规则说明

## CLI And Runtime Behavior

命令行参数保持和现有矩阵脚本一致：

- `--start-date`
- `--end-date`
- `--min-sample`
- `--top-n`
- `--output-dir`

启动时输出：

- `strategy = limit_inst_matrix`
- `description = 涨跌停 + 龙虎榜事件矩阵`
- `source_tables = stock_stk_factor_pro, stock_limit_list_d, stock_top_inst`
- `requested_date_range = ...`
- `output_dir = ...`
- `min_sample = ...`
- `top_n = ...`

阶段日志保持一致：

- `==> load_base_frame`
- `==> load_limit_frame`
- `==> load_top_inst_frame`
- `==> load_base_frame done | ...`
- `==> merge_side_frames`
- `==> build_features`
- `==> summarize_signal_matrix`
- `==> build_compact_summary`
- `==> build_signal_code_markdown`
- `==> write_outputs`

策略扫描阶段需要显示 `tqdm` 进度条。

## Testing

至少覆盖：

- CLI 输出契约
- 事件表 loader 和龙虎榜聚合口径
- 主表 + 事件表 merge
- 关键事件/状态派生字段
- `build_signal_rule_defs()` 生成足够数量且唯一的 `signal_code`
- `summarize_signal_matrix()` 输出列契约
- `write_outputs()` 写出带时间戳的 `csv` / `md`
- `run_analysis()` 端到端 compact contract
- `analysis/README.md` 新目录说明

## Non-Goals

第一版不做：

- 再叠加 `money_flow / cyq / hk_hold`
- 分年度分市场 regime 分层输出
- family summary / strategy ranking / latest_hits 的额外独立文件
- 实时行情或非数据库输入

这些留到该大类验证有效后再扩。
