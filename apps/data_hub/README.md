# Data Hub

`data_hub` 负责 A 股数据抓取、写库、调度、数据浏览与监控。

## 组件

| 路径 | 作用 |
| --- | --- |
| `data_pipeline_ts/` | TuShare 数据任务上下文，拥有 fetchers、notebooks、jobs、execution 和 runtime |
| `data_pipeline_ak/` | AkShare 数据任务上下文，当前承载交易日历等导入能力 |
| `data_explorer/` | 只读数据目录、预览和监控 UI |
| `tests/` | app-level composition / import contract 测试 |
| `data_explorer/tests/` | explorer 后端测试 |
| `data_pipeline_ts/tests/` | TuShare pipeline 测试 |
| `data_pipeline_ak/tests/` | AkShare pipeline 测试 |

## 必要环境变量

至少需要以下变量：

- `TUSHARE_TOKEN`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `TS_MYSQL_DATABASE`
- `AK_MYSQL_DATABASE`
- `MYSQL_CHARSET`

这些变量都必须在 `.env` / `.env.local` 里显式配置，不再有代码默认值。

## 常用命令

### 新机器初始化 `data_hub`：

```bash
bash apps/data_hub/setup.sh
```

上面的脚本会委托到共享的 `apps/setup.sh`，创建 `apps/.venv` 并安装 `data_hub` 相关依赖。
共享依赖清单统一收口在 `apps/requirements.txt`。

### 同步基础表

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh --targets stock_basic,stock_company
```

### 运行日常任务

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --profiles trade_day_post_close_core --as-of 2026-03-16
```

运行全部日常任务（不含 `manual`）：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_pre_open,trade_day_post_close_core,trade_day_post_close_extended,reference_trade_day_post_close,financial_calendar_nightly,reference_calendar_nightly \
  --as-of 2026-03-16
```

### 运行回溯

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh --jobs stock_daily,stock_daily_basic --start 20260310 --end 20260316
```

回溯全部日常任务（不含 `manual`）：

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_pre_open,trade_day_post_close_core,trade_day_post_close_extended,reference_trade_day_post_close,financial_calendar_nightly,reference_calendar_nightly \
  --start 20250101 --end 20260318
```

### 执行 `manual` 任务

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --profiles manual --jobs stock_daily,stock_daily_basic --as-of 2026-03-16
```

`manual` profile 不支持 backfill；如果要跑 manual 任务，只能用 `run_daily.sh` 并显式指定 `--jobs`，例如 `hm_list`、`pledge_detail`、`cyq_chips`、`stock_daily`、`stock_daily_basic`。

### 启动数据浏览与监控服务

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

### 运行测试

```bash
python -m pytest -q \
  apps/data_hub/tests \
  apps/data_hub/data_explorer/tests \
  apps/data_hub/data_pipeline_ts/tests \
  apps/data_hub/data_pipeline_ak/tests
```

启动 notebook：

```bash
PYTHONPATH=$(pwd) apps/.venv/bin/python -m jupyter lab apps/data_hub/data_pipeline_ts/notebooks
```

## 说明

- `data_pipeline_ts/` 负责日常任务、回溯、notebook support 和基础设施同步，并且只写 `TS_MYSQL_DATABASE`。
- `data_pipeline_ak/` 负责 AkShare 侧导入能力，当前主要提供交易日历等辅助数据入口。
- 当前任务链路只负责抓取、写库和记录 `job_run_log`。
- `data_explorer/` 提供数据库浏览与监控界面，当前会从 `TS_MYSQL_DATABASE` 和 `AK_MYSQL_DATABASE` 建立只读连接。
