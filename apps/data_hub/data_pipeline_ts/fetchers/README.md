# `fetchers`

`fetchers/` 是 `data_pipeline_ts` 的取数层。它负责：

- 调用 TuShare API
- 把返回值整理成稳定的 `pandas.DataFrame`
- 在类体内定义显式 `fields` 和 `table_schema`
- 在必要时处理 fan-out、分片兜底、快照补列、去重、限流

它不负责：

- 调度时机和 profile 归类
- 日期模板渲染
- 写库、覆盖删除、运行日志

这些职责分别在 `jobs/`、`execution/`、`execution/persistence.py` 中完成。

当前这一层包含：

- 51 个 job fetcher
- 3 个 infrastructure fetcher

## 调用链路

```text
execution.runner / execution.infrastructure
  -> fetcher.fetch(**params)
    -> BaseFetcher.fetch()
      -> 当前 fetcher.read_data(**params)
        -> TuShareClient.call(...) / TuShareClient.pro_bar(...)
        -> DataFrame reindex 到 fields 顺序
  -> DatabaseWriter.write(...)
```

核心文件：

- `base.py`
  - 定义 `BaseFetcher`、`ColumnDef`、`TableSchema`
  - 提供 `fanout_by_stock_codes(...)`
- `client.py`
  - 封装 TuShare 调用
  - 负责缓存、重试、最小间隔、每分钟限流
- `__init__.py`
  - 汇总 51 个 job fetcher
  - 生成 `FETCHER_REGISTRY`
- `infrastructure.py`
  - 暴露 `StockBasicFetch`、`StockCompanyFetch`、`TradeCalFetch`

## 目录规则

- 一个文件只放一个 fetcher class
- 文件名必须等于 MySQL `table_name` 的 snake_case
- 每个 fetcher 必须显式声明 `fields` 和 `table_schema`
- 常规 job fetcher 要从子包 `__init__.py` 导出，并注册到 `fetchers/__init__.py`
- infrastructure fetcher 可导入使用，但不进入 `FETCHER_REGISTRY`

## 特殊fetcher说明


### 默认会访问全市场 `ts_code`

| fetcher | 必填入口参数 | 可选覆盖参数 | 全市场状态范围 | 说明 |
| --- | --- | --- | --- | --- |
| `StockDailyQfqFetch` | `trade_date` 或 `start_date/end_date` | `stock_codes` | `("L",)` | 不能传单个 `ts_code`，内部用 `pro_bar` 拉前复权日线 |
| `FinaAuditFetch` | `ann_date` | `stock_codes` | `("L",)` | 不能传单个 `ts_code`，适配按公告日调度的增量拉取 |
| `PledgeDetailFetch` | `snapshot_date` | `stock_codes` | `("L",)` | 不能传单个 `ts_code`，结果额外补 `snapshot_date` |
| `CyqChipsFetch` | `trade_date` 或 `start_date/end_date` | `stock_codes` | `("L",)` | 不能传单个 `ts_code`，有额外限流与 no-data 处理 |


### 按枚举值内部 fan-out

| fetcher | 外部入口 | 内部分片 | 原因 |
| --- | --- | --- | --- |
| `StockHsgtFetch` | `trade_date` | `HK_SZ / SZ_HK / HK_SH / SH_HK` | `type` 是关键维度，单次返回也有截断风险 |
| `KPLListFetch` | `trade_date` | `涨停 / 炸板 / 跌停 / 自然涨停 / 竞价` | 不同 `tag` 的榜单需要合并后才是完整交易日视图 |

### 先直调，命中行数上限时按交易所拆分兜底

| fetcher | 外部入口 | 直调阈值 | 拆分维度 | 说明 |
| --- | --- | --- | --- | --- |
| `LimitListDFetch` | `trade_date` | `2500` 行 | `exchange=SH/SZ/BJ` | 先拿单日全集，只有命中上限才拆 |
| `MarginFetch` | `trade_date` | `4000` 行 | `exchange_id=SSE/SZSE/BSE` | 直调常态更省请求数 |
| `MarginSecsFetch` | `trade_date` | `6000` 行 | `exchange=SSE/SZSE/BSE` | 同上，拆分仅用于防截断 |

### 快照型 fetcher

| fetcher | 必填入口 | 调用方式 | 结果处理 |
| --- | --- | --- | --- |
| `HMListFetch` | `snapshot_date` | 直接调 `hm_list` | 补 `snapshot_date` 列 |
| `PledgeDetailFetch` | `snapshot_date` | 全市场 `ts_code` fan-out 调 `pledge_detail` | 补 `snapshot_date` 列 |

### 特殊 transport / 清洗逻辑

| fetcher | 特殊逻辑 | 说明 |
| --- | --- | --- |
| `StockDailyQfqFetch` | 使用 `client.pro_bar()` | 固定 `asset="E"`, `adj="qfq"`, `freq="D"` |
| `CyqChipsFetch` | 自定义 client 限流配置 | `min_interval_seconds=0.35`，`max_calls_per_minute=190` |
| `CyqChipsFetch` | 特殊错误处理 | `"指定数据不存在"` 视为无数据，限流错误会等待后重试 |
| `TopListFetch` | 去重 | 对 `trade_date + ts_code + reason` 去重 |
| `KPLListFetch` | sparse frame concat 保护 | 拼接前去掉全空列，避免 pandas `FutureWarning` |

