# `scripts/`

`scripts/` 是 `data_pipeline_ts` 的 Shell 入口层，负责解析 Python 路径并把参数转发给 `main.py`。

## 文件说明

| 脚本 | 作用 |
|------|------|
| `run_daily.sh` | 主入口脚本，解析 Python 后调用 `main.py`，默认模式为 `once` |
| `run_backfill.sh` | 便捷包装，等价于 `run_daily.sh --mode backfill "$@"` |
| `run_job.sh` | 单 job 显式参数入口，等价于 `python -m apps.data_hub.data_pipeline_ts.run_job "$@"` |
| `run_recommended_backfill.sh` | README 推荐回溯编排入口，串起系统表同步、常规 backfill、显式范围 job，以及可选第 4 步 manual job |
| `sync_infrastructure.sh` | 便捷包装，等价于 `run_daily.sh --mode infrastructure "$@"` |
| `install_launchd.sh` | macOS launchd 定时任务安装器 |

## `run_daily.sh`

主入口，所有其他脚本最终都通过它调用 `main.py`。

**Python 路径解析顺序**：

1. `apps/.venv/bin/python`（apps 共享 venv）
2. `shared/scripts/resolve_project_python.sh`（系统回退）

**使用方式**：

```bash
# 默认 once 模式，跑今天的盘后主链路
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core

# 指定日期
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-03-17

# 跑单个任务
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --jobs stock_daily --as-of 2026-03-17
```

## `run_backfill.sh`

回填模式的便捷入口，内部直接调用 `run_daily.sh --mode backfill`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --profiles trade_day_post_close_core \
  --start 20260101 --end 20260317
```

## `run_job.sh`

单 job 显式参数入口，适合：

- `manual` profile 下的快照或全市场 fan-out 任务
- `kpl_list` / `report_rc` 这类不适合混入统一 profile 回放的范围补数
- 需要直接传 `start_date` / `end_date` / `snapshot_date` 的一次性任务

参数通过重复的 `--param key=value` 传入；数组/对象/布尔值支持 JSON 解析，其余值按字符串传递。

```bash
# 触发一次 hm_list 快照
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job hm_list \
  --param snapshot_date=20260318

# 单独回补 report_rc 的一个时间窗口
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job report_rc \
  --param start_date=20260101 \
  --param end_date=20260317
```

## `run_recommended_backfill.sh`

把 `jobs/README.md` 里的推荐回溯顺序直接编排成一个入口脚本。

默认行为：

- 第 1 步：并行同步 `stock_basic,stock_company` 和 `trade_cal`
- 第 2 步：批量回溯所有常规非 `manual` job，并自动排除 `kpl_list` / `report_rc`
- 第 3 步：并行执行 `kpl_list` / `report_rc`

可选行为：

- `--include-step4`：在默认 1-3 步之后，再并行执行 `hm_list`、`pledge_detail`、`cyq_chips`、`fina_audit`
- `--only-step4`：只执行第 4 步
- `--snapshot-date YYYYMMDD`：覆盖 `hm_list` / `pledge_detail` 的快照日期；不传时默认使用 `--end`
- `--max-workers N`：透传给第 2 步的 `run_backfill.sh`
- `--dry-run`：仅打印真实命令，不执行

```bash
# 默认跑推荐回溯步骤 1-3
bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
  --start 20260101 \
  --end 20260317

# 在默认步骤后追加第 4 步
bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
  --start 20260101 \
  --end 20260317 \
  --include-step4

# 只执行第 4 步，并显式指定 snapshot_date
bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
  --start 20260101 \
  --end 20260317 \
  --only-step4 \
  --snapshot-date 20260317

# 先预览命令
bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
  --start 20260101 \
  --end 20260317 \
  --include-step4 \
  --dry-run
