# Stock Data Platform V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按 `apps/stock_data_platform_v1/docs/requirements.md` 与 `apps/stock_data_platform_v1/docs/design.md` 实现全新的 `stock_data_platform_v1`，保留 39 个 job + 3 个基础设施 fetcher，并提供 schema-driven 写入、profile 内并发执行、回填与 post-hook。

**Architecture:** 采用清晰模块化单体结构：`common` 负责环境、客户端与基础工具；`fetchers` 负责按数据源封装拉取逻辑并声明 `TableSchema`；`pipeline` 负责 context、job config、validator、writer、runner 与 CLI；`hooks` 负责下游通知；`jobs` 只保留 YAML 配置。数据库写入采用单表 scope-based DELETE + INSERT，首写自动建表和建索引。

**Tech Stack:** Python 3.11+, pandas, SQLAlchemy, PyYAML, requests, tushare, akshare, pytest

### Task 1: 建立 v1 包骨架与基础测试入口

**Files:**
- Create: `apps/stock_data_platform_v1/__init__.py`
- Create: `apps/stock_data_platform_v1/common/__init__.py`
- Create: `apps/stock_data_platform_v1/fetchers/__init__.py`
- Create: `apps/stock_data_platform_v1/fetchers/tushare/__init__.py`
- Create: `apps/stock_data_platform_v1/fetchers/akshare/__init__.py`
- Create: `apps/stock_data_platform_v1/pipeline/__init__.py`
- Create: `apps/stock_data_platform_v1/hooks/__init__.py`
- Create: `apps/stock_data_platform_v1/tests/__init__.py`
- Create: `apps/stock_data_platform_v1/tests/conftest.py`

**Step 1: 写失败测试**

- 为包导入、SQLite engine fixture 和核心模块路径写最小测试。

**Step 2: 跑失败测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_bootstrap.py`

Expected: 因模块缺失而失败。

**Step 3: 写最小实现**

- 建立包目录与 `conftest.py`。

**Step 4: 跑测试确认通过**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_bootstrap.py`

### Task 2: 实现基础层 `common` 与 fetcher 抽象

**Files:**
- Create: `apps/stock_data_platform_v1/common/database.py`
- Create: `apps/stock_data_platform_v1/common/clients.py`
- Create: `apps/stock_data_platform_v1/common/market_calendar.py`
- Create: `apps/stock_data_platform_v1/common/stock_universe.py`
- Create: `apps/stock_data_platform_v1/fetchers/base.py`
- Create: `apps/stock_data_platform_v1/tests/test_common.py`
- Create: `apps/stock_data_platform_v1/tests/test_base.py`

**Step 1: 写失败测试**

- 覆盖 `MYSQL_DATABASE` URL 构造、TuShareClient 重试/缓存入口、ExecutionContext 依赖的 calendar 行为、`ColumnDef/TableSchema/BaseFetcher` 的最小契约。

**Step 2: 跑失败测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_common.py apps/stock_data_platform_v1/tests/test_base.py`

**Step 3: 写最小实现**

- 从 v0 迁移 `client.py`、`market_calendar.py`、`stock_universe.py`，并把 fetcher 基类改为 `table_schema` 驱动。

**Step 4: 跑测试确认通过**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_common.py apps/stock_data_platform_v1/tests/test_base.py`

### Task 3: 迁移 39 个 fetcher 并建立 registry

**Files:**
- Create: `apps/stock_data_platform_v1/fetchers/tushare/daily.py`
- Create: `apps/stock_data_platform_v1/fetchers/tushare/financial.py`
- Create: `apps/stock_data_platform_v1/fetchers/tushare/reference.py`
- Create: `apps/stock_data_platform_v1/fetchers/tushare/special.py`
- Create: `apps/stock_data_platform_v1/fetchers/tushare/infrastructure.py`
- Create: `apps/stock_data_platform_v1/fetchers/akshare/calendar.py`
- Modify: `apps/stock_data_platform_v1/fetchers/__init__.py`
- Create: `apps/stock_data_platform_v1/tests/test_fetchers.py`

**Step 1: 写失败测试**

- 校验 registry 覆盖 39 个 job fetcher。
- 校验代表性 fetcher 的字段顺序、空结果、fan-out 行为、基础设施 fetcher 不进入 job registry。

