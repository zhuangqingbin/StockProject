# Stock Backtest Platform 设计文档

> 日期: 2026-03-15
> 状态: Draft
> 视觉稿: `apps/stock_backtest/brainstorm/` 目录下的 HTML 文件

## 1. 概述

### 1.1 目标
在 `apps/stock_backtest/` 下新建一个量化回测平台，提供：
- 基于 Backtrader 的策略回测引擎
- React 前端界面用于策略管理、回测配置、结果分析和策略对比
- Jupyter Notebook 集成用于高级数据探索
- 数据来源为 `stock_data_platform` 通过每日任务写入 MySQL 的行情数据

### 1.2 用户
小团队 / 朋友圈（几个人共用），需要基本的策略分享和结果对比。

### 1.3 核心决策
| 决策项 | 选择 | 理由 |
|--------|------|------|
| 回测引擎 | Backtrader | 社区成熟，已有实验基础 |
| 数据范围 | 全数据源 + 可扩展 | 所有 MySQL 表均可接入，未来新数据源插件式注册 |
| 前端技术 | React + Ant Design + ECharts | 组件化管理复杂交互，生态丰富 |
| Notebook 定位 | 辅助角色 | 前端为主操作界面，Notebook 用于高级分析 |
| 策略编写 | 模板配置 + 自定义代码 | 降低门槛同时保留灵活性 |
| 结果分析 | 全维度 | 收益、交易、风险归因、策略对比、参数敏感性 |
| 架构模式 | 单体 + ProcessPoolExecutor | 零额外依赖，小团队够用，未来可升级为 Celery |
| 交付范围 | 功能完整的 V1 | 一步到位 |

## 2. 系统架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────┐
│  React Frontend (Vite + Ant Design + ECharts)   │
│  策略管理 | 回测配置 | 结果分析 | 策略对比 | Notebook │
└───────────────────┬─────────────────────────────┘
                    │ REST API + WebSocket
┌───────────────────┴─────────────────────────────┐
│  FastAPI Backend                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Strategy │ │ Backtest │ │ Analysis │        │
│  │  Router  │ │  Router  │ │  Router  │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌─────────────────────────────────────┐        │
│  │  Engine (ProcessPoolExecutor)       │        │
│  │  Backtrader + DataFeed + Metrics    │        │
│  └─────────────────────────────────────┘        │
└───────────────────┬─────────────────────────────┘
                    │ SQLAlchemy
