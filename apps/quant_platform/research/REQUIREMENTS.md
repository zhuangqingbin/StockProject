# 因子研究与策略框架 — 需求文档

## 1. 项目目标

基于 `tushare_database` 中已有的 53 张数据表，系统性挖掘对 **A 股次日开盘价** 有预测能力的因子（单因子及组合因子），并将有效因子转化为可回测的交易策略。

**预测目标（Target）**：

```
overnight_return = (T+1日开盘价 - T日收盘价) / T日收盘价
```

**交易逻辑**：因子信号作为入场依据，出场条件灵活（止盈止损、反向信号、持仓时间限制等）。

---

## 2. 数据来源

直接读取 `tushare_database`（通过 `shared/stock_core/db.py`），不建独立缓存。数据由 `data_hub/data_pipeline_ts` 的每日 pipeline 维护更新。

研究主表统一以 `stock_stk_factor_pro` 作为日频行情、估值与技术指标基座；`stock_daily` 和 `stock_daily_basic` 已被其覆盖，不再作为独立研究数据源维护，避免重复 join 和口径不一致。

### 2.1 核心日频数据源

| 类别 | 表名 | 核心字段 | 主要用途 |
|------|------|----------|----------|
| 技术/行情主表 | `stock_stk_factor_pro` | OHLCV、复权价、换手、估值、市值、MA/EMA/MACD/KDJ/RSI/BOLL/ATR/OBV 等 | 日频主面板，绝大多数连续型因子的基座 |
| 个股资金流 | `stock_money_flow` | 大/中/小/特大单买卖额、`net_mf_amount` | 主力资金、散户/机构分歧 |
| 个股资金流(DC) | `stock_money_flow_dc` | `net_amount_rate`、超大/大/中/小单净流入占比 | 与 TuShare 口径交叉验证，增强资金结构信号 |
| 北向/南向市场资金 | `stock_money_flow_hsgt` | `north_money`、`south_money`、`hgt`、`sgt` | 市场级风险偏好与外资 regime |
| 大盘资金流(DC) | `stock_money_flow_mkt_dc` | 大盘主力净流入、大小单净流入占比 | 市场状态、顺/逆市场资金因子 |
| 筹码摘要 | `stock_cyq_perf` | `winner_rate`、`weight_avg`、成本分位 | 获利盘、平均成本、筹码集中度 |
| 筹码分布 | `stock_cyq_chips` | `price`、`percent` | 上方套牢、支撑密度、筹码峰结构 |
| 北向持仓明细 | `stock_hk_hold` | 持股数量、持股占比 | 外资持仓变化与拥挤度 |
| 中央结算持仓 | `stock_ccass_hold` | `shareholding`、`hold_nums`、`hold_ratio` | 持仓集中度、参与者扩散/收敛 |
| 两融明细 | `stock_margin_detail` | 融资余额/买入额/偿还额、融券余额/卖出量 | 杠杆资金多空行为 |
| 两融汇总 | `stock_margin` | 交易所级 `rzrqye`、`rzmre`、`rqmcl` | 市场级杠杆环境 |
| 涨跌停/炸板 | `stock_limit_list_d` | 连板数、封单金额、炸板次数 | 极端强弱、封板质量、情绪过热 |
| 龙虎榜 | `stock_top_list` | 净买入额、成交额占比、上榜原因 | 异动事件与席位强度 |
| 龙虎榜机构席位 | `stock_top_inst` | 机构买卖额、净买入额、占比 | 机构行为和席位质量 |
| 大宗交易 | `stock_block_trade` | 成交价、成交额、买卖营业部 | 折价/溢价成交与后续漂移 |
| 沪深股通十大成交 | `stock_hsgt_top10` | 排名、净成交额、买卖额 | 北向关注度与资金排名 |
| AH 比价 | `stock_stk_ah_comparison` | A/H 溢价相关字段 | 跨市场估值偏离和回归 |
| 涨跌停价 | `stock_stk_limit` | 涨停价、跌停价 | 回测可交易性约束 |
| 基础信息/交易日历 | `stock_basic`、`trade_cal` | 行业、上市日期、市场、交易日 | 股票池、行业归类、事件对齐 |
| 过滤辅助 | `stock_st`、`stock_suspend_d` | ST 状态、停复牌 | 股票池过滤和可交易性判断 |

### 2.2 扩展低频 / 事件数据源

| 类别 | 表名 | 对齐主键 | 主要用途 |
|------|------|----------|----------|
| 股东人数 | `stock_stk_holdernumber` | `ann_date` / `end_date` | 筹码分散/集中变化 |
| 股东增减持 | `stock_stk_holdertrade` | `ann_date` | 管理层/重要股东行为 |
| 回购公告 | `stock_repurchase` | `ann_date` | 资本运作与安全边际 |
| 解禁流通变动 | `stock_share_float` | `ann_date` / `float_date` | 解禁压力与供给冲击 |
| 质押统计 | `stock_pledge_stat` | `end_date` | 融资风险、脆弱性暴露 |
| 业绩预告 | `stock_forecast_vip` | `ann_date` | 预期差和业绩 surprise |
| 业绩快报 | `stock_express_vip` | `ann_date` | 确认式业绩事件与质量信号 |
| 财报披露计划 | `stock_disclosure_date` | 披露日期 | 临近财报窗口效应 |
| 卖方盈利预测 | `stock_report_rc` | `report_date` | 分析师预期、目标价与关注度 |
| 机构调研 | `stock_stk_surv` | `surv_date` | 机构关注热度与事件后漂移 |
| 财务指标 | `stock_fina_indicator_vip` | `ann_date` / `end_date` | 盈利质量、现金流质量、杠杆质量 |
| 财务报表 | `stock_income_vip`、`stock_balancesheet_vip`、`stock_cashflow_vip` | `ann_date` / `end_date` | 慢变量增强与财务核验 |
| 审计意见 | `stock_fina_audit` | `ann_date` | 财务可信度和风险过滤 |
| 股东结构 | `stock_top10_holders`、`stock_top10_floatholders` | `ann_date` / `end_date` | 股权集中度与锁仓程度 |

