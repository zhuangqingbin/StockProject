# Stock Backtest Platform 设计文档

> 日期: 2026-03-15
> 状态: Draft
> 视觉稿: `.superpowers/brainstorm/71511-1773510849/` 目录下的 HTML 文件

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
4. **进度推送** — 子进程通过 `multiprocessing.Queue` 报告进度 → 主进程 asyncio task 轮询 → WebSocket 推送
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
   3a. 加载策略代码 — strategy_loader 动态导入, 校验 bt.Strategy 继承
   3b. 准备数据 — data_registry 查找 Plugin → query MySQL → DataFrame → bt.feeds
   3c. 配置 Cerebro — 添加 DataFeed, Strategy, Broker, Analyzer, Observer
   3d. 执行回测 — cerebro.run(), 通过 Queue 报告进度
   3e. 提取结果 — result_extractor 解析交易记录、每日净值

④ 结果持久化
   写入 backtest_trades + backtest_daily → 计算 metrics → 更新 backtest_runs

⑤ 通知前端
   Future 回调 → WebSocket 推送完成事件
```

### 3.4 数据源插件机制

```python
class DataFeedPlugin(ABC):
    name: str           # "daily_kline"
    table: str          # MySQL 表名
    columns: list       # 可用列

    def query(self, symbol, start, end) -> DataFrame: ...
    def to_bt_feed(self, df) -> bt.feeds.PandasData: ...
```

新增数据源步骤：
1. 实现 `DataFeedPlugin` 接口
2. 在 `data_registry.py` 中注册
3. 前端数据源选择列表自动更新

### 3.5 进度推送机制

- **子进程 → 主进程**: `multiprocessing.Queue`，子进程在 Backtrader 的 `next()` 回调中按固定间隔写入进度
- **主进程 → 前端**: 后台 asyncio task 轮询 Queue，通过 WebSocket 推送

### 3.6 策略代码安全

小团队信任模型，不做过度沙箱：
- 动态 import（非 exec/eval）
- 校验必须继承 `bt.Strategy` 且实现 `next()` 方法
- 超时控制（默认 5 分钟）
- 子进程隔离，崩溃不影响主服务
- 最大并发任务数限制

## 4. 数据库设计

共用 `stock_database`，新增 4 张表。

### 4.1 strategies — 策略定义

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| name | VARCHAR(100) | 策略名称 |
| description | TEXT | 策略描述 |
| source_type | ENUM('template','custom') | 模板 / 自定义 |
| template_id | VARCHAR(50) | 模板标识 (如 ma_crossover) |
| code | TEXT | 策略 Python 代码 |
| default_params | JSON | 默认参数 `{"fast": 5, "slow": 20}` |
| required_feeds | JSON | 所需数据源 `["daily_kline", "moneyflow"]` |
| author | VARCHAR(50) | 作者 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

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
| status | ENUM('pending','running','completed','failed') | 状态 |
| progress | SMALLINT | 进度 0-100 |
| error_message | TEXT | 失败原因 |
| metrics | JSON | 绩效指标汇总 |
| submitted_by | VARCHAR(50) | 提交人 |
| created_at | DATETIME | 提交时间 |
| finished_at | DATETIME | 完成时间 |

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

### 4.4 backtest_daily — 每日净值快照

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO | 主键 |
| run_id | INT FK | 关联回测记录 |
| trade_date | DATE | 交易日 |
| portfolio_value | DECIMAL(15,2) | 组合总价值 |
| cash | DECIMAL(15,2) | 现金余额 |
| daily_return | DECIMAL(10,6) | 当日收益率 |
| cumulative_return | DECIMAL(10,6) | 累计收益率 |
| drawdown | DECIMAL(10,6) | 当前回撤 |
| positions | JSON | 持仓快照 `{"000001.SZ": {"size": 100, "value": 1125}}` |

## 5. 前端设计

### 5.1 技术栈

- React 18 + TypeScript
- Vite (构建)
- Ant Design 5 (UI 组件库)
- ECharts 5 (图表)
- Monaco Editor (代码编辑器)
- Zustand (状态管理)
- React Router (路由)

### 5.2 页面结构

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
- **experiments/backtrader**: 已有的探索性代码，可作为策略模板的参考

## 10. 附录：视觉稿索引

brainstorm 过程中的可视化设计稿保存在 `.superpowers/brainstorm/71511-1773510849/` 目录：

| 文件 | 内容 |
|------|------|
| architecture-approaches.html | 三种架构方案对比 |
| design-architecture.html | 系统架构图与数据流 |
| design-frontend.html | 五大页面 wireframe |
| design-backend-db.html | 后端模块、数据库 schema、策略模板 |
| design-engine-detail.html | 回测引擎流程、进度推送、安全性、指标体系 |