┌───────────────────┴─────────────────────────────┐
│  MySQL (stock_database)                         │
│  现有表: daily_kline, daily_basic, moneyflow... │
│  新增表: strategies, backtest_runs,             │
│          backtest_trades, backtest_daily         │
└─────────────────────────────────────────────────┘
```

### 2.2 核心数据流

1. **配置回测** — 用户选择策略模板或编写代码，设置参数、时间范围、标的池
2. **提交任务** — `POST /api/backtest/run` → 创建 `backtest_runs` 记录 (pending) → 提交到进程池
3. **执行回测** — 子进程加载策略代码 → 数据适配层从 MySQL 读取数据 → 转为 `bt.feeds` → Backtrader 执行
4. **进度推送** — 子进程通过数据库轮询方式报告进度（子进程直接更新 `backtest_runs.progress`），主进程 asyncio task 定时查询 → WebSocket 推送
5. **结果存储** — 提取交易记录、每日净值、绩效指标 → 写入 MySQL
6. **结果展示** — 前端拉取结果 → 收益曲线、交易明细、风险指标、归因分析

## 3. 后端设计

### 3.1 目录结构

```
apps/stock_backtest/
├── backend/
│   ├── main.py                      # FastAPI app, 挂载路由, 启动事件
│   ├── infrastructure/
│   │   ├── database.py              # 复用 shared/stock_core/db.py
│   │   └── settings.py              # 配置项 (进程池大小, 端口等)
│   │
│   ├── models/
│   │   ├── db_models.py             # SQLAlchemy ORM 模型
│   │   └── api_models.py            # Pydantic 请求/响应 Schema
│   │
│   ├── modules/
│   │   ├── strategy/                # 策略管理模块
│   │   │   ├── router.py            # CRUD API
│   │   │   ├── service.py           # 业务逻辑
│   │   │   └── repository.py        # 数据库操作
│   │   │
│   │   ├── backtest/                # 回测执行模块
│   │   │   ├── router.py            # 提交/状态/取消 API
│   │   │   ├── service.py           # 任务调度, 进程池管理
│   │   │   ├── repository.py        # 回测记录读写
│   │   │   └── websocket.py         # 进度推送
│   │   │
│   │   ├── analysis/                # 结果分析模块
│   │   │   ├── router.py            # 指标/归因/对比 API
│   │   │   ├── service.py           # 绩效计算, 风险分析
│   │   │   └── repository.py        # 结果数据查询
│   │   │
│   │   └── notebook/                # Notebook 管理模块
│   │       ├── router.py            # 启动/停止/列表 API
│   │       └── service.py           # JupyterLab 进程管理
│   │
│   └── engine/                      # 回测引擎核心 (独立于 FastAPI)
│       ├── runner.py                # Backtrader 回测入口, 子进程执行
│       ├── data_feed.py             # MySQL → bt.feeds.PandasData 适配
│       ├── data_registry.py         # 数据源注册表, 插件式扩展
│       ├── strategy_loader.py       # 动态加载用户策略代码
│       ├── result_extractor.py      # 从 Cerebro 提取交易/净值/指标
│       └── metrics.py               # 夏普/回撤/年化/归因 计算
│
├── frontend/                        # React (Vite + Ant Design + ECharts)
│   ├── src/
│   │   ├── pages/                   # 五大页面组件
│   │   ├── components/              # 通用组件 (图表, 表格, 编辑器)
│   │   ├── services/                # API 调用层
│   │   ├── stores/                  # 状态管理 (Zustand)
│   │   └── hooks/                   # WebSocket, 数据加载等
│   └── package.json
│
├── notebooks/                       # Jupyter 模板
│   ├── strategy_dev_template.ipynb
│   ├── data_explore_template.ipynb
│   └── result_analysis_template.ipynb
│
├── templates/                       # 内置策略模板
│   ├── ma_crossover.py              # 均线交叉
│   ├── breakout.py                  # 突破策略
│   ├── mean_reversion.py            # 均值回归
│   ├── momentum.py                  # 动量策略
│   └── money_flow.py               # 资金流向
│
├── tests/
├── requirements.txt
└── run.sh
```

### 3.2 模块职责

**strategy 模块** — 策略 CRUD，模板管理，代码验证（校验继承自 bt.Strategy）

**backtest 模块** — 任务提交与调度，ProcessPoolExecutor 管理，进度推送，任务取消

**analysis 模块** — 绩效指标计算，风险归因，策略对比，参数敏感性分析

**notebook 模块** — JupyterLab 进程启停，模板管理，最近文件列表

**engine 包** — 独立于 FastAPI 的回测引擎核心，可单独在 Notebook 中使用

### 3.3 回测引擎执行流程

```
① 接收请求 (FastAPI Router)
   验证参数 → 创建 backtest_runs 记录 (status=pending) → 返回 run_id

② 提交进程池 (ProcessPoolExecutor)
   submit(run_backtest, run_id, config) → status=running

③ 子进程执行 (run_backtest)
   3a. 创建独立 DB 连接 — 子进程必须新建 SQLAlchemy engine，不继承父进程连接池
   3b. 加载策略代码 — strategy_loader 动态导入, 校验 bt.Strategy 继承
   3c. 准备数据 — data_registry 查找 Plugin → query MySQL → DataFrame → bt.feeds
   3d. 配置 Cerebro — 添加 DataFeed, Strategy, Broker, Analyzer, Observer
   3e. 执行回测 — cerebro.run(), 采样式更新进度到 DB (每 100 个 bar)
   3f. 提取结果 — result_extractor 解析交易记录、每日净值
   3g. 关闭 DB 连接 — engine.dispose()

④ 结果持久化
   写入 backtest_trades + backtest_daily → 计算 metrics → 更新 backtest_runs

⑤ 通知前端
   Future 回调 → WebSocket 推送完成事件
