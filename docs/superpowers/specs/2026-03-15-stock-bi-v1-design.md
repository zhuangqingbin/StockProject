# Stock BI V1 设计文档

> 日期: 2026-03-15
> 状态: Draft
> 视觉稿: `apps/stock_bi_v1/brainstorm/` 目录下的 HTML 文件

## 1. 概述

### 1.1 目标
在 `apps/stock_bi_v1/` 下新建一个股票数据可视化平台，替代现有 `apps/stock_bi/`。核心诉求：
- 强大的多维数据分析能力
- Bloomberg 终端风格的专业界面（纯黑背景 + 橙色强调 + 等宽字体）
- 高信息密度，查询快，体验好
- 数据来源为 `stock_data_platform` 通过每日任务写入 MySQL 的行情数据（含 stock_stk_limit 涨跌停数据）

### 1.2 用户
小团队 / 朋友圈（几个人共用）。

### 1.3 核心决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 视觉风格 | Bloomberg 终端风 | 信息密度最高，专业感最强 |
| 导航模式 | 仪表盘 + 钻取 (Drill-down) | 减少页面跳转，数据探索最流畅 |
| 首页内容 | 市场全景 (9 模块) | 一屏展示全部核心维度 |
| 前端技术 | Next.js + shadcn/ui + TailwindCSS + ECharts | 现代设计系统，高度可定制 |
| 后端架构 | FastAPI + 预计算 + TTL 缓存 | 平衡性能和复杂度，无额外依赖 |
| 筛选能力 | 高级多条件组合筛选器 | 支持估值/行情/资金多维度交叉筛选 |

## 2. 系统架构

### 2.1 三层架构

```
┌──────────────────────────────────────────────────────┐
│  FRONTEND — Next.js + shadcn/ui + TailwindCSS + ECharts │
│  首页仪表盘 | 行业详情 | 个股详情 | 高级筛选           │
│  资金流详情 | 龙虎榜详情                               │
└─────────────────────┬────────────────────────────────┘
                      │ REST API
┌─────────────────────┴────────────────────────────────┐
│  BACKEND — FastAPI + 预计算 + 缓存                    │
│  ┌────────┐ ┌──────────┐ ┌───────┐ ┌──────┐         │
│  │ market │ │ industry │ │ stock │ │ flow │         │
│  └────────┘ └──────────┘ └───────┘ └──────┘         │
│  ┌─────────┐ ┌──────────┐                            │
│  │ toplist │ │ screener │                            │
│  └─────────┘ └──────────┘                            │
│  ┌──────────────────────────────────────────┐        │
│  │  预计算层 + 内存 TTL 缓存 (cachetools)    │        │
│  └──────────────────────────────────────────┘        │
└─────────────────────┬────────────────────────────────┘
                      │ SQLAlchemy (只读)
┌─────────────────────┴────────────────────────────────┐
│  MySQL (stock_database)                              │
│  现有表: daily_kline, daily_basic, moneyflow,        │
│          moneyflow_hsgt, index_daily, top_list,      │
│          stock_basic, stock_stk_limit                      │
│  新增: precomputed_market, precomputed_industry,     │
│        precomputed_limit                             │
└──────────────────────────────────────────────────────┘
```

### 2.2 钻取导航层级

```
Level 0: 首页仪表盘 (市场全景)
  → Level 1: 行业详情页 (板块走势 + 行业内个股涨跌幅排行 + 行业资金流)
    → Level 2: 个股详情页 (全维度分析)
  → Level 1: 排行钻取 (完整排行表格，可排序/筛选)
    → Level 2: 个股详情页
  → Level 1: 北向资金详情 (沪深港通分项 + 历史趋势 + 净买入个股)
    → Level 2: 个股详情页
  → Level 1: 龙虎榜详情 (营业部买卖明细 + 历史上榜)
    → Level 2: 个股详情页
  → Level 1: 涨停详情 (涨停列表 + 连板梯队 + 概念分布)
    → Level 2: 个股详情页

独立入口: 高级筛选器
  → 筛选结果列表 → 个股详情页
```

面包屑导航贯穿全部层级，支持回退到任意层。

## 3. 前端设计

### 3.1 技术栈