### 2.3 回测区间

**默认：2018-01-01 ~ 至今**，所有关键数据源（筹码、北向、涨跌停）在此区间均有覆盖。支持通过配置自定义。

### 2.4 股票池

可配置过滤器，默认规则：
- 排除 ST / *ST 股票（通过 `stock_st` 表判断）
- 排除上市不满 60 个交易日的次新股
- 排除当日停牌股票（通过 `stock_suspend_d` 判断）
- 支持按市值、行业、指数成分等自定义过滤

---

## 3. 目录结构

```
apps/quant_platform/research/
├── REQUIREMENTS.md              # 本文档
├── config.py                    # 研究配置（DB连接、默认参数、路径）
├── universe.py                  # 股票池过滤器
├── data_loader.py               # 多表数据加载器（含 available_lag / 事件对齐）
│
├── factor_engine/               # 因子工程
│   ├── __init__.py
│   ├── base.py                  # 因子基类、标准化管道
│   ├── technical.py             # 技术因子（stock_stk_factor_pro）
│   ├── money_flow.py            # 资金流因子
│   ├── chip.py                  # 筹码分布因子
│   ├── northbound.py            # 北向资金因子
│   ├── margin.py                # 两融因子
│   ├── limit.py                 # 涨跌停因子
│   ├── dragon.py                # 龙虎榜因子
│   ├── ownership.py             # 股东行为 / 资本运作因子
│   ├── event.py                 # 公告、业绩、卖方预期、调研因子
│   ├── fundamental.py           # 财务慢变量 / 质量因子
│   ├── cross_feature.py         # 特征交叉因子
│   ├── industry.py              # 行业维度因子
│   ├── market.py                # 市场情绪 / market regime / 跨股票关联因子
│   └── composite.py             # 组合因子合成
│
├── analyzer/                    # 因子分析
│   ├── __init__.py
│   ├── ic_analysis.py           # IC / Rank IC / IC_IR
│   ├── layered_backtest.py      # 分层回测（分5/10组）
│   ├── correlation.py           # 因子相关性矩阵
│   └── report.py                # 研究报告生成（CSV + 图片）
│
├── strategy/                    # 策略层
│   ├── __init__.py
│   ├── portfolio_backtest.py    # 向量化组合回测引擎（自建）
│   ├── backtest_config.py       # 回测配置（佣金、滑点、A股约束）
│   ├── signal_generator.py      # 因子 → 目标持仓权重
│   ├── exit_rules.py            # 出场规则（止盈止损等）
│   └── factor_strategy.py       # 策略封装（组合因子→信号→回测）
│
├── notebooks/                   # Jupyter Notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_single_factor_analysis.ipynb
│   ├── 03_factor_screening.ipynb
│   ├── 04_composite_factor.ipynb
│   └── 05_strategy_backtest.ipynb
│
├── scripts/                     # 命令行入口
│   ├── run_factor_research.py
│   ├── run_single_factor.py
│   └── run_strategy_backtest.py
│
└── output/                      # 研究产出（gitignore）
    ├── ic_reports/
    ├── layered_reports/
    ├── correlation_matrices/
    └── backtest_results/
```

---

## 4. 因子体系

### 4.1 第一层：基础因子（~120 个）

从单表直接提取或做轻量 join/归一化，分成三类统一管理：
- 直接 alpha 事件因子：更偏短期信息增量，如资金流、龙虎榜、回购、业绩预告、卖方预期；
- 慢变量增强因子：更偏中期质量和状态，如财务质量、股权结构、筹码分布；
- 风险过滤与暴露控制因子：如市值、杠杆、质押、解禁、行业和市场 regime。

#### 4.1.1 技术与估值因子（`technical.py`，来源：`stock_stk_factor_pro`）

统一使用**前复权（qfq）**口径，避免三种复权重复。

| 类别 | 因子 | 说明 |
|------|------|------|
| 动量 | `pct_chg`, `roc_qfq`, `mtm_qfq` | 当日涨跌幅和基础动量 |
| 均线结构 | `ma_spread_5_20`, `ma_spread_20_60`, `ema_spread_10_60` | 均线多空排列强度 |
| 趋势 | `macd_dif/dea/macd_qfq`, `dmi_pdi/mdi/adx/adxr_qfq`, `trix_qfq`, `cr_qfq` | 趋势方向和稳定性 |
| 波动 | `atr_pct = atr_qfq / close_qfq`, `boll_bandwidth` | 波动率与压缩/扩张状态 |
| 位置 | `close_to_ma_qfq_20`, `topdays`, `lowdays` | 价格相对均线/阶段高低点位置 |
| 量价 | `volume_ratio`, `turnover_rate_f`, `obv_qfq`, `mfi_qfq` | 成交活跃度和量价配合 |
| 超买超卖 | `rsi_qfq_6/12/24`, `kdj_k/d/j_qfq`, `wr_qfq`, `cci_qfq`, `psy_qfq` | 情绪极值与反转 |
| 乖离/拥挤 | `bias1/2/3_qfq` | 偏离均值程度 |
| 估值/市值 | `pe_ttm`, `pb`, `ps_ttm`, `dv_ttm`, `total_mv`, `circ_mv` | 风格暴露和风险控制变量 |

#### 4.1.2 个股资金流因子（`money_flow.py`，来源：`stock_money_flow`, `stock_money_flow_dc`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `net_mf_rate` | `net_mf_amount / amount` | 主力净流入占成交额比例 |
| `elg_net_ratio` | `(buy_elg_amount - sell_elg_amount) / amount` | 特大单净买入强度 |
| `lg_net_ratio` | `(buy_lg_amount - sell_lg_amount) / amount` | 大单净买入强度 |
| `retail_contra` | `[(buy_sm-sell_sm) - (buy_lg-sell_lg)] / amount` | 散户与大单背离 |
| `dc_main_strength` | `net_amount_rate` | 东方财富口径主力强度 |
| `dc_order_split` | `buy_elg_amount_rate - buy_sm_amount_rate` | 大资金 vs 小资金分歧 |
| `flow_consensus` | `sign(net_mf_amount) == sign(net_amount)` | 双口径资金方向一致性 |

