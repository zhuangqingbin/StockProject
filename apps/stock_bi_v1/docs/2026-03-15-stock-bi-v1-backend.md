# Stock BI V1 Backend Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend for stock_bi_v1 with 6 API modules, precompute pipeline, and TTL caching.

**Architecture:** Modular FastAPI backend following existing stock_bi patterns — raw SQL via `text()`, Pydantic response models, `cachetools.TTLCache`, router/service/repository per module. Reads from MySQL `stock_database` (read-only on existing tables, read-write on 3 new precomputed tables).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pandas, PyMySQL, Pydantic v2, cachetools

**Spec:** `docs/superpowers/specs/2026-03-15-stock-bi-v1-design.md`

**Existing patterns to follow:** `apps/stock_bi/codex/backend/` — same project structure, same shared config/db imports, same test style.

---

## Chunk 1: Backend Foundation

### Task 1: Project skeleton and infrastructure

**Files:**
- Create: `apps/stock_bi_v1/backend/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/settings.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/database.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/cache.py`
- Create: `apps/stock_bi_v1/backend/models/__init__.py`
- Create: `apps/stock_bi_v1/backend/modules/__init__.py`
- Create: `apps/stock_bi_v1/backend/precompute/__init__.py`
- Reference: `shared/stock_core/config.py`, `shared/stock_core/db.py`
- Reference: `apps/stock_bi/codex/backend/infrastructure/settings.py` (pattern)

- [ ] **Step 1:** Create directory structure，包括 backend/, infrastructure/, models/, modules/ (market, industry, stock, flow, toplist, screener), precompute/，各目录放 `__init__.py`

- [ ] **Step 2:** 写 `infrastructure/settings.py` — 从 `shared.stock_core.config` 导入 `get_env`, `get_int`，从 `shared.stock_core.db` 导入 `build_mysql_url`。导出: DATABASE_URL, API_HOST (默认 0.0.0.0), API_PORT (默认 8100), 7 个 CACHE_TTL 常量 (overview=300s, kline_daily=300s, kline_weekly=3600s, ranking=120s, screener=30s, heatmap=300s, search=600s)

- [ ] **Step 3:** 写 `infrastructure/database.py` — 创建 SQLAlchemy engine (pool_pre_ping=True, pool_recycle=3600)，导出 Base (declarative_base), `get_db()` (FastAPI 依赖注入), `execute_sql(sql, params)` → list[dict], `execute_scalar(sql, params)` → scalar

- [ ] **Step 4:** 写 `infrastructure/cache.py` — 基于 cachetools.TTLCache。提供 `cached(ttl)` 装饰器（按函数名+参数 MD5 做缓存 key），`clear_all_caches()` 清除所有缓存实例

- [ ] **Step 5:** Commit

---

### Task 2: ORM models (existing tables + precomputed tables)

**Files:**
- Create: `apps/stock_bi_v1/backend/models/db_models.py`
- Create: `apps/stock_bi_v1/backend/models/api_models.py`
- Reference: spec section 4.4 (precomputed schemas)

- [ ] **Step 1:** 写 `db_models.py` — 映射全部现有表和 3 张预计算表

现有表 ORM 映射:
| Model | Table | 主键 | 注意事项 |
|-------|-------|------|----------|
| DailyKline | daily_kline | (ts_code, trade_date) | |
| DailyBasic | daily_basic | (ts_code, trade_date) | |
| Moneyflow | moneyflow | (ts_code, trade_date) | 字段用 `_amount` 后缀 (buy_elg_amount 等) |
| MoneyflowHsgt | moneyflow_hsgt | trade_date | hgt, sgt, north_money, south_money |
| IndexDaily | index_daily | (ts_code, trade_date) | |
| TopList | top_list | (ts_code, trade_date) | **pct_chg 必须用 `Column("pct_change", Float)` 做 ORM 别名** |
| StockBasic | stock_basic | ts_code | 字段: ts_code, symbol, name, area, industry, market, exchange, is_hs, list_date |
| StockStkLimit | stock_stk_limit | (ts_code, trade_date) | pre_close, up_limit, down_limit |