- Next.js 14+ (App Router)
- shadcn/ui + TailwindCSS (Bloomberg 终端风定制)
- ECharts 5 (K线/Treemap/柱状/折线)
- SWR (数据加载 + 缓存)
- TypeScript

### 3.2 全局样式 (Bloomberg 终端风)

- 背景色: `#0a0a0a` (纯黑)
- 面板色: `#111111`
- 边框色: `#222222`
- 强调色: `#ff8c00` (橙色，用于标题/标签/高亮)
- 涨色: `#ff3333` (红)
- 跌色: `#33cc33` (绿)
- 字体: `monospace` 等宽字体
- 信息密度优先，紧凑间距

### 3.3 页面结构

#### 全局顶栏
- 左侧: Logo "STOCK BI" + 当前位置标识
- 中间: 全局搜索框（按名称/代码模糊搜索，回车跳转个股详情）
- 右侧: 日期显示

#### 首页仪表盘 (Level 0)

9 个核心模块，信息密集的一屏展示：

| 模块 | 数据来源 | 位置 | 钻取目标 |
|------|----------|------|----------|
| 指数行情条 | index_daily | 顶部通栏 | 指数详情 |
| 涨跌分布直方图 | daily_kline | 左上 | 区间个股列表 |
| 板块热力图 (Treemap) | precomputed_industry | 右上 (占2列) | 行业详情页 |
| 涨幅 TOP | daily_kline | 中左 | 个股详情 |
| 跌幅 TOP | daily_kline | 中中 | 个股详情 |
| 北向资金 (近30日折线) | moneyflow_hsgt | 中右 | 资金流详情 |
| 成交额 TOP | daily_kline | 下左 | 个股详情 |
| 换手率 TOP | daily_basic | 下中 | 个股详情 |
| 龙虎榜摘要 | top_list | 下方 (占2列) | 龙虎榜详情 |
| 涨停分析 | precomputed_limit | 下右 | 涨停详情 |

板块热力图仅支持「申万一级」行业分类（数据来源: stock_basic.industry 字段）。V1 不支持概念板块（无数据源）。
排行榜模块每个显示 TOP 5，右上角 "DRILL ›" 标识可钻取。

#### 行业详情页 (Level 1)

- 面包屑: 首页 › 行业名称
- 板块指数走势图 (如有) / 板块平均涨跌趋势
- 行业统计卡片: 涨跌家数、平均涨幅、总成交额、主力净流入
- **行业内个股涨跌幅排行表格**: 代码/名称/涨跌幅/价格/成交额/换手率/PE/主力净流入，可排序
- 点击个股行跳转个股详情

#### 个股详情页 (Level 2)

**固定区域 (页面上方):**
- 面包屑导航
- 股票头部: 名称 + 代码 + 行业 + 交易所 + 当前价格 + 涨跌幅
- 快速指标条: 开/高/低/昨收/成交量/成交额/换手率/振幅 (一行)
- K线图 (左侧，占 2/3 宽度):
  - 周期切换: 日K / 周K / 月K
  - 指标叠加: MA / MACD / KDJ / BOLL
  - 下方成交量柱状图
- 估值面板 (右侧，占 1/3):
  - PE(TTM) / PB / PS(TTM) / 总市值 / 流通市值 / 总股本 / 流通股 / 换手率
  - 同板块个股排名 (TOP 5)

**底部 Tab 切换 (5 个 Tab):**

| Tab | 内容 | 数据来源 |
|-----|------|----------|
| 资金流向 | 今日特大单(buy_elg_amount/sell_elg_amount)/大单(buy_lg_amount/sell_lg_amount)/中单(buy_md_amount/sell_md_amount)/小单(buy_sm_amount/sell_sm_amount)买卖明细 + 近30日主力净流入(net_mf_amount)柱状图 + 累计净流入曲线 | moneyflow |
| 估值趋势 | PE/PB/PS 历史走势图(可叠加) + 当前百分位 + 估值带(均值±标准差) | daily_basic |
| 大单明细 | 各档位买卖量趋势图 + 主力净流入占比 | moneyflow |
| 龙虎榜记录 | 历史上榜日期列表 + 营业部买卖额 + 上榜原因 | top_list |
| 历史行情 | 可滚动的历史日线数据表格 (日期/开高低收/量额/涨跌幅)，分页加载 | daily_kline |