## 当前 fetcher 总览

### `basic_data/`

| table_name | fetcher | 类型 | 说明 | 策略 |
| --- | --- | --- | --- | --- |
| `stock_new_share` | `NewShareFetch` | job | 新股发行 | direct |
| `stock_hsgt` | `StockHsgtFetch` | job | 沪深港通成份 | enum fan-out by `type` |
| `stock_st` | `StockStFetch` | job | 风险警示股票 | direct |
| `stock_basic` | `StockBasicFetch` | infrastructure | 公司基础信息 | direct |
| `stock_company` | `StockCompanyFetch` | infrastructure | 上市公司基本信息 | direct |
| `trade_cal` | `TradeCalFetch` | infrastructure | 交易日历 | direct |

### `stock_market_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_daily` | `StockDailyFetch` | 股票日线行情 | direct |
| `stock_daily_basic` | `StockDailyBasicFetch` | 股票日线基本指标 | direct |
| `stock_suspend_d` | `StockSuspendDFetch` | 每日停复牌信息 | direct |
| `stock_daily_qfq` | `StockDailyQfqFetch` | 股票前复权日线 | full-market `ts_code` fan-out + `pro_bar` |
| `stock_stk_limit` | `StkLimitFetch` | 个股涨跌停价格 | direct |
| `stock_hsgt_top10` | `HSGTTop10Fetch` | 沪深港通十大成交股 | direct |
| `stock_ggt_top10` | `GGTTop10Fetch` | 港股通十大成交股 | direct |
| `stock_ggt_daily` | `GGTDailyFetch` | 港股通每日成交统计 | direct |

### `money_flow_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_money_flow` | `MoneyFlowFetch` | 个股资金流向 | direct |
| `stock_money_flow_hsgt` | `MoneyFlowHSGTFetch` | 沪深港通资金流向 | direct |
| `stock_money_flow_dc` | `MoneyFlowDCFetch` | 东方财富资金流向 | direct |
| `stock_money_flow_mkt_dc` | `MoneyFlowMktDCFetch` | 东方财富大盘资金流向 | direct |

### `margin_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_margin` | `MarginFetch` | 融资融券汇总 | row-cap fallback by `exchange_id` |
| `stock_margin_detail` | `MarginDetailFetch` | 融资融券明细 | direct |
| `stock_margin_secs` | `MarginSecsFetch` | 融券卖出量 | row-cap fallback by `exchange` |
| `stock_slb_len` | `SLBLenFetch` | 转融通期限统计 | direct |

### `board_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_top_list` | `TopListFetch` | 龙虎榜每日明细 | direct + post-fetch de-dup |
| `stock_top_inst` | `TopInstFetch` | 龙虎榜机构明细 | direct |
| `stock_limit_list_d` | `LimitListDFetch` | 涨跌停统计 | row-cap fallback by `exchange` |
| `stock_kpl_list` | `KPLListFetch` | 开盘啦题材榜 | enum fan-out by `tag` |
| `stock_kpl_concept_cons` | `KPLConceptConsFetch` | 开盘啦题材成份 | direct |
| `stock_hm_list` | `HMListFetch` | 游资营业部龙虎榜快照 | direct + snapshot column |

### `financial_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_forecast_vip` | `ForecastVipFetch` | 业绩预告增量 | direct |
| `stock_express_vip` | `ExpressVipFetch` | 业绩快报增量 | direct |
| `stock_disclosure_date` | `DisclosureDateFetch` | 财报披露计划 | direct |
| `stock_dividend` | `DividendFetch` | 分红送股公告增量 | direct |
| `stock_fina_audit` | `FinaAuditFetch` | 财务审计意见增量 | full-market `ts_code` fan-out |
| `stock_income_vip` | `IncomeVipFetch` | 利润表披露增量 | direct |
| `stock_balancesheet_vip` | `BalancesheetVipFetch` | 资产负债表披露增量 | direct |
| `stock_cashflow_vip` | `CashflowVipFetch` | 现金流量表披露增量 | direct |
| `stock_fina_indicator_vip` | `FinaIndicatorVipFetch` | 财务指标披露增量 | direct |

### `reference_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_top10_holders` | `Top10HoldersFetch` | 十大股东增量 | direct |
| `stock_top10_floatholders` | `Top10FloatHoldersFetch` | 十大流通股东增量 | direct |
| `stock_stk_holdernumber` | `StkHolderNumberFetch` | 股东户数增量 | direct |
| `stock_stk_holdertrade` | `StkHolderTradeFetch` | 股东增减持增量 | direct |
| `stock_pledge_stat` | `PledgeStatFetch` | 股票质押统计增量 | direct |
| `stock_pledge_detail` | `PledgeDetailFetch` | 股票质押明细快照 | full-market `ts_code` fan-out + snapshot column |
| `stock_repurchase` | `RepurchaseFetch` | 股票回购增量 | direct |
| `stock_share_float` | `ShareFloatFetch` | 限售股解禁增量 | direct |
| `stock_block_trade` | `BlockTradeFetch` | 大宗交易 | direct |