#### 4.1.3 筹码结构因子（`chip.py`，来源：`stock_cyq_perf`, `stock_cyq_chips`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `winner_rate` | 原始值 | 获利盘比例 |
| `avg_cost_gap` | `close_qfq / weight_avg - 1` | 现价相对平均成本的距离 |
| `chip_width` | `(cost_95pct - cost_5pct) / weight_avg` | 筹码分散程度 |
| `chip_skew` | `[(cost_85-cost_50) - (cost_50-cost_15)] / weight_avg` | 上下方筹码不对称 |
| `upper_overhang` | `Σ percent(price > close_qfq)` | 上方套牢盘密度 |
| `support_density` | `Σ percent(abs(price/close_qfq - 1) <= 3%)` | 当前价附近支撑强度 |
| `dominant_peak_gap` | `(筹码主峰价格 - close_qfq) / close_qfq` | 成本峰与现价偏离 |

#### 4.1.4 北向 / 结算因子（`northbound.py`，来源：`stock_hk_hold`, `stock_hsgt_top10`, `stock_ccass_hold`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `hk_hold_ratio` | `ratio` | 外资持仓占比 |
| `hk_hold_chg` | 北向持股数量或占比变化率 | 外资增减仓趋势 |
| `hsgt_top10_flag` | 是否进入沪深股通前十大成交（0/1） | 北向关注度 |
| `hsgt_top10_net_ratio` | `net_amount / amount` | 北向成交净买入占比 |
| `ccass_hold_ratio` | `hold_ratio` | 中央结算口径持股占比 |
| `ccass_participant_chg` | `Δ hold_nums` | 参与者扩散或集中 |
| `north_attention_score` | 组合 `hk_hold_chg`、`hsgt_top10_flag`、`ccass_hold_ratio` | 外资关注综合强度 |

#### 4.1.5 两融因子（`margin.py`，来源：`stock_margin_detail`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `rzye_ratio` | `融资余额 / 流通市值` | 融资杠杆率 |
| `rzmre_intensity` | `融资买入额 / 成交额` | 杠杆资金主动买入强度 |
| `rqye_ratio` | `融券余额 / 流通市值` | 融券压力 |
| `margin_balance_chg` | `Δ (融资余额 - 融券余额)` | 杠杆多空变化 |

`stock_margin` 不直接做个股因子，而是进入 `market.py` 生成市场级杠杆 regime。

#### 4.1.6 盘后交易行为因子（`limit.py`, `dragon.py`，来源：`stock_limit_list_d`, `stock_top_list`, `stock_top_inst`, `stock_block_trade`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `limit_up_days` | 近 N 日涨停次数 | 强势程度 |
| `limit_down_days` | 近 N 日跌停次数 | 弱势程度 |
| `seal_amount_ratio` | `fd_amount / float_mv` | 封单质量 |
| `open_board_pressure` | `open_times / max(limit_times, 1)` | 炸板压力 |
| `top_list_net_rate` | `top_list.net_rate` | 龙虎榜净买入强度 |
| `inst_net_buy` | 聚合 `top_inst.net_buy` | 机构席位净买入额 |
| `inst_participation` | `Σ(top_inst.buy + top_inst.sell) / amount` | 机构参与度 |
| `block_discount` | `block_trade.price / close_qfq - 1` | 大宗折价/溢价 |
| `block_amount_ratio` | `block_trade.amount / daily_amount` | 大宗成交占全天成交比 |

#### 4.1.7 股东行为与资本运作因子（`ownership.py`，来源：`stock_stk_holdernumber`, `stock_stk_holdertrade`, `stock_repurchase`, `stock_share_float`, `stock_pledge_stat`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `holder_num_chg` | 股东户数环比变化 | 筹码分散/集中变化 |
| `insider_net_increase` | 增持事件 `Σ change_ratio (IN)` | 重要股东增持强度 |
| `insider_net_decrease` | 减持事件 `Σ change_ratio (DE)` | 重要股东减持压力 |
| `repurchase_amount_to_mv` | `回购金额 / 总市值` | 回购力度 |
| `repurchase_price_premium` | `回购价格上限 / close_qfq - 1` | 管理层隐含估值锚 |
| `unlock_ratio` | `float_ratio` | 解禁供给压力 |
| `pledge_ratio` | `pledge_ratio` | 质押风险暴露 |

#### 4.1.8 业绩 / 预期 / 调研事件因子（`event.py`，来源：`stock_forecast_vip`, `stock_express_vip`, `stock_report_rc`, `stock_disclosure_date`, `stock_stk_surv`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `forecast_surprise_mid` | `(p_change_min + p_change_max) / 2` | 业绩预告中枢 surprise |
| `turnaround_flag` | `type ∈ {扭亏, 首盈, 续盈}` | 盈利拐点事件 |
| `express_profit_yoy` | `yoy_dedu_np` 或 `yoy_eps` | 业绩快报确认强度 |
| `analyst_target_return` | `[(max_price + min_price)/2] / close_qfq - 1` | 卖方目标价空间 |
| `analyst_attention_20d` | 近 20 日研报数 / 机构数 | 卖方关注度 |
| `disclosure_countdown` | 下一次披露日距当前交易日的天数 | 财报窗口效应 |
| `survey_heat` | 近 20 日调研次数 | 机构调研热度 |

#### 4.1.9 财务质量与慢变量因子（`fundamental.py`，来源：`stock_fina_indicator_vip`, `stock_income_vip`, `stock_balancesheet_vip`, `stock_cashflow_vip`, `stock_fina_audit`）

