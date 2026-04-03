# Table Inventory By Category

> Source basis: `data_pipeline_ts/fetchers/*`, `data_pipeline_ts/jobs/catalog.py`, `README.md`, `notebooks/data_notebook_support.py`
> Purpose: support data_explorer information architecture discussion

## 1. Navigation Categories

| Category | Source | Current count | Notes |
|---|---|---:|---|
| `basic_data` | `fetchers/tushare/basic_data` | 6 | 基础资料与交易日历，部分通过基础设施同步脚本维护 |
| `stock_market_data` | `fetchers/tushare/stock_market_data` | 8 | 日线、停复牌、前复权、港股通相关 |
| `financial_data` | `fetchers/tushare/financial_data` | 9 | 财报、分红与审计意见 |
| `money_flow_data` | `fetchers/tushare/money_flow_data` | 4 | 资金流向 |
| `margin_data` | `fetchers/tushare/margin_data` | 4 | 融资融券 |
| `board_data` | `fetchers/tushare/board_data` | 6 | 龙虎榜、涨跌停、开盘啦题材等 |
| `reference_data` | `fetchers/tushare/reference_data` | 9 | 股东、质押、回购、大宗交易等 |
| `special_data` | `fetchers/tushare/special_data` | 8 | 筹码、AH 比价、技术因子、港股持仓等 |
| `runtime` | notebook special category | 1 | `job_run_log` |
| `database_metadata` | database metadata layer | n/a | DDL、索引、主键、约束、结构统计等 |

## 2. Suggested Category-To-Table Mapping

### `basic_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_basic` | A 股基础信息 | 平台最常用基础表 |
| `stock_company` | 公司基础资料 | 注册资本、城市、主营业务等 |
| `trade_cal` | 交易日历 | 用于判断交易日 |
| `stock_hsgt` | 沪深港通股票列表 | 盘前同步 |
| `stock_st` | ST 股票状态 | 盘前同步 |
| `stock_new_share` | 新股发行与申购日历 | 盘前同步 |

### `stock_market_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_daily` | A 股日线行情 | 高频核心表 |
| `stock_daily_basic` | 每日基本面指标 | 高频核心表 |
| `stock_suspend_d` | 每日停复牌信息 | 盘后核心 |
| `stock_stk_limit` | 每日涨跌停价 | 盘前同步 |
| `stock_hsgt_top10` | 沪深港通前十大成交明细 | 盘后扩展 |
| `stock_ggt_top10` | 港股通前十大成交明细 | 盘后扩展 |
| `stock_ggt_daily` | 港股通日度统计 | 盘后扩展 |

### `money_flow_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_money_flow` | 个股资金流向 | 核心日更 |
| `stock_money_flow_hsgt` | 沪深港通资金流向 | 核心日更 |
| `stock_money_flow_dc` | 扩展资金流向 | 盘后扩展 |
| `stock_money_flow_mkt_dc` | 东方财富大盘资金流向 | 盘后扩展 |

### `margin_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_margin` | 融资融券汇总 | 日更 |
| `stock_margin_detail` | 融资融券明细 | 日更 |
| `stock_margin_secs` | 融券券源信息 | 盘前 |
| `stock_slb_len` | 转融资交易汇总 | 盘后扩展 |

### `board_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_top_list` | 龙虎榜上榜明细 | 日更 |
| `stock_top_inst` | 龙虎榜营业部明细 | 盘后扩展 |
| `stock_limit_list_d` | 每日涨跌停统计与名单 | 盘后扩展 |
| `stock_kpl_list` | 开盘啦题材榜单 | 盘后扩展 |
| `stock_hm_list` | 市场游资名录 | 手工维护 |
| `stock_kpl_concept_cons` | 开盘啦题材成分股 | 手工维护 |

### `financial_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_forecast_vip` | 业绩预告 | 夜间刷新 |
| `stock_express_vip` | 业绩快报 | 夜间刷新 |
| `stock_disclosure_date` | 财报披露日期 | 夜间刷新 |
| `stock_dividend` | 分红送股公告 | 夜间刷新 |
| `stock_fina_audit` | 财务审计意见 | 夜间刷新 |
| `stock_income_vip` | 利润表 | 夜间刷新 |
| `stock_balancesheet_vip` | 资产负债表 | 夜间刷新 |
| `stock_cashflow_vip` | 现金流量表 | 夜间刷新 |
| `stock_fina_indicator_vip` | 财务指标 | 夜间刷新 |

### `reference_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_top10_holders` | 十大股东 | 手工快照 |
| `stock_top10_floatholders` | 十大流通股东 | 手工快照 |
| `stock_stk_holdernumber` | 股东户数 | 夜间刷新 |
| `stock_stk_holdertrade` | 股东增减持 | 夜间刷新 |
| `stock_pledge_stat` | 股权质押统计 | 手工快照 |
| `stock_pledge_detail` | 股权质押明细 | 手工快照 |
| `stock_repurchase` | 回购公告 | 夜间刷新 |
| `stock_share_float` | 限售股解禁 / 流通变动 | 夜间刷新 |
| `stock_block_trade` | 大宗交易 | 交易日盘后 |

### `special_data`

| Table | Business meaning | Notes |
|---|---|---|
| `stock_report_rc` | 卖方盈利预测数据 | 盘后扩展 |
| `stock_cyq_perf` | 每日筹码及胜率 | 盘后扩展 |
| `stock_cyq_chips` | 每日筹码分布 | 盘后扩展 |
| `stock_stk_factor_pro` | 股票技术面因子（专业版） | 盘后扩展 |
| `stock_ccass_hold` | 中央结算系统持股统计 | 盘后扩展 |
| `stock_hk_hold` | 沪深股通持股明细 | 盘后扩展 |
| `stock_stk_ah_comparison` | AH股比价 | 盘后扩展 |
| `stock_stk_surv` | 机构调研数据 | 盘后扩展 |

### `runtime`

| Table | Business meaning | Notes |
|---|---|---|
| `job_run_log` | 任务执行日志 | 支撑新鲜度和任务状态视图 |

### `database_metadata`

| Object / info | Meaning | Notes |
|---|---|---|
| schema summary | 库级概览 | 表数量、分类数量、对象分布 |
| table DDL | 建表 SQL | 真实结构的直接入口 |
| indexes | 索引信息 | 主键、唯一键、普通索引 |
| constraints | 约束信息 | 若存在则可见 |
| column metadata | 字段元信息 | 名称、类型、默认值、可空、注释 |

## 3. Excluded From data_explorer

下面这些表虽然存在于整体系统语境里，但不纳入当前这版平台范围：

| Table | Reason excluded |
|---|---|
| `precomputed_market` | 属于下游结果表，不是首期“数据库信息浏览”核心 |
| `precomputed_industry` | 属于下游结果表，不是首期“数据库信息浏览”核心 |
| `precomputed_limit` | 属于下游结果表，不是首期“数据库信息浏览”核心 |

## 4. What This Means For data_explorer

从信息架构看，V1 不是主题 BI，也不是下游结果大盘，而是一个覆盖原始表、系统表和数据库结构信息的内部数据库信息工作台。

因此更合理的页面组织方式是：
- 先按分类浏览
- 再进入单表详情
- 在单表详情里解决“这张表是什么、有没有数据、怎么筛、怎么把整张表翻着看、它的真实结构是什么”的问题

不建议首期直接按主题做大盘页、财务页、资金流页，也不建议把 `precomputed_*` 拉进目录，因为那会让平台目标从“数据库信息浏览”偏移。
