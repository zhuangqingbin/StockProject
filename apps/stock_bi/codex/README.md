# Stock BI

基于 FastAPI + ECharts 的 A 股市场数据可视化平台，支持自然语言查询。

## 目录结构

```text
apps/stock_bi/codex/
├── backend/
├── frontend/
├── requirements.txt
├── run.py
├── run.sh
└── README.md
```

## 快速开始

安装依赖：

```bash
cd apps/stock_bi/codex
pip install -r requirements.txt
```

配置数据库和数据源：

- 复用仓库根目录 `shared/stock_core/config.py` 的环境变量配置
- 至少需要可访问的 MySQL `daily_kline` 表

启动服务：

```bash
cd apps/stock_bi/codex
python3 run.py
```

或：

```bash
cd apps/stock_bi/codex
chmod +x run.sh
./run.sh
```

访问地址：

- 前端：`http://localhost:8000/`
- API 文档：`http://localhost:8000/api/docs`

## 技术栈

- 后端：FastAPI, SQLAlchemy, MySQL
- 前端：HTML, CSS, JavaScript, ECharts
- 数据源：仓库内股票数据平台生成的数据库表

## 开发说明

- 后端主入口：`apps/stock_bi/codex/backend/main.py`
- 前端入口：`apps/stock_bi/codex/frontend/index.html`
- 详细需求和表结构说明见 `apps/stock_bi/codex/requirements.md`