| 因子 | 计算逻辑 | 说明 |
|------|---------|------|
| `q_roe` | 单季度净资产收益率 | 盈利质量 |
| `q_ocf_to_sales` | 单季度经营现金流 / 营业收入 | 现金流质量 |
| `gross_margin` | 原始值 | 护城河和盈利结构 |
| `debt_to_assets` | 原始值 | 杠杆风险 |
| `q_gr_yoy` | 单季度营业总收入同比 | 收入成长性 |
| `q_profit_yoy` | 单季度净利润同比 | 利润成长性 |
| `audit_opinion_risk` | 审计意见映射到风险等级 | 财务可信度与风险过滤 |

---

### 4.2 第二层：时序衍生因子（~650 个）

对连续型基础因子，应用以下时间窗口变换（窗口 `N = 1, 3, 5, 10, 20, 60`）：

| 变换 | 公式 | 含义 |
|------|------|------|
| **动量（Momentum）** | `f(T) - f(T-N)` | 因子 N 日变化量 |
| **加速度（Acceleration）** | `mom(T) - mom(T-1)` | 变化的变化（二阶导） |
| **滚动分位数（Quantile）** | `f(T) 在过去 N 日中的百分位排名` | 相对历史位置 |
| **滚动波动率（Volatility）** | `std(f, N)` | 因子自身波动性 |
| **滚动偏度（Skewness）** | `skew(f, N)` | 分布不对称性 |
| **均值回归距离（MR Distance）** | `(f(T) - mean(f,N)) / std(f,N)` | 偏离均值程度 |
| **趋势强度（Trend T-stat）** | `linreg_slope(f, N) / std(f, N)` | 趋势的统计显著性 |

对事件型和稀疏型因子，额外应用事件时间变换：

| 变换 | 公式 | 含义 |
|------|------|------|
| **事件年龄（Event Age）** | `days_since_last_event` | 距离上次事件多久 |
| **事件计数（Event Count）** | `count(event, N)` | 近 N 日事件频次 |
| **事件衰减（Event Decay）** | `event_value × exp(-age / half_life)` | 事件影响衰减 |
| **连续修正强度（Revision Strength）** | `Σ signed_revision × decay` | 多次上修/下修的累计影响 |
| **状态持续期（State Duration）** | 某事件/状态已持续的交易日数 | 事件后漂移与拥挤度 |

**命名规则**：
- 连续型：`{base_factor}_{transform}_{window}`，例如 `rsi_qfq_6_momentum_5`
- 事件型：`{event_factor}_{event_transform}_{window}`，例如 `forecast_surprise_mid_event_decay_5`

**注意**：并非所有基础因子都适合所有变换。配置中可指定每个基础因子适用的变换列表，避免无意义组合（如对 0/1 变量 `hsgt_top10_flag` 算偏度）。

---

### 4.3 第三层：特征交叉因子（~120 个）

不同数据维度之间做有意义的跨表组合，不局限于单表单因子。

#### 4.3.1 量价 + 筹码交叉

| 因子 | 公式 | 含义 |
|------|------|------|
| `chip_breakout_strength` | `(close_qfq / weight_avg - 1) × volume_ratio` | 放量突破平均成本区 |
| `upper_overhang_reversal` | `upper_overhang × (-pct_chg)` | 上方套牢 + 当日转弱 |
| `support_rebound` | `support_density × (50 - rsi_qfq_6)` | 支撑密集区超卖反弹 |
| `turnover_chip_shift` | `turnover_rate_f × (-avg_cost_gap)` | 高频换手推动成本迁移 |

#### 4.3.2 资金共振交叉

| 因子 | 公式 | 含义 |
|------|------|------|
| `north_main_consensus` | `z(hk_hold_chg) + z(net_mf_rate) + z(dc_main_strength)` | 北向 + 主力 + DC 主力共振 |
| `north_attention_breakout` | `hsgt_top10_flag × hk_hold_chg × sign(macd_dif_qfq)` | 北向关注 + 趋势确认 |
| `ccass_north_mismatch` | `ccass_hold_ratio_chg - hk_hold_chg` | 结算与北向分歧 |
| `margin_flow_resonance` | `rzmre_intensity × dc_main_strength` | 杠杆资金与主力资金共振 |

#### 4.3.3 事件 + 交易行为交叉

| 因子 | 公式 | 含义 |
|------|------|------|
| `repurchase_discount_absorb` | `repurchase_price_premium × (-pct_chg) × net_mf_rate` | 回购预期下逆势吸筹 |
| `insider_followthrough` | `insider_net_increase × volume_ratio` | 增持事件后的成交确认 |
| `block_trade_followthrough` | `(-block_discount) × inst_net_buy` | 折价大宗后机构接力 |
| `survey_breakout` | `survey_heat × (close_qfq > ma_qfq_20)` | 调研热度配合技术突破 |

#### 4.3.4 预期差 + 技术确认交叉

| 因子 | 公式 | 含义 |
|------|------|------|
| `forecast_trend_confirm` | `forecast_surprise_mid × sign(macd_dif_qfq)` | 预告 surprise 与趋势同向 |
| `analyst_gap_oversold` | `analyst_target_return × (30 - rsi_qfq_6)` | 目标价空间 + 超卖修复 |
| `earnings_quality_breakout` | `express_profit_yoy × boll_bandwidth` | 业绩确认后的波动扩张 |
| `revision_flow_sync` | `analyst_attention_20d × dc_main_strength` | 卖方关注与资金同步 |

#### 4.3.5 风险与拥挤交叉

| 因子 | 公式 | 含义 |
|------|------|------|
| `high_margin_high_unlock` | `rzye_ratio × unlock_ratio` | 高杠杆 + 解禁压力 |
| `pledge_fragile_momentum` | `pledge_ratio × pct_chg_momentum_20` | 高质押下的脆弱动量 |
| `crowded_reversal` | `hk_hold_ratio × winner_rate × (-pct_chg)` | 拥挤获利盘的反转风险 |
| `quality_under_short_pressure` | `q_roe × rqye_ratio` | 高质量资产在融券压力下的韧性 |

---

### 4.4 第四层：行业维度因子（~70 个）

依赖 `stock_basic.industry` 字段做行业分组。

#### 4.4.1 行业相对因子（截面中性化）

