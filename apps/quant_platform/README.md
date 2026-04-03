# QuantViz — 量化可视化平台

股票数据可视化 + 量化策略回测平台，基于 FastAPI + React + MySQL。

## 功能

- **市场总览** — 四大指数实时行情、迷你走势图
- **板块热力图** — 按行业分组的涨跌幅热力图，支持按涨跌幅/成交额/股票数排序
- **个股排行** — 涨幅榜、跌幅榜、成交额榜
- **K线分析** — 专业K线图 + 7种技术指标（MA/EMA/MACD/KDJ/RSI/BOLL/VOL_MA）
- **多股对比** — 2-6只股票归一化走势对比
- **策略回测** — 5种内置量化策略，完整回测报告（净值曲线、夏普比率、最大回撤、交易记录等）

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
├── scripts/
│   ├── run.sh          # 统一启动脚本
│   ├── init_db.py      # 初始化数据库
│   ├── batch_download.py  # 批量下载历史数据
│   └── daily_update.py    # 每日增量更新
└── frontend/
    └── src/
        ├── pages/      # 6个页面组件
        └── utils/      # API 封装
```

## 数据说明

- 数据存储在独立的 `quantviz_database` 数据库中，不影响 `tushare_database` 和 `akshare_database`
- 首次查询某只股票时会自动从 TuShare API 拉取并缓存到本地数据库
- 后续相同查询直接读取本地缓存，不再消耗 API 积分