```

**子进程 DB 隔离**: `ProcessPoolExecutor` 创建的子进程不得共享父进程的 SQLAlchemy engine（fork 会复制 socket fd，导致连接池损坏）。`runner.py` 中的 `run_backtest()` 入口必须调用 `create_engine()` 创建局部 engine，执行完毕后 `dispose()`。

**任务取消机制**: `Future.cancel()` 只能取消未开始的任务。对已运行的任务，使用 `multiprocessing.Event` 作为中断标志传入子进程（Event 在 fork 后可共享），在 Backtrader 的 `next()` 回调中检查该标志，若已设置则调用 `cerebro.runstop()` 提前终止。取消 API 设置 Event + 更新 `backtest_runs.status` 为 `cancelled`。

### 3.4 数据源插件机制

```python
class DataFeedPlugin(ABC):
    name: str           # "daily_kline"
    table: str          # MySQL 表名
    columns: list       # 可用列
    column_map: dict    # TuShare 列名 → Backtrader 标准列名映射
                        # 例: {"vol": "volume", "ts_code": None}
                        # None 表示剔除该列

    def query(self, symbol, start, end) -> DataFrame: ...
    def to_bt_feed(self, df) -> bt.feeds.PandasData: ...
        # 内部完成: 列名重命名 (column_map) → 剔除多余列 → 构造 PandasData