将个股因子值减去同行业均值，剥离行业效应。

| 因子 | 公式 | 说明 |
|------|------|------|
| `ind_rel_return` | `pct_chg - industry_mean(pct_chg)` | 行业相对收益 |
| `ind_rel_flow` | `net_mf_rate - industry_mean(net_mf_rate)` | 行业相对资金流 |
| `ind_rel_chip` | `winner_rate - industry_mean(winner_rate)` | 行业相对获利盘 |
| `ind_rel_event` | `forecast_surprise_mid - industry_mean(forecast_surprise_mid)` | 行业内预期差 |
| `ind_rel_expectation` | `analyst_target_return - industry_mean(analyst_target_return)` | 行业内目标价空间 |
| `ind_rank_*` | 个股因子值在行业内的排名分位数 | 行业内相对位置 |

优先对以下基础因子生成行业相对版本：`pct_chg`, `turnover_rate_f`, `net_mf_rate`, `winner_rate`, `hk_hold_chg`, `inst_net_buy`, `forecast_surprise_mid`, `analyst_target_return`, `repurchase_amount_to_mv`。

#### 4.4.2 行业动量与事件热度因子

| 因子 | 公式 | 说明 |
|------|------|------|
| `ind_momentum_5d` | 行业等权平均收益（5日） | 行业短期动量 |
| `ind_momentum_20d` | 行业等权平均收益（20日） | 行业中期动量 |
| `ind_breadth` | 行业内上涨股票占比 | 普涨 vs 分化 |
| `ind_money_flow` | 行业内所有股票主力净流入之和 | 行业级资金方向 |
| `ind_limit_heat` | 行业内涨停/炸板热度 | 短线情绪强弱 |
| `ind_event_heat` | 行业内正向事件个股占比 | 行业催化密度 |
| `ind_revision_breadth` | 行业内卖方上修占比 | 行业预期改善广度 |

#### 4.4.3 行业轮动因子

| 因子 | 公式 | 说明 |
|------|------|------|
| `ind_rotation_score` | `ind_momentum_5d - ind_momentum_20d` | 短期加速行业（轮动信号） |
| `ind_crowding` | 行业平均换手率 / 全市场平均换手率 | 行业拥挤度 |
| `ind_relative_strength` | 行业收益 / 全市场收益 | 行业相对强弱 |
| `ind_flow_rotation` | `ind_money_flow 的 5 日排名变化` | 资金轮动方向 |
| `ind_event_rotation` | `ind_event_heat 的 5 日排名变化` | 催化轮动方向 |

---

### 4.5 第五层：跨股票关联因子（~40 个）

#### 4.5.1 市场情绪 / Market Regime 因子（全市场截面统计，每个股票共享同一值）

| 因子 | 公式 | 说明 |
|------|------|------|
| `mkt_advance_ratio` | 上涨家数 / 总家数 | 涨跌家数比 |
| `mkt_limit_up_count` | 当日涨停家数 | 市场打板热度 |
| `mkt_limit_down_count` | 当日跌停家数 | 市场恐慌度 |
| `mkt_avg_turnover` | 全市场平均换手率 | 市场活跃度 |
| `mkt_money_flow` | 全市场 `net_mf_amount` 之和 | 大盘资金方向 |
| `mkt_north_money` | `stock_money_flow_hsgt.north_money` | 外资整体方向 |
| `mkt_dc_main_strength` | `stock_money_flow_mkt_dc.net_amount_rate` | 大盘主力强度 |
| `mkt_big_small_split` | `buy_elg_amount_rate - buy_sm_amount_rate` | 大盘大小单分歧 |
| `mkt_margin_pulse` | `Δ stock_margin.rzrqye` | 市场杠杆脉冲 |
| `mkt_event_heat` | 当日正向公告/回购/增持/调研个股数 | 事件驱动环境 |

#### 4.5.2 个股 vs 市场

| 因子 | 公式 | 说明 |
|------|------|------|
| `beta_residual` | 个股收益 - beta × 市场收益 | 特质收益（alpha 成分） |
| `corr_with_market_20d` | 个股与大盘 20 日滚动相关性 | 跟随度 |
| `relative_strength_mkt` | 个股 N 日收益 / 大盘 N 日收益 | 市场相对强度 |
| `mkt_sensitivity` | 大盘下跌日的个股平均跌幅 / 大盘跌幅 | 下行 beta |
| `flow_beta_residual` | `net_mf_rate - beta_flow × mkt_dc_main_strength` | 资金面的市场中性残差 |

#### 4.5.3 关联股票 / Peer 因子

| 因子 | 公式 | 说明 |
|------|------|------|
| `peer_momentum` | 同行业其他股票等权平均收益（排除自身） | 同业带动 |
| `peer_money_flow` | 同行业其他股票平均主力净流入 | 同业资金共振 |
| `peer_limit_heat` | 同行业涨停/炸板热度 | 题材扩散度 |
| `peer_event_heat` | 同行业正向事件个股占比 | 事件外溢 |
| `peer_revision_breadth` | 同行业卖方上修占比 | 预期一致改善 |
| `ah_premium_chg` | A/H 溢价变化率（仅 A+H 股） | AH 溢价回归信号 |

---

### 4.6 第六层：组合因子合成（`composite.py`）

在前五层经 IC 筛选出有效因子后，使用以下方法合成 alpha 因子：

| 方法 | 说明 | 适用场景 |
|------|------|---------|
| **等权合成** | 有效因子 z-score 等权平均 | 基线方法 |
| **IC 加权** | 按滚动 20 日 IC 值加权 | 偏好近期有效的因子 |
| **ICIR 加权** | 按滚动 IC / IC_std 加权 | 奖励稳定因子 |
| **正交化合成** | Gram-Schmidt 去相关后等权 | 消除因子共线性 |
| **PCA 降维** | 主成分分析取前 N 个成分 | 高维因子压缩 |
| **机器学习** | XGBoost / LightGBM 非线性组合 | 捕获因子间非线性关系 |

### 4.7 因子总量估算