```

说明：

- 这个脚本负责编排，不改变现有 `run_backfill.sh` / `run_job.sh` / `sync_infrastructure.sh` 的职责边界
- 每次真实执行都会在 `apps/data_hub/data_pipeline_ts/scripts/logs/` 生成一个分钟级时间戳日志，例如 `202604181001.log`
- Step 1 / Step 2 / Step 4 只记录失败命令和对应报错，不记录成功输出
- Step 3 除了记录失败命令和报错，还会把 `kpl_list` / `report_rc` 的按日期聚合行数写进日志
- 显式范围 job 的“是否截断”仍建议结合这个日志、stdout 里的 `rows_fetched/rows_written` 与目标表日期覆盖一起判断

## 推荐回溯流程

如果你想理解 `run_recommended_backfill.sh` 背后的执行顺序，或者想拆开单独执行各步，可以按下面这套流程来。

这套任务定义当前有两种基础执行方式：

- 批量 profile/date-range 回放：`scripts/run_backfill.sh`
- 单 job 显式参数执行：`scripts/run_job.sh`

这里最容易踩坑的点是：

- `run_backfill.sh` 会严格遵守 `ProfileSpec.backfill_mode`
- `manual` profile 的 backfill_mode 是 `manual`，所以回溯时会被自动跳过
- `trade_day_post_close_extended` 里虽然包含 `kpl_list` 和 `report_rc`，但这两个 job 更适合单独用显式参数跑范围，不建议跟 bulk backfill 混在一起

### 1. 先同步系统表

建议先刷新基础表，再启动历史回溯：

**执行语言**：先同步系统表

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company

bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets trade_cal \
  --start XX \
  --end YY
```

其中 `trade_cal` 的时间范围至少要覆盖本次回溯窗口，因为 `ExecutionContext` 会依赖它推导 `trade_date`。

### 2. 批量回溯所有非 manual job，但排除 `kpl_list` / `report_rc`

由于 CLI 只有 include 没有 exclude，最稳妥的做法是先动态生成 job 名单，再交给 `run_backfill.sh`：

**执行语言**：从 xx 到xx 回溯所有除manual的profile（除了job report_rc和kpl_list）
```bash
BACKFILL_JOBS="$(
python - <<'PY'
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS

excluded = {
    "hm_list",
    "pledge_detail",
    "cyq_chips",
    "fina_audit",
    "stock_daily",
    "stock_daily_basic",
    "kpl_list",
    "report_rc",
}

print(",".join(job.name for job in ALL_JOBS if job.name not in excluded))
PY
)"

bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh \
  --jobs "${BACKFILL_JOBS}" \
  --start XX \
  --end YY
```

这条命令会覆盖：

- 所有非 `manual` profile 的常规任务
- 但不会误把 `kpl_list` / `report_rc` 混进统一回放
- 也不会触发 `manual` 下那 6 个手工/兼容任务

### 3. `kpl_list` / `report_rc` 单独触发

这两个 job 都建议走 `run_job.sh`，直接把显式范围参数传给 fetcher：

```bash
# 执行语言：触发一次kpl_list job，start_date为 xx  end_date为xx, 并确定没有被截断
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job kpl_list \
  --param start_date=XX \
  --param end_date=YY
  
# 执行语言：触发一次report_rc job，start_date为 xx  end_date为xx, 并确定没有被截断
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job report_rc \
  --param start_date=XX \
  --param end_date=YY
```

补充约束：

- `kpl_list` fetcher 内部会按 `tag` 做 5 次 fan-out 合并，所以适合单独跑窗口范围
- `kpl_list` 单次窗口建议不要超过约 3 个月；更长区间请拆多段执行
- `report_rc` 当前代码侧 client 会把每分钟调用数限制到 2 次；同时上游接口本身也有更严格的日配额，长区间需要分批规划

### 4. 可选的 manual 回溯任务

`manual` 里真正建议纳入历史回溯操作的只有 4 个：

```bash
# 快照型，只需要触发一次形成 snapshot_date 切片
# 执行语言：触发一次hm_list job （只要调用一次形成快照）
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job hm_list \
  --param snapshot_date=XX

# 执行语言：触发一次pledge_detail job （循环ts_code，形成快照）
bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job pledge_detail \
  --param snapshot_date=XX

# 全市场 ts_code fan-out 型，按日期范围重刷
# 执行语言：触发一次cyq_chips job，start_date为xx end_date为xx, 并确定没有被截断（循环ts_code，按照trade_date覆盖）

bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job cyq_chips \
  --param start_date=XX \
  --param end_date=YY

# 执行语言：触发一次fina_audit job，start_date为xx end_date为xx, 并确定没有被截断（循环ts_code，按照ann_date覆盖）

bash apps/data_hub/data_pipeline_ts/scripts/run_job.sh \
  --job fina_audit \
  --param start_date=XX \
  --param end_date=YY
```

