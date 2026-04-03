# data_pipeline_ts

`data_pipeline_ts` 是 A 股 TuShare 数据管线的 Python-native 调度入口，负责从 TuShare API 拉取数据并写入 MySQL。支持每日调度、历史回填和基础设施同步三种模式。

## 架构

```
data_pipeline_ts/
├── main.py              # CLI 入口，解析参数并分发到对应模式
├── execution/           # 执行引擎
│   ├── context.py       #   ExecutionContext — 日期 / 交易日推导
│   ├── runner.py        #   任务编排（串行 / 并行）
│   ├── calendar.py      #   交易日历集成
│   ├── persistence.py   #   DatabaseWriter — 建表 / 补列 / 写库
│   ├── rendering.py     #   参数模板渲染
│   ├── selection.py     #   任务 / 基础设施目标选择与过滤
│   └── infrastructure.py
├── fetchers/            # TuShare API 数据源（54 个 fetcher）
│   ├── base.py          #   BaseFetcher / ColumnDef / TableSchema
│   ├── client.py        #   TuShareClient（缓存 + 限速 + 重试）
│   ├── basic_data/      #   股票列表、公司信息、交易日历等（6 个）
│   ├── stock_market_data/ # 日行情、港股通、停复牌与前复权等（8 个）
│   ├── board_data/      #   龙虎榜、涨停跌停、热门概念等（6 个）
│   ├── money_flow_data/ #   资金流向（4 个）
│   ├── margin_data/     #   融资融券（4 个）
│   ├── financial_data/  #   财务报表与公告（9 个）
│   ├── special_data/    #   特色数据（8 个）
│   └── reference_data/  #   股东、质押、回购、大宗交易等（9 个）
├── jobs/                # 任务定义
│   ├── catalog.py       #   ALL_JOBS / INFRASTRUCTURE_TARGETS 定义
│   ├── profiles.py      #   7 个 ProfileId + ProfileSpec（cron、执行模式）
│   └── specs.py         #   JobSpec / InfrastructureSpec / JobRunResult
├── scripts/             # Shell 入口脚本
│   ├── run_daily.sh     #   主入口（解析 Python 路径，调用 main.py）
│   ├── run_backfill.sh  #   便捷包装 → run_daily.sh --mode backfill
│   ├── sync_infrastructure.sh # 便捷包装 → run_daily.sh --mode infrastructure
│   └── install_launchd.sh    # macOS launchd 定时任务安装
└── tests/               # 13 个测试文件
```

## 模式

### `once`（默认）

执行某一天的一组任务：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-03-17
```

### `backfill`

按日期区间重放任务。依赖 `trade_date` 的任务跳过非交易日；依赖 `current_date` 的按自然日逐天跑：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_post_close_core \
  --start 20260101 \
  --end 20260317
```

### `infrastructure`

同步基础表（stock_basic / stock_company / trade_cal），不走 profile 调度，始终串行：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company,trade_cal \
  --start 20260101 --end 20261231