| 层级 | 数量 |
|------|------|
| 基础因子 | ~120 |
| 时序衍生 | ~650 |
| 特征交叉 | ~120 |
| 行业维度 | ~70 |
| 跨股票关联 | ~40 |
| **合计候选因子** | **~1000** |
| 经 IC / FDR 筛选后预计有效因子 | 50~150 |

实际数量会随事件类因子的窗口数、衰减函数和是否启用行业/市场中性化而弹性变化。

---

## 5. 因子标准化管道

### 5.1 数据时效性控制（防止未来信息泄露）

部分数据源在 T 日收盘后并非当天可获取，必须标注可用延迟并自动 shift，否则回测结果不可信。

| 数据簇 | 代表表 | 可用延迟（`available_lag`） | 说明 |
|--------|--------|---------------------------|------|
| 收盘即可得的行情/技术/交易行为 | `stock_stk_factor_pro`, `stock_money_flow`, `stock_money_flow_dc`, `stock_money_flow_hsgt`, `stock_money_flow_mkt_dc`, `stock_cyq_perf`, `stock_cyq_chips`, `stock_limit_list_d`, `stock_top_list`, `stock_top_inst`, `stock_block_trade`, `stock_hsgt_top10`, `stock_stk_limit` | 0 | T 日收盘后即可纳入 T 日信号，作用于 T+1 开盘交易 |
| **T+1 才稳定可用的持仓 / 杠杆数据** | `stock_hk_hold`, `stock_ccass_hold`, `stock_margin_detail`, `stock_margin` | **1** | 缺少可靠盘中时点，统一保守处理为下一交易日可用 |
| **公告 / 财报 / 股东事件数据** | `stock_stk_holdernumber`, `stock_stk_holdertrade`, `stock_repurchase`, `stock_share_float`, `stock_forecast_vip`, `stock_express_vip`, `stock_disclosure_date`, `stock_report_rc`, `stock_stk_surv`, `stock_fina_indicator_vip`, `stock_income_vip`, `stock_balancesheet_vip`, `stock_cashflow_vip`, `stock_fina_audit`, `stock_pledge_stat`, `stock_top10_holders`, `stock_top10_floatholders` | **1** | 只有日期、没有精确发布时间戳时，统一按下一交易日生效，宁可保守不偷看 |

**实现方式**：`data_loader.py` 中为每个数据源配置 `available_lag` 参数。加载时自动对有延迟的数据做 shift：若 `available_lag=1`，则 T 日因子使用的是 T-1 日的原始数据。所有因子模块无需关心延迟逻辑，由 data_loader 统一处理。

**事件表额外规则**：
- `ann_date` / `end_date` / `report_date` / `surv_date` 类稀疏事件表不直接把原值无脑 forward fill 到所有日期；
- 先映射到 `effective_date`，再生成 `event_age`、`event_count`、`event_decay`、`state_duration` 等事件状态特征；
- 财务慢变量只允许在公告生效后 forward fill，绝不回填到公告前。

### 5.2 标准化流程

所有因子在分析前经过统一处理：

```
原始值
  → 数据延迟 shift（按 available_lag 自动处理）
  → 去极值：MAD（Median Absolute Deviation）3 倍截断
  → 截面标准化：同一 trade_date 内所有股票的同一因子做 z-score
  → 缺失值处理：行业中位数填充；无行业数据则全市场中位数填充
```

**为什么用截面标准化**：因子值需可跨股票比较。同一天内，所有股票的某因子值被归一化到均值 0、标准差 1，消除量纲和分布差异。

---

## 6. 因子分析模块（`analyzer/`）

### 6.1 IC 分析（`ic_analysis.py`）

| 指标 | 定义 | 判断标准 |
|------|------|---------|
| **IC（Information Coefficient）** | 因子值与下期收益的 Pearson 相关系数 | \|IC\| > 0.02 有信号 |
| **Rank IC** | 因子排名与下期收益排名的 Spearman 相关系数 | 更稳健，推荐优先使用 |
| **IC_IR（IC Information Ratio）** | mean(IC) / std(IC) | \|IC_IR\| > 0.5 为有效因子 |
| **IC 胜率** | IC > 0 的天数占比 | > 55% 为稳定 |
| **IC 衰减** | IC 在 lag=1,2,...,10 日的值 | 衰减越慢因子越持久 |

输出：IC 时间序列图、IC 分布直方图、IC 衰减曲线。

### 6.2 分层回测（`layered_backtest.py`）

1. 每个交易日按因子值把股票分为 5 组（或 10 组）
2. 每组等权持仓，每日调仓
3. 计算每组的累计收益曲线
4. 检验：第 1 组（因子值最大）与第 5 组的收益差（多空收益）是否显著
5. 检验：各组收益是否单调递增/递减

输出：分层累计净值图、多空收益曲线、各组年化收益/夏普/回撤。

### 6.3 相关性分析（`correlation.py`）

1. 计算有效因子之间的截面相关性矩阵
2. 用聚类方法识别高度相关的因子簇
3. 每簇取 IC_IR 最高的因子作为代表

输出：因子相关性热力图、因子聚类树状图。

### 6.4 研究报告（`report.py`）

汇总以上分析结果，生成：
- 因子排行榜（按 IC_IR 排序的 CSV）
- 每个有效因子的详情页（IC 图 + 分层图 + 统计摘要）
- 组合因子的性能对比

输出路径：`research/output/`（加入 `.gitignore`）。

---

## 7. 策略层（`strategy/`）

### 7.1 组合回测引擎（`portfolio_backtest.py`）

**不使用现有的 `BacktestEngine`**（那是单股信号驱动引擎）。因子策略是多股票组合策略，需要自建向量化组合回测引擎。

**为什么不用 Backtrader 等第三方框架**：
- 因子研究的核心循环是"改因子 → 跑回测 → 看结果"，需要快。向量化引擎跑全 A 股 6 年数据几秒钟，Backtrader 事件驱动模式需要几十分钟
- 因子策略本质是"每日调仓到目标权重"，不需要复杂的 order/broker 机制
- A 股特殊规则直接在权重矩阵上 mask，实现简洁
- 与现有 pandas 数据流无缝衔接