说明：

- `hm_list` 是纯快照，只要单次触发并写入 `snapshot_date`
- `pledge_detail` 会在 fetcher 内部自动循环全市场 `ts_code`，同样只需要单次快照触发
- `cyq_chips` 会在 fetcher 内部循环全市场 `ts_code`，写库时按 `trade_date` 覆盖
- `fina_audit` 现在支持显式 `start_date/end_date` 范围执行，fetcher 内部循环全市场 `ts_code`，写库时按 `ann_date` 覆盖

`stock_daily` 和 `stock_daily_basic` 仍然保留在 `manual`，主要是兼容历史表结构；新的历史回溯不要再单独跑这两个表，统一以 `stk_factor_pro` 为准。

### 5. 怎么确认没有跑偏或被截断

统一检查项：

- 先看 `job_run_log` 最近记录是否都是 `status=success`
- 再看目标表在 `XX ~ YY` 范围内的日期覆盖是否连续
- 对于显式范围任务，优先看 `run_job.sh` 输出的 `rows_fetched/rows_written`

额外经验规则：

- `kpl_list`：如果某个大窗口跑完后你怀疑结果异常，优先把窗口缩到更小区间重跑，而不是继续扩大 profile 级回放
- `report_rc`：如果单次范围返回量已经非常接近上游已知上限，就拆更小窗口重跑
- `cyq_chips` / `fina_audit`：这两个不是单次聚合接口，而是 fetcher 内部逐 `ts_code` fan-out，重点检查失败日志和日期覆盖，不需要按 profile backfill 去硬塞

换句话说，历史回溯的推荐顺序是：

1. 同步系统表
2. 用 `run_backfill.sh` 批量回放所有常规非 manual job，但排除 `kpl_list` / `report_rc`
3. 用 `run_job.sh` 单独处理 `kpl_list` / `report_rc`
4. 再按需要触发 `hm_list`、`pledge_detail`、`cyq_chips`、`fina_audit`

## `sync_infrastructure.sh`

基础设施同步的便捷入口，内部直接调用 `run_daily.sh --mode infrastructure`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh \
  --targets stock_basic,stock_company,trade_cal \
  --start 20260101 --end 20261231
```

## `install_launchd.sh`

macOS launchd 定时任务安装器，自动为所有有 cron 的 profile 生成 plist 并注册。

**工作原理**：

1. 通过 Python 读取 `jobs/profiles.py` 中的 `PROFILE_SPECS`
2. 筛选出有 `cron` 的 profile，解析为 `Hour/Minute`
3. 为每个 profile 生成 `~/Library/LaunchAgents/com.stockproject.stock-data-v1-orchestrator-v2.{profile}.plist`
4. 用 `launchctl bootstrap` 注册到当前用户

**可选参数**：

- `--max-workers N`
  - 给每个定时 profile 追加 `--max-workers N`
  - 不传时保持旧行为，仍使用运行时代码默认并发

**产出**：

| Profile | Plist Label | 触发时间 |
|---------|-------------|----------|
| `trade_day_pre_open` | `...trade-day-pre-open` | 每天 09:25 |
| `trade_day_post_close_core` | `...trade-day-post-close-core` | 每天 18:00 |
| `trade_day_post_close_extended` | `...trade-day-post-close-extended` | 每天 18:35 |
| `reference_trade_day_post_close` | `...reference-trade-day-post-close` | 每天 18:40 |
| `financial_calendar_nightly` | `...financial-calendar-nightly` | 每天 21:30 |
| `reference_calendar_nightly` | `...reference-calendar-nightly` | 每天 21:45 |

日志输出到 `apps/data_hub/data_pipeline_ts/scripts/logs/`。

```bash
bash apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh

# 让所有定时 profile 都以单 worker 运行
bash apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh --max-workers 1
```