### `special_data/`

| table_name | fetcher | 说明 | 策略 |
| --- | --- | --- | --- |
| `stock_report_rc` | `ReportRCFetch` | 卖方盈利预测数据 | direct |
| `stock_cyq_perf` | `CyqPerfFetch` | 每日筹码及胜率 | direct |
| `stock_cyq_chips` | `CyqChipsFetch` | 每日筹码分布 | full-market `ts_code` fan-out + custom rate-limit handling |
| `stock_stk_factor_pro` | `StkFactorProFetch` | 股票技术面因子（专业版） | direct |
| `stock_ccass_hold` | `CcassHoldFetch` | 中央结算系统持股统计 | direct |
| `stock_hk_hold` | `HKHoldFetch` | 沪深股通持股明细 | direct |
| `stock_stk_ah_comparison` | `StkAHComparisonFetch` | AH股比价 | direct |
| `stock_stk_surv` | `StkSurvFetch` | 机构调研数据 | direct |

## 详细说明：默认访问全市场 `ts_code` 的 fetcher

这类 fetcher 的共同点：

- 外部调度只传日期或快照参数
- 上游接口本身要求 `ts_code`，或者单只股票是天然查询粒度
- 复杂度封装在 fetcher 内部，调度层不需要知道“要循环哪些 code”

### `BaseFetcher.fanout_by_stock_codes(...)`

`base.py` 提供的共享 helper 做了这几件事：

1. 如果显式传入 `stock_codes`，先做 strip + 去重
2. 如果没传 `stock_codes`，按 `stock_basic_statuses` 循环调用：
   - `stock_basic(exchange="", list_status=<status>, fields="ts_code")`
3. 汇总并去重 `ts_code`
4. 对每个 `ts_code` 调 `fetch_one(stock_code)`
5. 拼接非空结果并按 `columns` 重排


## 调度参数和上游 API 参数不是一回事

这层有一个重要原则：

- 调度层传“业务入口参数”
- fetcher 决定是否把它翻译成上游 API 所需的多次调用

常见例子：

- `ann_date -> FinaAuditFetch`：
  调度层只知道“按公告日增量”，fetcher 内部把它展开成多个 `ts_code + ann_date`
- `snapshot_date -> PledgeDetailFetch`：
  调度层只知道“当天快照”，fetcher 内部负责遍历全市场并补快照列
- `trade_date -> KPLListFetch`：
  调度层只知道“某个交易日的开盘啦榜单”，fetcher 内部负责把 5 个 `tag` 合并起来

所以：

- 可以把这些策略摘要写进 `jobs/catalog.py` 的 `fetch_strategies`
- 但不要把真实分片阈值、枚举列表、重试分支等执行细节搬进 `jobs/catalog.py`
- 不要让 `execution/` 知道 `type/tag/exchange` 这些内部拆分细节

当前 `jobs/catalog.py` 使用的策略元数据值包括：

- `direct`
- `full_market_stock_code_fanout`
- `enum_fanout_type`
- `enum_fanout_tag`
- `row_cap_fallback_exchange`
- `row_cap_fallback_exchange_id`
- `snapshot_column`
- `transport_pro_bar`
- `custom_rate_limit_handling`
- `post_fetch_dedup`

## 新增或修改 fetcher 时的建议

### 默认策略

优先写成 direct single-call：

- `read_data()` 直接调用一个 endpoint
- `fields=",".join(self.fields)`
- 空结果返回 `pd.DataFrame(columns=self.fields)`

### 只有在确实需要时，再升级成特殊策略

- 上游接口要求 `ts_code`，但调度入口只给日期：
  - 用 `fanout_by_stock_codes(...)`
- 上游接口要求按枚举参数才能拿全：
  - 在 fetcher 内部做 enum fan-out
- 上游接口有单次行数上限：
  - 先直调，再在命中上限时分片兜底
- 数据是快照：
  - 显式要求 `snapshot_date`，并在结果中补列
- 上游数据可能重复：
  - 在 fetcher 层做轻量去重

### 测试至少覆盖

- fetcher 是否正确注册
- `client.call()` 或 `client.pro_bar()` 是否收到正确参数
- 返回列顺序是否等于 `fields`
- 特殊行为是否被覆盖：
  - fan-out
  - row-cap fallback
  - snapshot 列补充
  - 参数拒绝逻辑
  - 去重 / warning 兜底

推荐最小验证：

```bash
python -m pytest -q apps/data_hub/data_pipeline_ts/tests/test_fetchers.py
```

## 一句话理解这层

`fetchers/` 的职责边界很窄：把“这个数据怎么从上游接口拉下来，并整理成稳定表结构”封装好，不把调度、模板渲染和写库规则混进来。