#### 高级筛选页

- 筛选条件区: Tag 式条件组件，可动态添加/删除
- 每个条件: 字段选择 + 运算符(介于/大于/小于/等于) + 值输入
- 可用筛选字段 (20+ 个，三大维度):

**行情维度:** 涨跌幅、现价、成交额、成交量、换手率、振幅、连涨/连跌天数

**估值维度:** PE(TTM)、PB、PS(TTM)、总市值、流通市值、总股本、流通股本

**资金+分类维度:** 主力净流入(net_mf_amount)、特大单净流入(buy_elg_amount - sell_elg_amount)、大单净流入(buy_lg_amount - sell_lg_amount)、行业、市场(沪/深)、是否 ST (通过 `stock_basic.name LIKE 'ST%' OR LIKE '*ST%'` 判定，stock_basic 无 is_st 字段)

- 结果表格: 代码/名称/涨跌幅/PE/PB/市值/换手/主力净流入/行业，可排序
- 点击行跳转个股详情
- 支持导出 CSV

#### 其他 Level 1 钻取页

**北向资金详情:**
- 沪股通 / 深股通 分项趋势
- 历史净流入趋势 (日/周/月)
- 今日北向净买入个股 TOP

**龙虎榜详情:**
- 今日上榜个股列表 (涨幅/换手/买卖额/原因)
- 点击个股展开营业部明细

**涨停详情:**
- 涨停股完整列表 (数据来源: stock_stk_limit + precomputed_limit)
- 连板梯队 (5板/4板/3板/2板/首板)
- 涨停行业分布 (基于 stock_basic.industry，V1 不含概念分类)

## 4. 后端设计

### 4.1 目录结构

```
apps/stock_bi_v1/
├── backend/
│   ├── main.py                      # FastAPI app, CORS, 路由挂载
│   ├── infrastructure/
│   │   ├── database.py              # 复用 shared/stock_core/db.py
│   │   ├── settings.py              # 端口, 缓存 TTL 等配置
│   │   └── cache.py                 # TTL 缓存装饰器 (cachetools)
│   │
│   ├── models/
│   │   ├── db_models.py             # SQLAlchemy ORM (现有表映射 + 预计算表)
│   │   └── api_models.py            # Pydantic 响应 Schema
│   │
│   ├── modules/
│   │   ├── market/                  # 市场概览
│   │   │   ├── router.py            # 概览/指数/涨跌分布/涨停分析
│   │   │   ├── service.py           # 汇总计算逻辑
│   │   │   └── repository.py        # 预计算表 + 原始表查询
│   │   │
│   │   ├── industry/                # 行业板块
│   │   │   ├── router.py            # 板块列表/详情/成分股排行
│   │   │   ├── service.py           # 行业聚合计算
│   │   │   └── repository.py
│   │   │
│   │   ├── stock/                   # 个股
│   │   │   ├── router.py            # 详情/K线/估值趋势/同板块排名
│   │   │   ├── service.py           # 指标计算/多周期K线转换
│   │   │   └── repository.py
│   │   │
│   │   ├── flow/                    # 资金流向
│   │   │   ├── router.py            # 北向资金/个股资金/大单明细
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   │
│   │   ├── toplist/                 # 龙虎榜
│   │   │   ├── router.py            # 今日龙虎/历史记录
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   │
│   │   └── screener/                # 高级筛选
│   │       ├── router.py            # 筛选/可用条件/导出
│   │       ├── service.py           # 动态 SQL 构建
│   │       └── repository.py
│   │
│   └── precompute/                  # 预计算任务 (收盘后触发)
│       ├── runner.py                # 预计算入口
│       ├── market_summary.py        # 市场概览汇总
│       ├── industry_stats.py        # 行业统计
│       └── limit_analysis.py        # 涨跌停分析
│
├── frontend/                        # Next.js
│   ├── src/
│   │   ├── app/                     # App Router
│   │   │   ├── page.tsx             # 首页仪表盘
│   │   │   ├── industry/[id]/       # 行业详情 (L1)
│   │   │   ├── stock/[code]/        # 个股详情 (L2)
│   │   │   ├── flow/                # 资金流详情 (L1)
│   │   │   ├── toplist/             # 龙虎榜详情 (L1)
│   │   │   ├── limit/               # 涨停详情 (L1)
│   │   │   ├── screener/            # 高级筛选
│   │   │   └── layout.tsx           # 全局布局
│   │   ├── components/
│   │   │   ├── charts/              # ECharts 封装
│   │   │   ├── tables/              # 数据表格
│   │   │   ├── filters/             # 筛选器组件
│   │   │   └── ui/                  # shadcn/ui 基础组件
│   │   ├── lib/
│   │   │   ├── api.ts               # API 调用层
│   │   │   ├── hooks.ts             # SWR 数据加载 hooks
│   │   │   └── format.ts            # 数值格式化 (亿/万/百分比)
│   │   └── styles/
│   │       └── terminal.css         # Bloomberg 终端风全局样式
│   ├── tailwind.config.ts
│   └── package.json
│
└── run.sh
```

