# 服务器端部署 Checklist

`apps/setup.sh` 已经覆盖了 venv、依赖、`.env` 模板、建库、npm install、基础数据同步、cron 安装等步骤，所以服务器端部署只需要按下面的 checklist 走一遍。

适用平台：Linux（Debian/Ubuntu/CentOS/Fedora/AliCloud），macOS 同样可用（cron 部分会换成 launchd）。

---

## 1. 系统前置依赖（一次性）

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y git python3.11 python3.11-venv nodejs npm mysql-client

# CentOS / Fedora / AliCloud
sudo dnf install -y git python3.11 nodejs npm mysql
```

- **MySQL**：直连共享 MySQL 服务器时只需要 client；要在本机起库才需要 `mysql-server`
- **Node.js**：只有要跑 `data_explorer` 前端时才需要；纯跑 pipeline 可以 `--skip-fe`
- **Python**：必须 3.11+，`apps/setup.sh` 会校验

## 2. MySQL 初始化（新装服务器才需要）

```bash
# 启动服务
sudo systemctl start mysqld          # CentOS/Fedora/AliCloud
sudo systemctl start mysql           # Debian/Ubuntu
sudo systemctl enable mysqld         # 开机自启

# 首次登录（新装的 MySQL root 还没有密码）
sudo mysql                           # 走 socket，不用密码
```

进入 mysql shell 之后设置 root 密码（用你 `.env.local` 里的 `MYSQL_PASSWORD`）：

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '<你设置的密码>';
FLUSH PRIVILEGES;
EXIT;
```

> MySQL 8 安装时如果自动生成了临时密码，可以从日志找到：
> ```bash
> sudo grep 'temporary password' /var/log/mysqld.log
> ```

之后用密码登录验证：

```bash
mysql -u root -p                     # 输入刚设的密码
```

进入后常用命令：

```sql
SHOW DATABASES;                      -- 列出所有库
USE tushare_database;                -- 切到指定库
SHOW TABLES;                         -- 当前库的表
SELECT COUNT(*) FROM stock_basic;    -- 看行数
DESC stock_basic;                    -- 看表结构
EXIT;
```

库本身不需要手动建——下面第 4 步的 `apps/setup.sh` 会按 `.env.local` 里的 `TS_MYSQL_DATABASE` / `AK_MYSQL_DATABASE` 自动创建。

## 3. 拉代码 + 配 `.env.local`（敏感信息）

```bash
git clone <your-repo-url> ~/StockProject
cd ~/StockProject
cp .env .env.local        # 用根目录的 .env 模板做起点（仓库自带）
vim .env.local
```

> **重要**：所有真实密钥（TuShare token、MySQL 密码、邮箱授权码等）都写到 `.env.local`，不要写到 `.env`。
>
> - `.env` 是**模板**，已被 git 追踪，里面只能放占位值
> - `.env.local` 在 `.gitignore` 里，不会被提交
> - 解析优先级：`.env.local` > `.env` > shell 环境变量（`apps/setup.sh` 与 Python 运行时使用同一套优先级）

`.env.local` 必填项：

| 变量 | 说明 |
|------|------|
| `TUSHARE_TOKEN` | TuShare API token |
| `MYSQL_HOST` | MySQL 主机 |
| `MYSQL_PORT` | MySQL 端口（默认 3306） |
| `MYSQL_USER` | MySQL 用户 |
| `MYSQL_PASSWORD` | MySQL 密码 |
| `TS_MYSQL_DATABASE` | TuShare 库名（如 `tushare_database`） |
| `AK_MYSQL_DATABASE` | AkShare 库名（如 `akshare_database`） |
| `MAIL_*`（可选） | 任务失败邮件通知，不需要可留空 |

## 4. 一键安装（按用途选 flag）

| 场景 | 命令 |
|------|------|
| 数据采集机（只跑 pipeline） | `bash apps/setup.sh --skip-fe` |
| 查询机（只挂 data_explorer 前后端） | `bash apps/setup.sh --skip-cron --skip-infra` |
| 复用已存在的远程库，不要建库 | `bash apps/setup.sh --skip-db --skip-infra --skip-fe` |
| 全装（含每日定时任务） | `bash apps/setup.sh` |

`apps/setup.sh` 是幂等的，可以反复运行。

## 5. 验证

```bash
# 跑一次盘后核心 profile（替换为最近交易日）
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh \
  --profiles trade_day_post_close_core \
  --as-of 2026-04-25

# 或起后端服务（监听 0.0.0.0:8201）
./apps/data_hub/data_explorer/scripts/run.sh backend

# 检查 cron 是否就位
crontab -l | grep stockproject

# 看每日任务日志
ls apps/data_hub/data_pipeline_ts/.logs/
```

## 6. 常用日常命令

```bash
# 手动跑某个 profile
bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --profiles trade_day_post_close_core

# 区间补数据
bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
  --start 20260101 \
  --end 20260424

# 卸载 cron
crontab -l | grep -v stockproject | crontab -
```

## 7. 默认定时计划（cron 安装后自动生效）

| 时间 | Profile | 用途 |
|------|---------|------|
| 09:25 | `trade_day_pre_open` | 盘前：ST 标记 / 涨跌停价 / 港通成分等 |
| 18:00 | `trade_day_post_close_core` | 盘后主链路：日行情 / 资金流 / 指数 / 龙虎榜 |
| 18:35 | `trade_day_post_close_extended` | 盘后扩展：融资融券 / 涨跌停统计 / 港通 Top10 |
| 18:40 | `reference_trade_day_post_close` | 大宗交易 |
| 21:30 | `financial_calendar_nightly` | 财务公告：利润表 / 资产负债表 / 现金流等 |
| 21:45 | `reference_calendar_nightly` | 参考数据：股东 / 质押 / 回购 / 解禁等 |

## 8. 常见坑

- `.env.local` 里的 MySQL 必须是**服务器能连到**的地址；用云 MySQL 时记得把服务器 IP 加白名单
- TuShare token 没填或权限不足时 `run_daily.sh` 会失败但**不会自动告警**，建议把日志接入监控（默认输出到 `apps/data_hub/data_pipeline_ts/.logs/<profile>.log`）
- 共享 venv 在 `apps/.venv`，**不要**用系统 Python 直接跑 pipeline，否则会找不到 `shared/stock_core`
- 服务器系统时区会影响 cron 触发时间；A 股相关 profile 默认按本地时间触发，如果服务器是 UTC，请把时区调到 `Asia/Shanghai`：
  ```bash
  sudo timedatectl set-timezone Asia/Shanghai
  ```
- pipeline 写入是大量 upsert，建议 MySQL 端 `innodb_buffer_pool_size` 至少给到内存的 50%，并且开 `innodb_flush_log_at_trx_commit=2` 以提升吞吐