**Step 2: 跑失败测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py`

**Step 3: 写最小实现**

- 以 v0 为蓝本迁移 fetcher。
- 为每个 fetcher 增加 `table_schema`，索引优先覆盖 `trade_date`、`ann_date`、`end_date`、`ts_code` 等查询维度。

**Step 4: 跑测试确认通过**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_fetchers.py`

### Task 4: 实现 pipeline 核心

**Files:**
- Create: `apps/stock_data_platform_v1/pipeline/context.py`
- Create: `apps/stock_data_platform_v1/pipeline/job_config.py`
- Create: `apps/stock_data_platform_v1/pipeline/validator.py`
- Create: `apps/stock_data_platform_v1/pipeline/writer.py`
- Create: `apps/stock_data_platform_v1/pipeline/runner.py`
- Create: `apps/stock_data_platform_v1/tests/test_context.py`
- Create: `apps/stock_data_platform_v1/tests/test_job_config.py`
- Create: `apps/stock_data_platform_v1/tests/test_validator.py`
- Create: `apps/stock_data_platform_v1/tests/test_writer.py`
- Create: `apps/stock_data_platform_v1/tests/test_runner.py`

**Step 1: 写失败测试**

- 覆盖 context 渲染、YAML 装载与 profile/job 过滤、schema 校验、auto-DDL、scope delete + insert、同 profile 并发执行与失败隔离、`job_run_log` 写入。

**Step 2: 跑失败测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_context.py apps/stock_data_platform_v1/tests/test_job_config.py apps/stock_data_platform_v1/tests/test_validator.py apps/stock_data_platform_v1/tests/test_writer.py apps/stock_data_platform_v1/tests/test_runner.py`

**Step 3: 写最小实现**

- 从 v0 `runtime.py` 拆分出 context / config / writer / runner。
- writer 增加自动建表与 composite index。
- runner 使用 `ThreadPoolExecutor` 在单个 trigger profile 内并发执行。

**Step 4: 跑测试确认通过**

Run: 同上。

### Task 5: 实现 hooks、CLI、脚本与 YAML 配置

**Files:**
- Create: `apps/stock_data_platform_v1/hooks/post_sync.py`
- Create: `apps/stock_data_platform_v1/pipeline/cli.py`
- Create: `apps/stock_data_platform_v1/jobs/daily_jobs.yaml`
- Create: `apps/stock_data_platform_v1/jobs/financial_jobs.yaml`
- Create: `apps/stock_data_platform_v1/jobs/reference_jobs.yaml`
- Create: `apps/stock_data_platform_v1/jobs/special_jobs.yaml`
- Create: `apps/stock_data_platform_v1/scripts/run_daily.sh`
- Create: `apps/stock_data_platform_v1/scripts/run_backfill.sh`
- Create: `apps/stock_data_platform_v1/scripts/install_launchd.sh`
- Create: `apps/stock_data_platform_v1/tests/test_cli.py`
- Create: `apps/stock_data_platform_v1/tests/test_hooks.py`

**Step 1: 写失败测试**

- 覆盖 CLI 参数解析、回填参数校验、hook 请求 payload/错误处理、YAML 中 39 个 jobs 的 `source` / `params` / `scope_columns` 一致性。

**Step 2: 跑失败测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_cli.py apps/stock_data_platform_v1/tests/test_hooks.py`

**Step 3: 写最小实现**

- 从 v0 job YAML 复制 `params` 和 `scope_columns`，删掉 mirror/sync 旧字段，补上 `source`。
- CLI 支持 `--trigger-profiles`、`--as-of`、`--jobs`、`--backfill --start --end`。

**Step 4: 跑测试确认通过**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests/test_cli.py apps/stock_data_platform_v1/tests/test_hooks.py`

### Task 6: 全量验证

**Files:**
- Modify: 仅在验证暴露缺陷时调整

**Step 1: 跑聚合测试**

Run: `python -m pytest -q apps/stock_data_platform_v1/tests`

**Step 2: 跑静态/执行验证**

Run: `python -m apps.stock_data_platform_v1.pipeline.cli --help`

**Step 3: 记录验证结果**

- 把通过/失败与剩余风险写入 `progress.md`。