```

## 参数

| 参数 | 模式 | 说明 |
|------|------|------|
| `--mode` | 直接调 `main.py` 时 | `once` / `backfill` / `infrastructure` |
| `--profiles` | `once` / `backfill` | 逗号分隔的 profile 名称 |
| `--jobs` | `once` / `backfill` | 逗号分隔的 job 名称（更细粒度） |
| `--targets` | `infrastructure` | 逗号分隔的基础设施目标名 |
| `--as-of` | `once` | 日历日，格式 `YYYY-MM-DD` |
| `--start` | `backfill` / `infrastructure` | 开始日期，格式 `YYYYMMDD` |
| `--end` | `backfill` / `infrastructure` | 结束日期，格式 `YYYYMMDD` |
| `--max-workers` | `once` / `backfill` | 单个 profile 的最大并发数 |

## 执行链路

1. `run_daily.sh` 解析 Python 路径 → 调用 `main.py`
2. `ExecutionContext.for_as_of(as_of_date)` 推导 `trade_date`（回看 14 天交易日历）
3. `rendering.py` 渲染 `jobs/catalog.py` 中的参数模板
4. `fetcher.fetch(**resolved_params)` 调用 TuShare API
5. `DatabaseWriter` 按 `scope_columns` 删除旧切片 → 写入新数据
6. 结果记录到 `job_run_log`

### 模板变量

| 变量 | 含义 | 示例 |
|------|------|------|
| `{current_date}` | 自然日紧凑格式 | `20260318` |
| `{current_dt}` | 自然日 ISO 格式 | `2026-03-18` |
| `{trade_date}` | 交易日紧凑格式 | `20260317` |
| `{trade_dt}` | 交易日 ISO 格式 | `2026-03-17` |

### params 与 scope_columns 的关系

- `params` 决定"抓什么数据"（渲染后传给 fetcher）
- `scope_columns` 决定"写库时覆盖哪一片旧数据"

常见组合：

| params | scope_columns | 语义 |
|--------|---------------|------|
| `trade_date: {trade_date}` | `(trade_date,)` | 重刷某个交易日整片数据 |
| `ann_date: {current_date}` | `(ann_date,)` | 重刷某个公告日增量 |
| `snapshot_date: {current_date}` | `(snapshot_date,)` | 按当前自然日写入手工快照 |

## Profile 调度

Profile 是调度分组，决定触发时机、执行方式和回填行为。

| Profile | Cron | 并行/串行 | 回填模式 | 任务数 |
|---------|------|-----------|----------|--------|
| `trade_day_pre_open` | `25 9 * * *` | 并行 | trade_day | 5 |
| `trade_day_post_close_core` | `0 18 * * *` | 并行 | trade_day | 7 |
| `trade_day_post_close_extended` | `35 18 * * *` | 并行 | trade_day | 20 |
| `reference_trade_day_post_close` | `40 18 * * *` | 并行 | trade_day | 1 |
| `financial_calendar_nightly` | `30 21 * * *` | 并行 | calendar_day | 9 |
| `reference_calendar_nightly` | `45 21 * * *` | 并行 | calendar_day | 7 |
| `manual` | 无 | 串行 | 不回填 | 2 |

**注意**：`--profiles` 选的是"跑哪一组任务"，`--jobs` 用于精确点单个任务。是否每天自动跑看的是 profile 有无 cron，而不是它在 `catalog.py` 里属于哪个目录分组列表。

## Fetcher 总览（54 个）

### 基础数据（6 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| StockBasicFetch | stock_basic | 股票列表（代码、名称、地域、行业） |
| StockCompanyFetch | stock_company | 公司详细信息 |
| TradeCalFetch | trade_cal | 交易日历 |
| StockHsgtFetch | stock_hsgt | 沪深港通成分股 |
| StockStFetch | stock_st | ST 标记 |
| NewShareFetch | stock_new_share | IPO 新股 |

### 行情数据（7 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| StockDailyFetch | stock_daily | A 股日线 OHLCV |
| StockDailyBasicFetch | stock_daily_basic | 日指标（换手率、PE、PB） |
| StockSuspendDFetch | stock_suspend_d | 每日停复牌信息 |
| StkLimitFetch | stock_stk_limit | 涨跌停价 |
| HSGTTop10Fetch | stock_hsgt_top10 | 沪深港通 Top10 |
| GGTTop10Fetch | stock_ggt_top10 | 港股通 Top10 |
| GGTDailyFetch | stock_ggt_daily | 港股通每日汇总 |

### 榜单数据（6 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| TopListFetch | stock_top_list | 龙虎榜明细 |
| TopInstFetch | stock_top_inst | 龙虎榜机构交易 |
| LimitListDFetch | stock_limit_list_d | 涨跌停统计 |
| KPLListFetch | stock_kpl_list | 开盘啦热门话题 |
| KPLConceptConsFetch | stock_kpl_concept_cons | 话题成分股 |
| HMListFetch | stock_hm_list | 游资营业部快照（手工） |

### 资金流向（4 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| MoneyFlowFetch | stock_money_flow | 个股资金流向 |
| MoneyFlowHSGTFetch | stock_money_flow_hsgt | 沪深港通资金流向 |
| MoneyFlowDCFetch | stock_money_flow_dc | 东方财富资金流向 |
| MoneyFlowMktDCFetch | stock_money_flow_mkt_dc | 东方财富大盘资金流向 |

### 融资融券（4 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| MarginFetch | stock_margin | 融资融券汇总 |
| MarginDetailFetch | stock_margin_detail | 融资融券明细（按股票） |
| MarginSecsFetch | stock_margin_secs | 融券费率 |
| SLBLenFetch | stock_slb_len | 转融通期限分布 |

### 财务数据（9 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| ForecastVipFetch | stock_forecast_vip | 业绩预告 |
| ExpressVipFetch | stock_express_vip | 业绩快报 |
| DisclosureDateFetch | stock_disclosure_date | 财报披露计划 |
| DividendFetch | stock_dividend | 分红送股公告 |
| FinaAuditFetch | stock_fina_audit | 财务审计意见 |
| IncomeVipFetch | stock_income_vip | 利润表 |
| BalancesheetVipFetch | stock_balancesheet_vip | 资产负债表 |
| CashflowVipFetch | stock_cashflow_vip | 现金流量表 |
| FinaIndicatorVipFetch | stock_fina_indicator_vip | 财务指标 |

### 参考数据（9 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| Top10HoldersFetch | stock_top10_holders | 前十大股东 |
| Top10FloatHoldersFetch | stock_top10_floatholders | 前十大流通股东 |
| StkHolderNumberFetch | stock_stk_holdernumber | 股东人数 |
| StkHolderTradeFetch | stock_stk_holdertrade | 股东增减持 |
| PledgeStatFetch | stock_pledge_stat | 股权质押统计 |
| PledgeDetailFetch | stock_pledge_detail | 股权质押明细（手工快照） |
| RepurchaseFetch | stock_repurchase | 股份回购 |
| ShareFloatFetch | stock_share_float | 限售解禁 |
| BlockTradeFetch | stock_block_trade | 大宗交易 |

### 特色数据（8 个）

| Fetcher | 表 | 说明 |
|---------|-----|------|
| ReportRCFetch | stock_report_rc | 卖方盈利预测数据 |
| CyqPerfFetch | stock_cyq_perf | 每日筹码及胜率 |
| CyqChipsFetch | stock_cyq_chips | 每日筹码分布 |
| StkFactorProFetch | stock_stk_factor_pro | 股票技术面因子（专业版） |
| CcassHoldFetch | stock_ccass_hold | 中央结算系统持股统计 |
| HKHoldFetch | stock_hk_hold | 沪深股通持股明细 |
| StkAHComparisonFetch | stock_stk_ah_comparison | AH股比价 |
| StkSurvFetch | stock_stk_surv | 机构调研数据 |

### 基础设施目标（3 个，独立于 Job 体系）

| Target | 表 | Scope | 说明 |
|--------|-----|-------|------|
| stock_basic | stock_basic | ts_code | 全量股票列表 |
| stock_company | stock_company | ts_code | 全量公司信息 |
| trade_cal | trade_cal | exchange, cal_date | 交易日历（需 --start/--end） |

## TuShareClient

- **缓存**：Pickle 文件缓存于 `.cache/tushare/`，默认 24 小时 TTL
- **限速**：可配置最小请求间隔
- **重试**：2 次重试，指数退避（0.6s * 2^attempt）
- **Token**：读取环境变量 `TUSHARE_TOKEN`

## DatabaseWriter

1. 检查/创建表、补列、修复 TEXT→VARCHAR（索引列）、补复合索引
2. 按 `scope_columns` 删除旧切片
3. 批量 INSERT 新数据
4. 写入 `job_run_log` 记录运行结果

## 测试

```bash
python -m pytest -q apps/data_hub/data_pipeline_ts/tests
```