```

**列名映射说明**: Backtrader 内部要求标准列名 (`open`, `high`, `low`, `close`, `volume`, `openinterest`)，但 MySQL 表中的列名来自 TuShare（如 `vol` 而非 `volume`）。每个 Plugin 在 `to_bt_feed()` 中负责列名重命名和过滤。

新增数据源步骤：
1. 实现 `DataFeedPlugin` 接口（包括 `column_map`）
2. 在 `data_registry.py` 中注册
3. 前端数据源选择列表自动更新

**V1 内置数据源 Plugin**: `daily_kline`, `daily_basic`, `moneyflow`, `index_daily`, `top_list`, `stock_basic`（静态数据，用于行业归因）

### 3.5 进度推送机制

- **子进程 → DB**: 子进程在 Backtrader 的 `next()` 回调中采样式上报进度（每 100 个 bar 或每 2 秒），直接 UPDATE `backtest_runs.progress`（使用子进程自己的 DB 连接）
- **主进程 → 前端**: 后台 asyncio task 每秒查询活跃任务的 `progress` 字段，通过 WebSocket 推送给订阅的客户端

**为什么不用 `multiprocessing.Queue`**: `ProcessPoolExecutor.submit()` 的参数必须可 pickle，而 `multiprocessing.Queue` 不可 pickle。`Manager().Queue()` 可行但增加复杂度。直接用 DB 轮询最简单可靠，且进度信息天然持久化。

### 3.6 策略代码安全

小团队信任模型 — 用户代码在子进程中拥有完整权限，不做代码级沙箱（对小团队而言过度工程化）。安全边界仅通过资源控制实现：

- **动态 import 加载**: `importlib` 加载用户 .py 文件。注意：导入时顶层代码会执行，与 `exec` 等价，安全性依赖于团队成员间的信任
- **结构校验**: 导入后校验必须继承 `bt.Strategy` 且实现 `next()` 方法
- **超时控制**: 每任务可配置，默认 10 分钟（通过 `backtest_runs` 配置或 `settings.py` 全局默认值）。超时后通过 `os.kill(pid, SIGTERM)` 终止子进程，更新 status 为 `failed`
- **子进程隔离**: 策略代码崩溃不影响主服务
- **并发限制**: 最大并发任务数由 `settings.py` 中 `MAX_WORKERS` 控制（默认 4）

### 3.7 API 路由表

#### Strategy 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/strategies | 策略列表 (支持 ?author= 筛选) |
| GET | /api/strategies/{id} | 策略详情 |
| POST | /api/strategies | 创建策略 |
| PUT | /api/strategies/{id} | 更新策略 |
| DELETE | /api/strategies/{id} | 删除策略 |
| GET | /api/strategies/templates | 可用模板列表 (从 templates/ 目录扫描) |
| GET | /api/strategies/templates/{template_id} | 模板详情 (含代码和参数定义) |

#### Backtest 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/backtest/run | 提交回测任务，返回 run_id |
| GET | /api/backtest/runs | 回测记录列表 (支持 ?strategy_id=, ?status= 筛选) |
| GET | /api/backtest/runs/{run_id} | 回测详情 (含 KPI 指标) |
| POST | /api/backtest/runs/{run_id}/cancel | 取消运行中的任务 |
| DELETE | /api/backtest/runs/{run_id} | 删除回测记录 |
| POST | /api/backtest/grid-search | 批量参数扫描 (见下文参数敏感性设计) |
| WS | /ws/backtest | WebSocket 进度推送 |

#### Analysis 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analysis/{run_id}/trades | 交易明细列表 |
| GET | /api/analysis/{run_id}/daily | 每日净值序列 (支持 ?start=&end= 日期范围) |
| GET | /api/analysis/{run_id}/positions?date= | 指定日期的持仓快照 (从 trades 聚合计算) |
| GET | /api/analysis/{run_id}/industry-exposure | 行业暴露分布 |
| GET | /api/analysis/{run_id}/rolling?metric=sharpe&window=60 | 滚动指标 |
| GET | /api/analysis/{run_id}/monthly-returns | 月度收益热力图数据 |
| GET | /api/analysis/compare?run_ids=1,2,3 | 多策略对比 (指标 + 每日净值叠加) |
| GET | /api/analysis/grid-search/{group_id} | 参数敏感性结果矩阵 |

#### Notebook 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/notebook/start | 启动 JupyterLab |
| POST | /api/notebook/stop | 停止 JupyterLab |
| GET | /api/notebook/status | JupyterLab 运行状态和 URL |
| GET | /api/notebook/templates | Notebook 模板列表 |
| GET | /api/notebook/recent | 最近打开的 Notebook 列表 |

#### Data 模块
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/data/feeds | 可用数据源列表 (从 data_registry 获取) |
| GET | /api/data/symbols?keyword= | 股票搜索 (模糊搜索 stock_basic) |

### 3.8 参数敏感性分析

**触发方式**: 前端策略对比页提供"参数扫描"入口，用户选择一个策略 + 一个参数 + 参数值范围（如短期均线 3/5/8/10/15 日），提交 `POST /api/backtest/grid-search`。

**执行模型**: 后端为每组参数创建独立的 `backtest_runs` 记录，共享同一个 `grid_search_group_id`（新增字段），批量提交到进程池。每个 run 独立执行、独立存储结果。

**结果查询**: `GET /api/analysis/grid-search/{group_id}` 返回同组所有 run 的核心指标，前端渲染为柱状图/热力图。

### 3.9 数据库迁移方案

V1 沿用 `Base.metadata.create_all(engine)` 方式在应用启动时自动建表（与 stock_bi 一致）。此方式仅支持新建表，不支持变更已有表结构（加列、加索引）。V2 如需迭代表结构，引入 Alembic 做版本化迁移。

## 4. 数据库设计

共用 `stock_database`，新增 4 张表。

### 4.1 strategies — 策略定义

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| name | VARCHAR(100) | 策略名称 |
| description | TEXT | 策略描述 |
| source_type | ENUM('template','custom') | 模板 / 自定义 |
| template_id | VARCHAR(50) NULL | 模板标识 (如 ma_crossover)。source_type='template' 时必填 |
| code | TEXT NULL | 策略 Python 代码。source_type='custom' 时必填，'template' 时为 NULL（代码由 template_id 动态加载） |
| default_params | JSON | 默认参数 `{"fast": 5, "slow": 20}` |
| required_feeds | JSON | 所需数据源 `["daily_kline", "moneyflow"]` |
| author | VARCHAR(50) | 作者 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**模板 vs 自定义加载路径**: `strategy_loader.py` 根据 `source_type` 分两条路径：
- `template`: 从 `templates/{template_id}.py` 文件加载代码，`default_params` 存用户覆盖的参数
- `custom`: 从 `code` 列加载用户编写的完整策略代码

### 4.2 backtest_runs — 回测运行记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| strategy_id | INT FK | 关联策略 |
| params | JSON | 本次参数覆盖 |
| symbols | JSON | 标的列表 `["000001.SZ", ...]` |
| start_date | DATE | 回测开始日期 |
| end_date | DATE | 回测结束日期 |
| initial_cash | DECIMAL(15,2) | 初始资金 |
| commission_rate | DECIMAL(8,6) | 手续费率 |
| benchmark | VARCHAR(20) | 基准指数代码 |
| data_feeds | JSON | 使用的数据源 |
| status | ENUM('pending','running','completed','failed','cancelled') | 状态 |
| progress | SMALLINT | 进度 0-100 |
| error_message | TEXT | 失败原因 |
| total_return | DECIMAL(12,6) NULL | 总收益率 (小数形式，0.183 = 18.3%) |
| annual_return | DECIMAL(12,6) NULL | 年化收益率 |
| max_drawdown | DECIMAL(12,6) NULL | 最大回撤 |
| sharpe_ratio | DECIMAL(8,4) NULL | 夏普比率 |
| win_rate | DECIMAL(6,4) NULL | 胜率 |
| profit_loss_ratio | DECIMAL(8,4) NULL | 盈亏比 |
| metrics | JSON | 完整绩效指标 (含上述 + 其他辅助指标) |
| grid_search_group_id | VARCHAR(36) NULL | 参数扫描组 ID (UUID)，同组 run 共享 |
| submitted_by | VARCHAR(50) | 提交人 |
| created_at | DATETIME | 提交时间 |
| finished_at | DATETIME | 完成时间 |

**索引**: `INDEX idx_strategy_id (strategy_id)`, `INDEX idx_status (status)`, `INDEX idx_annual_return (annual_return)`, `INDEX idx_grid_group (grid_search_group_id)`

**核心指标独立列**: 年化收益、最大回撤、夏普、胜率、盈亏比提升为独立 DECIMAL 列并建索引，支持策略对比页面的排序和筛选。其余辅助指标保留在 `metrics` JSON 列中。

### 4.3 backtest_trades — 交易明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| run_id | INT FK | 关联回测记录 |
| trade_date | DATE | 交易日期 |
| symbol | VARCHAR(20) | 标的代码 |
| direction | ENUM('buy','sell') | 买卖方向 |
| price | DECIMAL(12,4) | 成交价格 |
| size | INT | 成交数量 |
| commission | DECIMAL(10,4) | 手续费 |
| pnl | DECIMAL(12,4) | 本笔盈亏 (卖出时计算) |

**索引**: `INDEX idx_run_id (run_id)`

### 4.4 backtest_daily — 每日净值快照

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| run_id | INT FK | 关联回测记录 |
| trade_date | DATE | 交易日 |
| portfolio_value | DECIMAL(15,2) | 组合总价值 |
| cash | DECIMAL(15,2) | 现金余额 |
| daily_return | DECIMAL(12,8) | 当日收益率 (小数形式，0.053 = 5.3%) |
| cumulative_return | DECIMAL(12,8) | 累计收益率 |
| drawdown | DECIMAL(12,8) | 当前回撤 |

**索引**: `UNIQUE KEY uq_run_date (run_id, trade_date)`, `INDEX idx_run_id (run_id)`

**约定**: 所有收益率/回撤字段以小数形式存储（0.053 = 5.3%，-0.124 = -12.4%）。

**持仓数据**: 持仓快照不存在 `backtest_daily` 中（避免 JSON 膨胀），而是通过 `backtest_trades` 按时间聚合计算得出。前端"持仓分析" Tab 请求时后端实时计算。

## 5. 前端设计

### 5.1 技术栈

- React 18 + TypeScript
- Vite (构建)
- Ant Design 5 (UI 组件库)
- ECharts 5 (图表)
- Monaco Editor (代码编辑器)
- Zustand (状态管理)
- React Router (路由)

### 5.2 Zustand Store 划分

| Store | 职责 | 跨页面 |
|-------|------|--------|
| `useStrategyStore` | 策略列表、当前编辑的策略、模板列表 | 是 |
| `useBacktestStore` | 当前运行中的任务 ID 和进度、回测记录列表 | 是 |
| `useAnalysisStore` | 当前查看的 run 结果、对比选中的 run_ids | 是 |
| `useWsStore` | WebSocket 连接状态、重连逻辑 | 是 |

### 5.3 页面结构

顶部导航栏切换五大模块：

#### 页面一：策略管理
- **左侧**: 策略列表，卡片式展示，标记「模板」/「自定义」，显示最后回测结果摘要
- **右侧**: 策略编辑器，两种模式切换
  - 「模板配置」: 下拉选择模板 + 参数表单（均线天数、止损止盈、仓位管理等）
  - 「代码编辑」: Monaco Editor 编辑 Python 策略代码，语法高亮
- **操作**: 新建策略、编辑、删除、复制

#### 页面二：回测中心
- **左侧**: 回测配置面板
  - 选择策略（下拉）
  - 回测区间（日期范围选择器）
  - 标的选择（搜索 + Tag 方式添加多只股票）
  - 初始资金、手续费率
  - 基准指数选择
  - 数据源多选（日线行情、基本面、资金流、龙虎榜等）
  - 「开始回测」按钮
- **右侧**: 回测记录列表
  - 卡片式展示，带状态标识（完成/运行中+进度条/失败+错误信息）
  - 点击跳转到结果分析页

#### 页面三：结果分析
- **顶部**: KPI 卡片行 — 总收益、年化收益、最大回撤、夏普比率、胜率、盈亏比
- **中部**: 图表区
  - 收益曲线 vs 基准（叠加折线图）
  - 回撤曲线
- **底部**: Tab 切换
  - 交易明细（表格，买卖方向、价格、数量、盈亏）
  - K 线买卖点（ECharts K 线图 + 买卖标注）
  - 持仓分析（持仓集中度、个股贡献）
  - 行业暴露（行业分布饼图/柱状图）
  - 滚动指标（滚动夏普、滚动回撤的时序图）
  - 风险归因（月度热力图、因子贡献）

#### 页面四：策略对比
- **顶部**: 收益曲线叠加图（多策略 + 基准，可勾选显隐）
- **中部**: 指标对比表（年化收益、最大回撤、夏普、胜率、盈亏比、交易次数，带排名高亮）
- **底部**: 参数敏感性分析（柱状图，展示某参数不同取值下的年化收益）

#### 页面五：Notebook 入口
- 一键启动 JupyterLab（预装回测环境和数据连接）
- Notebook 模板列表（策略开发、数据探索、结果分析）
- 最近打开的 Notebook 列表

## 6. 绩效指标体系

### 6.1 收益指标
- 总收益率
- 年化收益率
- 月度收益率序列
- 超额收益 (vs 基准)
- Alpha / Beta

### 6.2 风险指标
- 最大回撤（幅度 + 持续天数）
- 年化波动率
- 下行波动率
- VaR (95%)
- 最大连续亏损天数

### 6.3 风险调整指标
- 夏普比率
- 索提诺比率
- Calmar 比率
- 信息比率
- 收益回撤比

### 6.4 交易统计
- 总交易次数
- 胜率
- 盈亏比
- 平均持仓天数
- 最大单笔盈利 / 亏损

### 6.5 归因分析
- 行业暴露分布
- 个股贡献排名
- 滚动夏普 / 回撤
- 月度热力图
- 参数敏感性矩阵

## 7. 内置策略模板 (V1)

| 模板 | 文件 | 参数 | 数据源 |
|------|------|------|--------|
| 均线交叉 | ma_crossover.py | fast_period, slow_period, stop_loss, take_profit | daily_kline |
| 突破策略 | breakout.py | lookback, breakout_pct, hold_days | daily_kline |
| 均值回归 | mean_reversion.py | period, std_dev, exit_threshold | daily_kline, daily_basic |
| 动量策略 | momentum.py | momentum_period, top_n, rebalance_days | daily_kline, daily_basic |
| 资金流向 | money_flow.py | flow_threshold, hold_days, net_flow_type | daily_kline, moneyflow |

## 8. 技术栈汇总

### 前端
- React 18 + TypeScript
- Vite (构建工具)
- Ant Design 5 (UI 组件)
- ECharts 5 (图表)
- Monaco Editor (代码编辑器)
- Zustand (状态管理)
- React Router (路由)

### 后端
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- Backtrader (回测引擎)
- Pandas / NumPy (数据处理)
- PyMySQL (数据库驱动)
- Pydantic v2 (数据验证)

### 基础设施
- MySQL 8.0 (共用 stock_database)
- JupyterLab (Notebook 环境)
- WebSocket (实时通信)
- ProcessPoolExecutor (任务执行)
- 共用 shared/stock_core (配置/DB)

## 9. 与现有系统的关系

- **stock_data_platform**: 数据生产者，通过每日任务写入 MySQL。stock_backtest 只读取这些数据，不写入
- **stock_bi**: 并行应用，互不依赖。共用 MySQL 和 shared/stock_core
- **shared/stock_core**: 复用 config.py（数据库连接配置）和 db.py（SQLAlchemy engine）
- **experiments/backtrader** (如存在): 已有的探索性 Notebook，可作为策略模板设计的参考

## 10. 附录：视觉稿索引

brainstorm 过程中的可视化设计稿保存在 `apps/stock_backtest/brainstorm/` 目录：

| 文件 | 内容 |
|------|------|
| architecture-approaches.html | 三种架构方案对比 |
| design-architecture.html | 系统架构图与数据流 |
| design-frontend.html | 五大页面 wireframe |
| design-backend-db.html | 后端模块、数据库 schema、策略模板 |
| design-engine-detail.html | 回测引擎流程、进度推送、安全性、指标体系 |