### 4.2 模块职责

**market 模块** — 仪表盘全量数据、指数行情、涨跌分布直方图、排行榜（涨幅/跌幅/成交/换手）、涨停分析

**industry 模块** — 板块热力图 Treemap 数据、行业详情、行业内个股涨跌幅排行

**stock 模块** — 个股 profile + 今日行情、K线数据（日/周/月转换）、估值历史时序、同板块排名、历史行情分页、模糊搜索

**flow 模块** — 北向资金趋势（沪/深/合计）、个股资金流（超大/大/中/小单）、大单明细

**toplist 模块** — 今日龙虎榜列表、个股历史上榜记录。**注意**: `top_list` 表的涨跌幅字段为 `pct_change`（非 `pct_chg`）。ORM 定义时使用 `pct_chg = Column("pct_change", Float)` 在 ORM 层完成别名映射，确保 API 响应统一使用 `pct_chg`

**screener 模块** — 可用筛选条件元数据、动态 SQL 组合筛选、结果排序分页、CSV 导出

**precompute 包** — 收盘后触发，计算市场概览汇总、行业统计、涨停分析，写入预计算表

### 4.3 API 路由表

#### Market 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/market/overview | 仪表盘全量数据 (预计算) |
| GET | /api/market/indices | 5大指数行情 |
| GET | /api/market/distribution?date= | 涨跌分布直方图 |
| GET | /api/market/ranking?sort_by=pct_chg&order=desc&limit=20 | 排行榜 |
| GET | /api/market/limit-stats?date= | 涨停分析统计 (返回 precomputed_limit 聚合数据: 涨停数/跌停数/炸板率/连板梯队) |
| GET | /api/market/limit-list?type=up&date= | 涨停/跌停股列表 (返回 precomputed_limit.up_limit_stocks 或 down_limit_stocks JSON 数组) |

#### Industry 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/industry/heatmap?date= | 板块热力图 Treemap 数据 |
| GET | /api/industry/detail?name= | 行业详情 (指数走势+统计，name 为 URL 编码的行业名称) |
| GET | /api/industry/stocks?name=&sort_by=pct_chg&order=desc | 行业内个股排行 |

#### Stock 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stock/search?q= | 模糊搜索 (代码/名称)，**必须在 {code} 路由前注册** |
| GET | /api/stock/{code}/profile | 基本信息 + 今日行情 + 估值 |
| GET | /api/stock/{code}/kline?period=daily&start=&end= | K线数据 (日/周/月) |
| GET | /api/stock/{code}/valuation-history?start=&end= | PE/PB/PS 历史时序 |
| GET | /api/stock/{code}/peers | 同板块个股排名 |
| GET | /api/stock/{code}/history?start=&end=&page=&size= | 历史行情 (分页) |

#### Flow 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/flow/north?days=30 | 北向资金趋势 |
| GET | /api/flow/stock/{code}?days=30 | 个股资金流 |
| GET | /api/flow/stock/{code}/detail?date= | 某日各档位(特大/大/中/小单)买卖额明细，与资金流向Tab共用 moneyflow 数据 |

#### TopList 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/toplist/daily?date= | 今日龙虎榜列表 |
| GET | /api/toplist/stock/{code} | 个股历史上榜记录 |