预计算表 ORM 映射 (按 spec section 4.4 的完整 schema):
| Model | Table | 主键 | 关键列 |
|-------|-------|------|--------|
| PrecomputedMarket | precomputed_market | trade_date (Date) | distribution(JSON), up/down_limit_count(INT), flat_count(INT), total_amount(DECIMAL), top_gainers/losers/volume/turnover(JSON) |
| PrecomputedIndustry | precomputed_industry | (trade_date, industry) 复合主键 | avg_pct_chg(DECIMAL), total_amount, up/down_count, net_mf_amount, stock_count |
| PrecomputedLimit | precomputed_limit | trade_date (Date) | up/down_limit_stocks(JSON), up/down_count(INT), broken_count(INT), broken_rate(DECIMAL), tier_stats(JSON) |

- [ ] **Step 2:** 写 `api_models.py` — Pydantic v2 响应模型，覆盖所有 6 个模块

需要的 Pydantic 模型:
- **Market**: IndexItem, RankingItem, MarketOverviewResponse, LimitStatsResponse, LimitStockItem
- **Industry**: IndustryHeatmapItem, IndustryDetailResponse, IndustryStockItem
- **Stock**: StockProfileResponse, KlineItem, ValuationItem, PeerItem, SearchResult
- **Flow**: NorthMoneyItem, StockFlowItem, FlowDetailResponse
- **TopList**: TopListItem, TopListHistoryItem
- **Screener**: ScreenerCondition (field, operator, value), ScreenerRequest (conditions, sort_by, order, page, size), ScreenerResultItem, ScreenerResponse (total, page, size, items), FilterMeta (field, label, category, operators)

- [ ] **Step 3:** Commit

---

### Task 3: Main app entry point and run scripts

**Files:**
- Create: `apps/stock_bi_v1/backend/main.py`
- Create: `apps/stock_bi_v1/run.py`
- Create: `apps/stock_bi_v1/run.sh`
- Create: `apps/stock_bi_v1/requirements.txt`
- Modify: `pyproject.toml` (添加 test path)

- [ ] **Step 1:** 写 `main.py` — FastAPI app，lifespan 中做 `Base.metadata.create_all()` 建预计算表 + `_ensure_indexes()` 创建 spec 4.6 中定义的 8 个索引 (`CREATE INDEX IF NOT EXISTS`)。CORS 全开。注册 6 个模块 router (prefix `/api/{module}`)。Health check endpoint。预计算触发 endpoint: `POST /api/precompute/{trade_date}` 使用 BackgroundTasks 异步执行

- [ ] **Step 2:** 写 `run.py` — 确保 repo root 在 sys.path，用 uvicorn 启动 `apps.stock_bi_v1.backend.main:app`，支持 reload

- [ ] **Step 3:** 写 `run.sh` — cd 到 repo root 后 `exec python3 -m apps.stock_bi_v1.run`

- [ ] **Step 4:** 写 `requirements.txt` — fastapi, uvicorn[standard], sqlalchemy>=2.0, pymysql, pydantic>=2.0, cachetools>=5.3, pandas>=2.0

- [ ] **Step 5:** `pyproject.toml` 的 testpaths 中加入 `"apps/stock_bi_v1/tests"`

- [ ] **Step 6:** Commit

---

### Task 4: Tests for infrastructure

**Files:**
- Create: `apps/stock_bi_v1/tests/__init__.py`
- Create: `apps/stock_bi_v1/tests/test_infrastructure.py`