**引擎核心设计**：

```python
class PortfolioBacktestEngine:
    """
    向量化组合回测引擎
    
    输入：
    - weight_matrix: DataFrame (date × stock)，每日目标持仓权重
    - return_matrix: DataFrame (date × stock)，每日个股收益率
    - trade_constraints: A 股交易约束配置
    
    输出：
    - PortfolioBacktestResult：净值曲线、交易记录、绩效指标
    """
```

**核心计算逻辑**（纯矩阵运算，不逐行循环）：

```
每个交易日 T：
1. target_weight = signal_generator 输出的目标权重
2. 应用交易约束（见 7.2），得到 actual_weight
3. turnover = |actual_weight(T) - actual_weight(T-1)|.sum()
4. cost = turnover × (commission + slippage)
5. portfolio_return(T) = Σ(actual_weight × stock_return) - cost
6. nav(T) = nav(T-1) × (1 + portfolio_return(T))
```

### 7.2 A 股交易约束

回测引擎内置以下 A 股特殊规则，在权重矩阵上做 mask：

| 约束 | 处理方式 | 数据来源 |
|------|---------|---------|
| **T+1 制度** | T 日新买入的股票，T 日不能卖出（权重只能增不能减） | 引擎内部逻辑 |
| **涨停不可买** | 当日涨停（close = limit_up_price）的股票，新增权重设为 0 | `stock_stk_limit` |
| **跌停不可卖** | 当日跌停（close = limit_down_price）的股票，不能减仓 | `stock_stk_limit` |
| **一字板过滤** | 一字涨停（open = limit_up_price）完全不可买入 | `stock_stk_limit` |
| **停牌处理** | 停牌股票保持前一日权重不变，不参与调仓 | `stock_suspend_d` |
| **ST 限制** | ST 股票默认排除（由 universe 过滤） | `stock_st` |

### 7.3 信号生成（`signal_generator.py`）

基于组合因子值生成目标持仓权重：

```
每个交易日 T 收盘后：
1. 计算所有股票的组合因子值
2. 截面排名，选出因子值最高的 Top N% 股票
3. 目标权重：等权分配给入选股票，或按因子值加权
4. 已持仓股票若跌出 Top M%，目标权重设为 0（卖出）
```

可配置参数：
- `top_pct`：买入阈值（默认 10%，即因子排名前 10% 的股票）
- `hold_pct`：持仓阈值（默认 30%，跌出前 30% 才卖出，避免频繁换手）
- `max_holdings`：最大持仓数（默认 20 只）
- `weighting`：权重方式（`equal` 等权 / `factor_weighted` 因子值加权）

### 7.4 出场规则（`exit_rules.py`）

在信号生成后、权重矩阵传入回测引擎前，应用出场规则修正权重：

| 规则 | 说明 | 默认参数 |
|------|------|---------|
| 止盈 | 持仓收益达到阈值，权重设为 0 | 20% |
| 止损 | 持仓亏损达到阈值，权重设为 0 | -8% |
| 最大持仓天数 | 超过 N 天强制清仓 | 10 天 |
| 因子反转 | 因子排名跌出 hold_pct | 30% |
| 反向信号 | 因子值变为负数 | - |

### 7.5 回测配置（`backtest_config.py`）

```python
@dataclass
class PortfolioBacktestConfig:
    initial_capital: float = 10_000_000     # 初始资金（组合策略用 1000 万）
    commission_rate: float = 0.0003         # 佣金率（双边）
    stamp_tax: float = 0.001               # 印花税（卖出单边）
    slippage: float = 0.002                # 滑点
    min_commission: float = 5.0             # 最低佣金
    benchmark: str = "000300.SH"            # 基准指数（沪深300）
    enforce_t1: bool = True                 # 是否执行 T+1 限制
    enforce_limit: bool = True              # 是否执行涨跌停限制
    enforce_suspend: bool = True            # 是否执行停牌限制
```

### 7.6 回测评估指标

| 指标 | 说明 |
|------|------|
| 年化收益率 | 策略年化收益 |
| 夏普比率 | 风险调整后收益 |
| 最大回撤 | 最大净值回撤幅度 |
| 最大回撤持续期 | 回撤恢复天数 |
| Calmar 比率 | 年化收益 / 最大回撤 |
| 胜率 | 盈利交易日占比 |
| 盈亏比 | 平均盈利日收益 / 平均亏损日收益 |
| 日均换手率 | 每日调仓带来的换手 |
| 多空收益 | Top 组收益 - Bottom 组收益 |
| 超额收益 | 策略收益 - 基准收益（沪深300） |
| 信息比率 | 超额收益 / 超额收益波动率 |
| 月度胜率 | 月度超额收益 > 0 的月份占比 |

---

## 8. Jupyter Notebooks

### 8.1 `01_data_exploration.ipynb` — 数据探索

- 加载各表，查看结构、行数、时间范围
- 检查缺失值比例、异常值分布
- 检查事件表稀疏度、公告滞后和 `effective_date` 映射是否正确
- 关键字段的描述性统计和分布图
- 数据质量问题记录

### 8.2 `02_single_factor_analysis.ipynb` — 单因子研究

- 选择一个连续型因子（如 `net_mf_rate`）和一个事件型因子（如 `forecast_surprise_mid_event_decay_5`）跑完整分析流程
- IC 时间序列 + 分布 + 衰减
- 分 5 组回测 + 净值曲线
- 展示连续因子与稀疏事件因子的完整研究 pipeline，作为模板

### 8.3 `03_factor_screening.ipynb` — 全量因子筛选

- 批量计算所有候选因子的 IC / IC_IR
- 因子排行榜可视化
- 相关性矩阵 + 聚类分析
- 筛选出有效因子池

### 8.4 `04_composite_factor.ipynb` — 组合因子

