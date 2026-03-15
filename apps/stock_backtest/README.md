# Stock Backtest

`apps/stock_backtest` 是一个量化回测工作台，包含：

- FastAPI 后端与 Backtrader 执行骨架
- React + Vite 前端
- 总览塔台、数据实验室、策略工坊、回测发射台、结果分析、策略对比、研究入口
- 扩展后的内置 Backtrader 模板策略库
- 运行时摘要、回测事件诊断、重复请求结果复用

## 启动

后端：

```bash
./apps/stock_backtest/run.sh
```

启动脚本会自动按当前 Python 架构创建并复用独立虚拟环境：

- Apple Silicon 原生终端通常会落到 `.venv-stock-backtest-arm64`
- Rosetta / `x86_64` 终端会落到 `.venv-stock-backtest-x86_64`
- 同时会更新统一入口 symlink：`.venv-stock-backtest`
- 启动前会自动清理旧的 `uvicorn apps.stock_backtest.backend.main:app` 进程，避免端口占用和热重启残留

前端开发：

```bash
./apps/stock_backtest/run.sh frontend
```

后端默认读取 `shared/stock_core` 的 MySQL 环境变量；如果要本地测试，可设置：

```bash
export STOCK_BACKTEST_DATABASE_URL="sqlite+pysqlite:///./stock-backtest.sqlite3"
export STOCK_BACKTEST_EXECUTION_MODE="inline"
```

如果根目录已有 `.env` / `.env.local`，`MYSQL_*` 与 `STOCK_BACKTEST_*` 会自动加载，不需要每次手工 `export`。

如果要直接让后端托管前端页面，先构建：

```bash
cd apps/stock_backtest/frontend
npm install
npm run build
cd /Users/qingbin.zhuang/Personal/StockProject
./apps/stock_backtest/run.sh
```

## 验证

后端测试：

```bash
./.venv-stock-backtest/bin/python -m pytest apps/stock_backtest/tests -q
```

前端测试与构建：

```bash
cd apps/stock_backtest/frontend
npm test
npm run build
```

## 当前入口

- `/dashboard` 总览塔台：看平台状态、工作流入口、feed 覆盖和基准指数
- `/data` 数据实验室：看 feed 健康度、行业热区和股票检索
- `/strategies` 策略工坊：看策略库存、模板仓和代码编辑
- `/runs` 回测发射台：真实填写参数并提交回测，同时看运行诊断时间线
- `/analysis` 结果分析：收益、回撤、交易与滚动指标
- `/compare` 策略对比：叠加净值与参数敏感性
- `/notebook` 研究入口：启动/停止 JupyterLab 并查看分析模板
