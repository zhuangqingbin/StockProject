# QuantViz — 量化可视化平台

股票数据可视化 + 量化策略回测平台，基于 FastAPI + React + MySQL。

## 项目边界

`quant_platform` 是仓库中的量化研究与应用项目，负责：

- 量化研究与因子分析
- 策略回测与结果展示
- 面向量化场景的前后端 API 与页面

它会使用 `data_hub` 管理的市场数据，但并不拥有 `data_hub` 的采集、调度或数据治理逻辑。

## 功能

- **市场总览** — 四大指数实时行情、迷你走势图
- **板块热力图** — 按行业分组的涨跌幅热力图，支持按涨跌幅/成交额/股票数排序
- **个股排行** — 涨幅榜、跌幅榜、成交额榜
- **K线分析** — 专业K线图 + 7种技术指标（MA/EMA/MACD/KDJ/RSI/BOLL/VOL_MA）
- **多股对比** — 2-6只股票归一化走势对比
- **策略回测** — 5种内置量化策略，完整回测报告（净值曲线、夏普比率、最大回撤、交易记录等）
- **因子研究框架** — 基于 `tushare_database` 的多表因子构建、IC 分析、分层回测、组合因子、组合回测与平台内研究工作台

## 内置策略

| 策略 | 说明 |
|------|------|
| 双均线 | 短期均线上穿长期均线买入，下穿卖出 |
| MACD | MACD 金叉买入，死叉卖出 |
| 布林带 | 价格触及下轨买入，触及上轨卖出 |
| 海龟交易法 | 突破 N 日高点买入，跌破 M 日低点卖出 |
| RSI | RSI 超卖买入，超买卖出 |

## 快速开始

### 环境要求

- Python 3.11+（使用 `apps/.venv` 共享虚拟环境）
- Node.js 18+
- MySQL

### 配置

在项目根目录 `.env.local` 中添加：

```
QV_MYSQL_DATABASE=quantviz_database
```

其余 MySQL 连接信息（`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_CHARSET`）和 `TUSHARE_TOKEN` 复用已有配置。

可选环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `QV_MYSQL_DATABASE` | `quantviz_database` | 数据库名 |
| `QV_API_PORT` | `8202` | 后端端口 |
| `QV_API_HOST` | `0.0.0.0` | 后端监听地址 |
| `QV_DEBUG` | `false` | 调试模式 |

### 初始化

```bash
# 创建数据库表 + 下载全量股票列表
bash apps/quant_platform/scripts/run.sh init

# 批量下载历史日线数据（默认最近1年）
bash apps/quant_platform/scripts/run.sh download --days 365
```

### 启动

```bash
# 后端 (端口 8202)
bash apps/quant_platform/scripts/run.sh backend

# 前端开发服务器 (端口 3001，代理 API 到 8202)
bash apps/quant_platform/scripts/run.sh frontend
```

浏览器打开 `http://localhost:3001` 即可使用。

### 每日更新

```bash
bash apps/quant_platform/scripts/run.sh update
```

支持自动重试，失败的股票会在 10 分钟后重试，最多重试 6 次。

## 技术栈

**后端：** FastAPI · SQLAlchemy (async) · aiomysql · TuShare · pandas · numpy · loguru

**前端：** React 18 · Vite · Tailwind CSS · ECharts · Axios · dayjs · lucide-react

## 目录结构

```
apps/quant_platform/
├── app/
│   ├── api/            # FastAPI 路由 (stocks, market, strategy)
│   ├── core/           # 配置 & 数据库模型
│   ├── services/       # TuShare 数据服务 + 本地缓存
│   └── strategies/     # 回测引擎 + 5种内置策略
├── research/
│   ├── factor_engine/  # 因子工程与组合因子
│   ├── analyzer/       # IC / 分层 / 相关性 / 报告
│   ├── strategy/       # 组合信号、退出规则、向量化回测
│   ├── scripts/        # 研究命令行入口
│   └── notebooks/      # Notebook 模板
├── scripts/
│   ├── run.sh          # 统一启动脚本
│   ├── init_db.py      # 初始化数据库
│   ├── batch_download.py  # 批量下载历史数据
│   └── daily_update.py    # 每日增量更新
└── frontend/
    └── src/
        ├── pages/      # 7个页面组件（含 Research 工作台）
        └── utils/      # API 封装
```

## 数据说明

- `quant_platform` 使用独立的 `quantviz_database` 保存自身应用数据，不影响 `TS_MYSQL_DATABASE` 和 `AK_MYSQL_DATABASE`
- 主应用链路在查询时仍会直接从 TuShare API 拉取数据，并缓存到 `quantviz_database`
- 研究模块会直接读取 `data_hub` 管理的数据源，例如 `tushare_database`
- 这种关系是数据消费关系，不代表 `quant_platform` 拥有 `data_hub` 的抓取、调度或数据治理职责

## 研究框架

研究模块直接读取 `tushare_database`，不建立二级缓存，默认研究目标是次日开盘收益：

```text
overnight_return = (T+1 open - T close) / T close
```

常用入口：

```bash
# 启动 research notebook
bash apps/quant_platform/scripts/run.sh research-notebook

# 单因子研究
bash apps/quant_platform/scripts/run.sh research-single --factor pct_chg

# 多因子排序与报告
bash apps/quant_platform/scripts/run.sh research-factor \
  --panel-csv /path/to/panel.csv \
  --factor pct_chg \
  --factor net_mf_rate

# 直接从 tushare_database 构建多表全量研究面板并输出分样本报告
bash apps/quant_platform/scripts/run.sh research-factor \
  --from-db \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output-dir apps/quant_platform/research/output/full_research

# 完整 overnight pipeline：因子筛选、组合因子、策略比较
apps/.venv/bin/python -m apps.quant_platform.research.scripts.run_full_pipeline \
  --start-date 2023-01-01 \
  --end-date 2025-12-31 \
  --max-factors 60

# 组合因子策略回测
bash apps/quant_platform/scripts/run.sh research-backtest \
  --panel-csv /path/to/panel.csv \
  --factor alpha_1 \
  --factor alpha_2
```

额外依赖已在 `apps/.venv` 中安装：`scikit-learn`、`scipy`、`matplotlib`、`seaborn`、`jupyterlab`。

平台集成：

- 前端研究页路径：`/research`
- 概览接口：`GET /api/research/overview`
- 研究产出静态资源：`/research-assets/*`
- `research-factor --from-db` 默认会生成 `full_factor_panel.csv`、`factor_catalog.json`、各 sample split 的 `factor_ranking.csv` 与 `split_factor_summary.csv`
- `run_full_pipeline.py` 会额外生成 `factor_ranking_full.csv`、`strategy_comparison.csv`、`best_strategy.json`