#### Screener 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/screener/filters | 可用筛选条件列表 |
| POST | /api/screener/query | 执行筛选 (body: conditions, sort, page) |
| POST | /api/screener/export?format=csv | 导出筛选结果 (body: 与 query 相同的 conditions，最大 5000 行。响应: Content-Type: text/csv, Content-Disposition: attachment) |

#### Precompute 触发
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/precompute/{trade_date} | 触发预计算 (由 daily_runner.py 在数据入库后调用) |

### 4.4 预计算层

每日收盘后由 `stock_data_platform` 的 daily job 触发。集成方式: 沿用现有 `sync_stock_bi` 模式，在 `daily_runner.py` 末尾（**所有 jobs 全部完成后，包括 stock_stk_limit**）新增一步 HTTP POST 调用 `POST /api/precompute/{trade_date}` 触发预计算。后端需新增此 endpoint，内部调用 `precompute/runner.py` 执行计算并写入预计算表。

> **顺序要求**: 预计算依赖 `stock_stk_limit` 数据（涨停判定），而 `stk_limit` job 无 `trigger_stock_bi_sync` 标记。因此 precompute 调用必须放在 `daily_runner.py` 所有 jobs 循环结束之后，不能挂在单个 job 的 trigger 上。

**precomputed_market** — 每日一行
- `trade_date` DATE NOT NULL PRIMARY KEY
- `distribution` JSON: `{"-10~-7": n, "-7~-5": n, "-5~-3": n, "-3~0": n, "0": n, "0~3": n, "3~5": n, "5~7": n, "7~10": n}`
- `up_limit_count` INT, `down_limit_count` INT, `flat_count` INT
- `total_amount` DECIMAL(20,2)
- `top_gainers` JSON: `[{ts_code, name, pct_chg, close, amount}]` (TOP 20)
- `top_losers` JSON: 同上
- `top_volume` JSON: `[{ts_code, name, pct_chg, close, amount}]` (TOP 20)
- `top_turnover` JSON: `[{ts_code, name, pct_chg, close, turnover_rate}]` (TOP 20，需 JOIN daily_basic)

**precomputed_industry** — 每日每行业一行 (主键: trade_date + industry)
- `trade_date` DATE NOT NULL
- `industry` VARCHAR(50) NOT NULL
- `avg_pct_chg` DECIMAL(8,4)
- `total_amount` DECIMAL(20,2)
- `up_count` INT, `down_count` INT
- `net_mf_amount` DECIMAL(20,2) (主力净流入合计)
- `stock_count` INT (行业内股票总数)

**precomputed_limit** — 每日一行
- `trade_date` DATE NOT NULL PRIMARY KEY
- `up_limit_stocks` JSON: `[{ts_code, name, pct_chg, close, amount, consecutive_days, industry}]`
- `down_limit_stocks` JSON: `[{ts_code, name, pct_chg, close, amount, industry}]`
- `up_count` INT, `down_count` INT, `broken_count` INT
- `broken_rate` DECIMAL(5,2)
- `tier_stats` JSON: `{"1": count, "2": count, "3": count, ...}` (连板梯队，key 为字符串)

> **预计算数据来源与算法**:
> - 涨停判定: `stock_stk_limit` 表提供每日个股的涨停价 (`up_limit`) 和跌停价 (`down_limit`)。通过 JOIN `daily_kline` 判断 `close >= up_limit` 确定涨停，`close <= down_limit` 确定跌停。
> - 价格/成交数据: 从 `daily_kline` 获取 `pct_chg`, `close`, `amount`。
> - 行业信息: 从 `stock_basic` 获取 `industry`。
> - `consecutive_days` (连板天数): 向前回溯 `daily_kline`，计算连续 N 日满足 `close >= up_limit` 的天数。
> - `broken_count` (炸板): 当日盘中触及涨停但收盘未封住，即 `high >= up_limit AND close < up_limit`（从 `daily_kline` + `stock_stk_limit` 推导）。
> - 股票名称: 从 `stock_basic` 获取 `name`。

### 4.5 缓存策略

使用 `cachetools.TTLCache` 实现内存级缓存：