- 用多种合成方法（等权、IC加权、ML）构建组合因子
- 对比各组合方法的 IC 表现
- 特征重要性分析（ML 方法）
- 确定最终组合因子方案

### 8.5 `05_strategy_backtest.ipynb` — 策略回测

- 基于组合因子生成交易信号
- 完整回测：净值曲线、交易记录、绩效指标
- 参数敏感性分析（不同 top_pct、exit_rules 的影响）
- 与基准（沪深300）、内置策略（双均线等）对比

---

## 9. 技术规范

### 9.1 依赖

复用 `apps/.venv` 共享虚拟环境。需要的额外依赖：

| 包 | 用途 |
|----|------|
| `scikit-learn` | PCA、线性回归、标准化 |
| `lightgbm` 或 `xgboost` | 非线性因子合成 |
| `matplotlib` / `seaborn` | 图表生成 |
| `jupyterlab` | Notebook 环境 |
| `scipy` | 统计检验 |

### 9.2 数据库连接

```python
from shared.stock_core.db import build_mysql_url
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(build_mysql_url("TS_MYSQL_DATABASE"))
df = pd.read_sql("SELECT ... FROM stock_stk_factor_pro WHERE trade_date = %s", engine, params=[date])
```

### 9.3 性能考虑

- `stock_stk_factor_pro` 有 14M 行 × 261 列，全量加载不现实
- 按 trade_date 分批加载，每次处理一个交易日的截面数据
- 计算密集型操作使用 pandas 向量化，避免逐行循环
- `stock_cyq_chips` 这类明细表先在日内聚合为少数统计量（如 `upper_overhang`, `support_density`），再 join 回主表
- 稀疏事件表先预聚合成 `date × stock` 的事件特征层，再与 `stock_stk_factor_pro` 左连接，避免把公告明细直接拉成宽表
- 大批量因子计算结果可缓存到 `output/` 目录的 parquet 文件

### 9.4 命名规范

- 因子名：全小写，下划线分隔，`{来源}_{含义}_{窗口}`
- 文件名：模块职责清晰，一个文件一个类别
- 输出文件：`{日期}_{分析类型}_{参数}.csv/png`

---

## 10. 开发阶段

### Phase 1：基础设施（先跑通 pipeline）

1. `config.py` + `data_loader.py` + `universe.py`
2. `factor_engine/base.py`（标准化管道）
3. `factor_engine/technical.py`（先做技术因子）
4. `analyzer/ic_analysis.py` + `analyzer/layered_backtest.py`
5. `notebooks/01` + `notebooks/02`
6. 验证：选 3~5 个技术因子跑通完整 IC + 分层流程

### Phase 2：全量因子（扩展数据源）

7. 完成剩余 factor_engine 模块（money_flow, chip, northbound, margin, limit, dragon, ownership, event, fundamental）
8. `factor_engine/cross_feature.py` + `industry.py` + `market.py`
9. `analyzer/correlation.py` + `analyzer/report.py`
10. `notebooks/03`
11. 验证：覆盖核心日频表 + 事件表的全量因子筛选，产出有效因子排行榜

### Phase 3：组合与策略

12. `factor_engine/composite.py`
13. `strategy/` 全部模块
14. `notebooks/04` + `notebooks/05`
15. 验证：组合因子策略跑通回测，与内置策略对比

### Phase 4：可视化集成（后续）

16. 将研究成果集成到 quant_platform Web UI

---

## 11. 研究严谨性

### 11.1 样本划分

| 区间 | 用途 | 说明 |
|------|------|------|
| 2018-01-01 ~ 2023-12-31 | **训练集（样本内）** | 因子挖掘、IC 分析、参数调优 |
| 2024-01-01 ~ 2025-06-30 | **验证集** | 因子筛选、组合方法选择 |
| 2025-07-01 ~ 至今 | **测试集（样本外）** | 最终策略评估，仅跑一次 |

**原则**：
- 因子研究阶段只看训练集结果，不偷看验证集和测试集
- 组合因子方法的选择在验证集上做
- 测试集仅用于最终报告，不允许反复调参

### 11.2 过拟合防护

约 1000 个候选因子做大量统计检验，多重比较问题严重。采取以下措施：

| 措施 | 说明 |
|------|------|
| **FDR 校正（Benjamini-Hochberg）** | 对所有因子的 IC t-test p 值做 FDR 校正，控制假发现率 < 5% |
| **IC_IR 双重门槛** | 因子需同时满足 \|IC_IR\| > 0.5 且 FDR 校正后 p < 0.05 |
| **滚动窗口验证** | IC 不仅看全期，还要在滚动 1 年窗口内保持稳定（>70% 窗口有效） |
| **分层单调性检验** | 分 5 组的收益必须通过 Spearman 单调性检验 |
| **训练/验证一致性** | 训练集有效的因子必须在验证集也有效（IC 方向一致且 \|IC_IR\| > 0.3） |

### 11.3 幸存者偏差处理

- **纳入退市股票**：从 `stock_basic` 中取 `list_status='D'`（退市）的股票，在其存续期间纳入研究
- **纳入 ST 股票的历史数据**：股票在被 ST 之前的数据正常参与因子计算，被 ST 后由 universe 过滤排除
- **IPO 过滤**：上市不满 60 个交易日的数据不参与因子计算（新股波动异常）

### 11.4 其他注意事项

| 事项 | 处理 |
|------|------|
| **复权口径统一** | 所有价格类因子使用前复权（qfq），保证时间序列可比 |
| **行业分类时效** | 股票行业归属可能变更，使用当时的行业分类而非最新分类 |
| **缺失值比例监控** | 因子缺失率 > 30% 的交易日，该日不参与 IC 计算 |
| **事件日期保守对齐** | 公告/调研/财报类数据默认按下一交易日生效，避免日期粒度导致未来信息泄露 |
| **事件覆盖率监控** | 稀疏事件因子需同时报告覆盖股票数和覆盖交易日占比，防止“高 IC 但样本极少”的伪信号 |
| **极端市场过滤** | 可选：排除熔断等极端行情日（2015-06 ~ 2015-09） |