- [ ] **Step 1:** 写 `test_infrastructure.py`，测试:
  - settings 常量能正确加载 (DATABASE_URL 以 mysql+pymysql:// 开头, API_PORT 是 int, CACHE_TTL_OVERVIEW == 300)
  - `@cached` 装饰器: 相同参数只调用一次，不同参数分别缓存
  - `clear_all_caches()` 清除后重新调用
  - TTL 过期后重新调用 (sleep 1.1s)

- [ ] **Step 2:** 运行 `pytest apps/stock_bi_v1/tests/test_infrastructure.py -v`，全部 PASS

- [ ] **Step 3:** Commit

---

## Chunk 2: Market & Industry Modules

### Task 5: Market module — repository + service

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/market/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/market/service.py`

- [ ] **Step 1:** 写 `market/repository.py`，提供以下查询函数:

| 函数 | 说明 | SQL 要点 |
|------|------|----------|
| `get_latest_trade_date()` | MAX(trade_date) from daily_kline | |
| `get_index_daily(trade_date)` | 5 大指数行情 | ts_code IN ('000001.SH', '399001.SZ', '399006.SZ', '000688.SH', '399005.SZ') |
| `get_precomputed_market(trade_date)` | SELECT * FROM precomputed_market | |
| `get_precomputed_limit(trade_date)` | SELECT * FROM precomputed_limit | |
| `get_distribution(trade_date)` | SELECT pct_chg FROM daily_kline | |
| `get_ranking(trade_date, sort_by, order, limit)` | JOIN daily_kline + stock_basic + daily_basic | **sort_by 必须白名单校验**: pct_chg→dk.pct_chg, amount→dk.amount, turnover_rate→db.turnover_rate |

- [ ] **Step 2:** 写 `market/service.py`，提供带缓存的业务函数:

| 函数 | TTL | 逻辑 |
|------|-----|------|
| `get_overview(trade_date?)` | CACHE_TTL_OVERVIEW | 组装 indices (含中文名映射) + precomputed_market 数据。JSON 字段如果是字符串需 json.loads。TOP 列表截取前 5 条。若无预计算数据则返回空结构 |
| `get_indices(trade_date?)` | CACHE_TTL_OVERVIEW | 索引行情 + 中文名映射 |
| `get_distribution(trade_date?)` | CACHE_TTL_OVERVIEW | 将 pct_chg 列表分桶统计: "-10~-7", "-7~-5", ..., "7~10" |
| `get_ranking(trade_date?, sort_by, order, limit)` | CACHE_TTL_RANKING | 直接调 repository |
| `get_limit_stats(trade_date?)` | CACHE_TTL_OVERVIEW | 从 precomputed_limit 读聚合数据 |
| `get_limit_list(trade_date?, type)` | CACHE_TTL_OVERVIEW | 从 precomputed_limit 读 up_limit_stocks 或 down_limit_stocks JSON 数组 |

所有返回值需做 Decimal → float 转换。

- [ ] **Step 3:** Commit

---

### Task 6: Market module — router

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/market/router.py`

- [ ] **Step 1:** 写 `market/router.py`，路由按 spec 4.3 定义:

| 方法 | 路径 | 参数 |
|------|------|------|
| GET | /overview | date? |
| GET | /indices | date? |
| GET | /distribution | date? |
| GET | /ranking | sort_by="pct_chg", order="desc", limit=20, date? |
| GET | /limit-stats | date? |
| GET | /limit-list | type="up", date? |

- [ ] **Step 2:** Commit

---

### Task 7: Industry module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/industry/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/industry/service.py`
- Create: `apps/stock_bi_v1/backend/modules/industry/router.py`

- [ ] **Step 1:** 写 `industry/repository.py`:

| 函数 | SQL 要点 |
|------|----------|
| `get_precomputed_industries(trade_date)` | SELECT FROM precomputed_industry ORDER BY avg_pct_chg DESC |
| `get_industry_detail(industry, trade_date)` | WHERE trade_date AND industry |
| `get_industry_stocks(industry, trade_date, sort_by, order)` | JOIN daily_kline + stock_basic + daily_basic + moneyflow，按行业筛选。**sort_by 白名单**: pct_chg, amount, turnover_rate, pe_ttm, net_mf_amount |

- [ ] **Step 2:** 写 `industry/service.py` — get_heatmap (缓存 CACHE_TTL_HEATMAP), get_detail (缓存), get_stocks (不缓存，参数多)。Decimal → float 转换

- [ ] **Step 3:** 写 `industry/router.py` — 按 spec 4.3，**用 query param 传行业名 (避免中文 URL path 问题)**:

| 方法 | 路径 | 参数 |
|------|------|------|
| GET | /heatmap | date? |
| GET | /detail | name (必填), date? |
| GET | /stocks | name (必填), sort_by="pct_chg", order="desc", date? |

- [ ] **Step 4:** Commit

---

### Task 8: Tests for market and industry

**Files:**
- Create: `apps/stock_bi_v1/tests/test_market_service.py`
- Create: `apps/stock_bi_v1/tests/test_industry_service.py`

- [ ] **Step 1:** 写 `test_market_service.py` — mock repository 函数，测试:
  - overview 无预计算数据时返回空结构 + indices 有中文名
  - distribution 分桶正确 (如 5.0 进 "3~5" 桶, -2.0 进 "-3~0" 桶, 10.0 进 "7~10" 桶)
  - ranking 透传 repository 结果

- [ ] **Step 2:** 写 `test_industry_service.py` — mock repository，测试:
  - heatmap Decimal 转 float
  - get_stocks 返回正确字段

- [ ] **Step 3:** 运行测试，全部 PASS

- [ ] **Step 4:** Commit

---

## Chunk 3: Stock, Flow, TopList Modules

### Task 9: Stock module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/stock/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/stock/service.py`
- Create: `apps/stock_bi_v1/backend/modules/stock/router.py`

- [ ] **Step 1:** 写 `stock/repository.py`:

| 函数 | SQL 要点 |
|------|----------|
| `search_stocks(query, limit=20)` | WHERE ts_code LIKE %q% OR name LIKE %q% |
| `get_stock_profile(ts_code)` | JOIN stock_basic + daily_kline + daily_basic (最新交易日) |
| `get_kline(ts_code, start?, end?)` | SELECT OHLCV from daily_kline，ORDER BY trade_date |
| `get_valuation_history(ts_code, start?, end?)` | SELECT pe_ttm, pb, ps_ttm from daily_basic |
| `get_peers(ts_code, trade_date)` | 同行业股票 JOIN daily_kline + daily_basic，ORDER BY total_mv DESC LIMIT 20 |
| `get_history(ts_code, start?, end?, page, size)` | 分页查询，返回 (rows, total_count) |

- [ ] **Step 2:** 写 `stock/service.py`:
  - `search(query)` — 缓存 CACHE_TTL_SEARCH
  - `get_profile(ts_code)` — 直接调 repository
  - `get_kline(ts_code, period, start?, end?)` — 缓存 CACHE_TTL_KLINE_DAILY。**若 period 为 weekly/monthly，用 Pandas resample 转换** (open=first, high=max, low=min, close=last, vol/amount=sum, pct_chg=累乘)
  - `get_valuation_history`, `get_peers`, `get_history` — 透传

- [ ] **Step 3:** 写 `stock/router.py` — **search 路由必须在 {code} 路由之前注册**:

| 方法 | 路径 | 参数 |
|------|------|------|
| GET | /search | q (必填) |
| GET | /{code}/profile | |
| GET | /{code}/kline | period="daily", start?, end? |
| GET | /{code}/valuation-history | start?, end? |
| GET | /{code}/peers | |
| GET | /{code}/history | start?, end?, page=0, size=50 |

- [ ] **Step 4:** Commit

---

### Task 10: Flow module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/flow/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/flow/service.py`
- Create: `apps/stock_bi_v1/backend/modules/flow/router.py`

- [ ] **Step 1:** 写 `flow/repository.py`:

| 函数 | SQL 要点 |
|------|----------|
| `get_north_money(days)` | FROM moneyflow_hsgt ORDER BY trade_date DESC LIMIT days |
| `get_stock_flow(ts_code, days)` | FROM moneyflow，全部 _amount 字段 + net_mf_amount |
| `get_stock_flow_detail(ts_code, trade_date)` | 单日单股全部 _amount 字段 |

- [ ] **Step 2:** 写 `flow/service.py` — get_north_money, get_stock_flow (结果 reverse 成时间正序), get_stock_flow_detail

- [ ] **Step 3:** 写 `flow/router.py`:

| 方法 | 路径 | 参数 |
|------|------|------|
| GET | /north | days=30 |
| GET | /stock/{code} | days=30 |
| GET | /stock/{code}/detail | date (必填) |

- [ ] **Step 4:** Commit

---

### Task 11: TopList module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/toplist/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/toplist/service.py`
- Create: `apps/stock_bi_v1/backend/modules/toplist/router.py`

- [ ] **Step 1:** 写 `toplist/repository.py`:

| 函数 | SQL 要点 |
|------|----------|
| `get_daily_toplist(trade_date)` | **必须用 `pct_change AS pct_chg` 别名**，ORDER BY pct_change DESC |
| `get_stock_toplist_history(ts_code)` | 同上别名处理，ORDER BY trade_date DESC |

- [ ] **Step 2:** 写 `toplist/service.py` — get_daily(trade_date?), get_stock_history(ts_code)

- [ ] **Step 3:** 写 `toplist/router.py`:

| 方法 | 路径 | 参数 |
|------|------|------|
| GET | /daily | date? |
| GET | /stock/{code} | |

- [ ] **Step 4:** Commit

---

## Chunk 4: Screener & Precompute

### Task 12: Screener module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/screener/service.py`
- Create: `apps/stock_bi_v1/backend/modules/screener/router.py`
- Create: `apps/stock_bi_v1/backend/modules/screener/repository.py` (空文件，逻辑在 service)

- [ ] **Step 1:** 写 `screener/service.py` — 核心是动态 SQL 构建:

**FIELD_MAP 白名单** (field → SQL 表达式):
- 行情: pct_chg→dk.pct_chg, close→dk.close, amount→dk.amount, vol→dk.vol, turnover_rate→db.turnover_rate
- 估值: pe_ttm→db.pe_ttm, pb→db.pb, ps_ttm→db.ps_ttm, total_mv→db.total_mv, circ_mv→db.circ_mv, total_share→db.total_share, float_share→db.float_share
- 资金: net_mf_amount→mf.net_mf_amount, net_elg_amount→(mf.buy_elg_amount - mf.sell_elg_amount), net_lg_amount→(mf.buy_lg_amount - mf.sell_lg_amount)
- 分类: industry→sb.industry, market→sb.market

**FILTER_META**: 每个字段的 label, category, operators 元数据

**is_st 特殊处理**: 不在 FIELD_MAP 中，在 `_build_query` 中用 `sb.name LIKE 'ST%' OR LIKE '*ST%'` 判定。默认排除 ST，用户可通过 is_st 条件显式包含

**振幅、连涨/连跌天数**: V1 暂不支持（daily_kline 无此字段），在 FILTER_META 中注释说明

**`_build_query()`**: 构建 FROM ... JOIN ... WHERE ... 的 base SQL，支持 gt/lt/eq/between 操作符。返回 (base_sql, params, sort_col, order_dir)

**`query()`**: 调 _build_query，先 COUNT(*) 拿 total，再 SELECT + ORDER BY + LIMIT OFFSET

**`export_csv()`**: 同 _build_query，LIMIT 5000，输出 CSV 字符串

- [ ] **Step 2:** 写 `screener/router.py`:

| 方法 | 路径 | Body/参数 | 响应 |
|------|------|-----------|------|
| GET | /filters | | FilterMeta 列表 |
| POST | /query | ScreenerRequest | ScreenerResponse |
| POST | /export | ScreenerRequest | StreamingResponse (text/csv, Content-Disposition: attachment) |

- [ ] **Step 3:** Commit

---

### Task 13: Precompute pipeline

**Files:**
- Create: `apps/stock_bi_v1/backend/precompute/runner.py`
- Create: `apps/stock_bi_v1/backend/precompute/market_summary.py`
- Create: `apps/stock_bi_v1/backend/precompute/industry_stats.py`
- Create: `apps/stock_bi_v1/backend/precompute/limit_analysis.py`
- Modify: `apps/stock_bi_v1/backend/main.py` (添加 precompute endpoint)

- [ ] **Step 1:** 写 `precompute/market_summary.py`:

`compute_market_summary(trade_date)` → dict:
- 分桶统计 distribution (与 service 中相同逻辑)
- **涨停/跌停数必须用 stock_stk_limit JOIN daily_kline** (`close >= up_limit` / `close <= down_limit`)，**不要用 pct_chg >= 9.9 近似** (ST ±5%, 科创 ±20%, 北交 ±30%)
- 全市场 SUM(amount)
- TOP 20 gainers/losers/volume: JOIN daily_kline + stock_basic
- TOP 20 turnover: JOIN daily_kline + stock_basic + daily_basic (取 turnover_rate)
- Decimal → float 转换

`save_market_summary(data)`:
- DELETE + INSERT 到 precomputed_market
- JSON 字段用 json.dumps
- **不要 pop trade_date**，用 `data["trade_date"]` 读取

- [ ] **Step 2:** 写 `precompute/industry_stats.py`:

`compute_industry_stats(trade_date)` → list[dict]:
- GROUP BY sb.industry，AVG(pct_chg), SUM(amount), 涨/跌家数, SUM(net_mf_amount), COUNT(*)
- JOIN daily_kline + stock_basic + moneyflow

`save_industry_stats(trade_date, stats)`:
- DELETE + 逐行 INSERT 到 precomputed_industry

- [ ] **Step 3:** 写 `precompute/limit_analysis.py`:

`compute_limit_analysis(trade_date)` → dict:
- 涨停股: JOIN daily_kline + stock_stk_limit + stock_basic，WHERE close >= up_limit AND up_limit > 0
- 跌停股: 同上，WHERE close <= down_limit AND down_limit > 0
- 炸板: WHERE high >= up_limit AND close < up_limit
- **连板天数 `consecutive_days` 必须批量查询** — 一次性查所有涨停股的近 30 日 daily_kline + stock_stk_limit，在 Python 中按 ts_code 分组后逐股向前回溯计数。**避免 N+1 查询** (每股单独查会导致 100-300 次 DB 查询)
- tier_stats: 按 consecutive_days 分组计数，key 用字符串 ("1", "2", "3"...)

`save_limit_analysis(data)`: DELETE + INSERT 到 precomputed_limit

- [ ] **Step 4:** 写 `precompute/runner.py`:

`run_precompute(trade_date)`:
1. compute + save market_summary
2. compute + save industry_stats
3. compute + save limit_analysis
4. clear_all_caches()
5. 打印进度日志

- [ ] **Step 5:** 在 main.py 添加 `POST /api/precompute/{trade_date}` endpoint，用 BackgroundTasks 异步执行 run_precompute

- [ ] **Step 6:** Commit

---

### Task 14: Tests for screener and precompute

**Files:**
- Create: `apps/stock_bi_v1/tests/test_screener.py`
- Create: `apps/stock_bi_v1/tests/test_precompute.py`

- [ ] **Step 1:** 写 `test_screener.py`，测试:
  - get_filters() 返回 ≥15 个字段，所有字段都在 FIELD_MAP 白名单中
  - _build_query 忽略未知字段 (不崩溃)
  - _build_query between 操作符生成正确 SQL 参数
  - 默认排除 ST 股 (SQL 含 NOT LIKE)
  - is_st=1 时包含 ST 股 (SQL 含 LIKE 'ST%')

- [ ] **Step 2:** 写 `test_precompute.py` — mock execute_sql，测试:
  - compute_market_summary 分桶正确
  - limit 计数使用 stock_stk_limit (mock 返回的 up_limit/down_limit 值)

- [ ] **Step 3:** 运行测试，全部 PASS

- [ ] **Step 4:** Commit

---

## Chunk 5: Integration & Smoke Tests

### Task 15: API smoke test

**Files:**
- Create: `apps/stock_bi_v1/tests/test_api_smoke.py`

- [ ] **Step 1:** 写 `test_api_smoke.py` — 用 FastAPI TestClient，验证所有路由已注册 (返回非 404):
  - /health → 200
  - /api/market/* (6 条路由)
  - /api/industry/heatmap
  - /api/stock/search?q=test
  - /api/flow/north
  - /api/toplist/daily
  - /api/screener/filters
  - /api/precompute/20260315 (POST)

  部分路由可能返回 500 (无 DB) — 只要不是 404 即可。

- [ ] **Step 2:** 运行测试

- [ ] **Step 3:** Commit

---

### Task 16: 全量验证

- [ ] **Step 1:** 运行全部测试 `pytest apps/stock_bi_v1/tests/ -v`，全部 PASS

- [ ] **Step 2:** 手动验证后端启动: `bash apps/stock_bi_v1/run.sh`，确认 http://localhost:8100/health 返回 `{"status": "ok"}`

- [ ] **Step 3:** 修复问题后 Commit

---

## Summary

| Chunk | Tasks | 交付物 |
|-------|-------|--------|
| 1: Foundation | 1-4 | 基础设施 + ORM + Pydantic + main + run scripts + 基础测试 |
| 2: Market & Industry | 5-8 | 市场概览模块 + 行业模块 + 单元测试 |
| 3: Stock, Flow, TopList | 9-11 | 个股模块 + 资金流模块 + 龙虎榜模块 |
| 4: Screener & Precompute | 12-14 | 高级筛选 (动态SQL) + 预计算管道 + 测试 |
| 5: Integration | 15-16 | API 冒烟测试 + 全量验证 |

**Total: 16 tasks, ~50 steps**

**Frontend plan:** 后端完成并验证 API 后单独写 `2026-03-15-stock-bi-v1-frontend.md`。