| 数据类型 | TTL | 说明 |
|----------|-----|------|
| 仪表盘 overview | 5 min | 预计算数据变化不频繁 |
| 个股日 K线 | 5 min | 收盘后数据入库一次，无需频繁刷新 |
| 周K/月K线 | 1 hour | 历史周/月K不变，仅最新周/月可能更新 |
| 排行榜 | 2 min | 首页高频请求 |
| 筛选结果 | 30 sec | 条件变化大，不宜长缓存 |
| 行业热力图 | 5 min | 与仪表盘同步 |
| 搜索结果 | 10 min | stock_basic 变化极少 |

### 4.6 性能优化：索引规划

在现有表上新增组合索引以支撑高级筛选和排行查询：

```sql
-- daily_kline: 按日期查询 + 涨跌幅排序
CREATE INDEX idx_dk_date_pctchg ON daily_kline(trade_date, pct_chg);
CREATE INDEX idx_dk_date_amount ON daily_kline(trade_date, amount);

-- daily_basic: 估值筛选
CREATE INDEX idx_db_date_pe ON daily_basic(trade_date, pe_ttm);
CREATE INDEX idx_db_date_pb ON daily_basic(trade_date, pb);
CREATE INDEX idx_db_date_mv ON daily_basic(trade_date, total_mv);
CREATE INDEX idx_db_date_turnover ON daily_basic(trade_date, turnover_rate);

-- moneyflow: 资金流筛选
CREATE INDEX idx_mf_date_net ON moneyflow(trade_date, net_mf_amount);

-- stock_basic: 行业筛选
CREATE INDEX idx_sb_industry ON stock_basic(industry);
```

### 4.7 数据库迁移方案

V1 使用 `Base.metadata.create_all(engine)` 自动建预计算表。索引通过启动脚本执行 `CREATE INDEX IF NOT EXISTS` 添加。与 stock_bi 一致的简单方案。

### 4.8 动态 SQL 构建 (Screener)

筛选器的核心是动态构建多表 JOIN + WHERE 条件：

```
基础表: daily_kline (最新交易日)
LEFT JOIN daily_basic ON (ts_code, trade_date)
LEFT JOIN moneyflow ON (ts_code, trade_date)
LEFT JOIN stock_basic ON (ts_code)
WHERE condition1 AND condition2 AND ...
ORDER BY sort_field
LIMIT page_size OFFSET page * page_size
```

- 条件白名单校验（只允许预定义的字段名，防 SQL 注入）
- 使用 SQLAlchemy ORM 构建查询，非拼接 SQL
- 筛选结果缓存 30 秒（相同条件组合命中缓存）

## 5. 技术栈汇总

### 前端
- Next.js 14+ (App Router)
- shadcn/ui + TailwindCSS
- ECharts 5
- SWR (数据获取)
- TypeScript

### 后端
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0
- Pandas (数据处理、周K/月K转换)
- PyMySQL
- Pydantic v2
- cachetools (TTL 缓存)

### 基础设施
- MySQL 8.0 (共用 stock_database，只读现有表)
- 共用 shared/stock_core (配置/DB)

## 6. 与现有系统的关系

- **stock_data_platform**: 数据生产者。stock_bi_v1 只读取 MySQL 数据。预计算任务由 data_platform 的 daily job 触发
- **stock_bi (旧版)**: 并行存在，stock_bi_v1 是其替代品，不依赖旧版任何代码
- **stock_backtest**: 并行应用，互不依赖。共用 MySQL 和 shared/stock_core
- **shared/stock_core**: 复用 config.py 和 db.py

## 7. 附录：视觉稿索引

brainstorm 过程中的可视化设计稿：

| 文件 | 内容 |
|------|------|
| 01-visual-style.html | 三种视觉风格对比 (选定 Bloomberg 终端风) |
| 02-navigation-layout.html | 三种导航结构对比 (选定仪表盘+钻取) |
| 03-dashboard-layout.html | 首页仪表盘完整 wireframe (9 模块) |
| 04-design-architecture.html | 系统架构图 + 钻取层级 |
| 05-design-stock-detail.html | 个股详情页 wireframe |
| 06-design-screener-backend.html | 高级筛选器 + 后端模块 + API 路由 |
