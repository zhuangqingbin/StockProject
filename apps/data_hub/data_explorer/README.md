# data_explorer

`data_explorer` 是 `stock_database_v1` 的只读数据库信息平台（FastAPI + React），用于浏览和监控 TuShare 数据管线产出的 A 股数据。

## 功能

- **表目录浏览** — 按 TuShare 业务分类（基础、行情、财务、资金流、融资融券、榜单、参考、特色、运行时）导航 50+ 张表
- **表结构查看** — 字段定义、索引、约束、DDL
- **数据预览** — 只读分页预览（50 行/页），支持 ts_code / 日期范围过滤，最大 10,000 行
- **任务监控** — 四维视角：总览（新鲜度统计）、数据集、任务、运行批次
- **Database Metadata** — 数据库级别总览和表级下钻

## 架构

```
data_explorer/
├── backend/
│   ├── main.py                  # FastAPI 入口，挂载路由和静态文件
│   ├── api/                     # 路由层
│   │   ├── catalog.py           #   /api/catalog/*
│   │   ├── preview.py           #   /api/preview/*
│   │   ├── monitor.py           #   /api/monitor/*
│   │   └── database_metadata.py #   /api/database/*
│   ├── services/                # 业务逻辑层
│   │   ├── catalog_service.py   #   表注册、分类、统计
│   │   ├── preview_service.py   #   安全 SQL 构建与过滤
│   │   ├── monitor_service.py   #   运行日志聚合与新鲜度推导
│   │   ├── table_detail_service.py
│   │   └── database_metadata_service.py
│   └── infrastructure/          # 数据访问层
│       ├── db.py                #   MySQL 连接池
│       ├── mysql_introspection.py # DDL/索引/约束检查
│       └── catalog_loader.py    #   YAML 解析
├── config/
│   └── table_catalog.yaml       # 表元数据：分类、中文描述
├── frontend/                    # React 19 + Vite + TypeScript
│   └── src/
│       ├── pages/               # DirectoryPage / TableDetailPage / MonitorPage / DatabaseMetadataPage
│       ├── components/          # CategoryTree / TablePreview / TableStructure / MonitorTabs 等
│       ├── hooks/               # TanStack Query hooks（useCatalog / usePreview / useMonitor）
│       ├── stores/              # Zustand（navigationStore，URL 同步）
│       └── api.ts               # Axios API 客户端
├── scripts/
│   └── run.sh                   # 启动脚本
├── tests/                       # Pytest 测试
└── docs/                        # PRD、页面规格、需求脑暴
```

### 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI, SQLAlchemy (只做 introspection), MySQL |
| 前端 | React 19, Ant Design 5, TanStack Query, Zustand, Vite |
| 测试 | Pytest (后端), Vitest (前端) |

### API 端点

```
GET /api/catalog/categories                    # 分类列表
GET /api/catalog/categories/{key}/tables       # 分类下的表
GET /api/catalog/tables/{name}                 # 表详情（摘要 + 结构 + 最近运行）

GET /api/preview/{table_name}                  # 分页数据预览
    ?page=1&page_size=50&filters=...

GET /api/monitor/overview                      # 聚合新鲜度统计
GET /api/monitor/tables                        # 表视角监控
GET /api/monitor/jobs                          # 任务视角监控
GET /api/monitor/runs                          # 运行批次聚合

GET /api/database/overview                     # 数据库总览
GET /api/database/tables/{name}/metadata       # 表 DDL / 列 / 索引

GET /health                                    # 健康检查
```

### 数据来源

- **表注册表** — 动态发现自 `data_pipeline_ts/fetchers/` + `config/table_catalog.yaml` 合并
- **表统计** — 实时 MySQL 查询（行数、最新日期等）
- **任务元数据** — 来自 `data_pipeline_ts/jobs/catalog.py`
- **运行日志** — 来自 `job_run_log` 表

### 表状态推导

| 状态 | 规则 |
|------|------|
| `no_data` | 行数为 0 |
| `delayed` | 最新数据日期 > 3 天前 |
| `error` | 有任务绑定但无成功运行 |
| `normal` | 有任务绑定且有近期成功运行 |
| `manual` | 无任务绑定 |

## 启动

```bash
# 后端（端口 8201）
./apps/data_hub/data_explorer/scripts/run.sh backend

# 前端开发服务（端口 5178，代理 /api 到后端）
./apps/data_hub/data_explorer/scripts/run.sh frontend

# 同时启动（后端后台 + 前端前台）
./apps/data_hub/data_explorer/scripts/run.sh dev
```

## 测试

```bash
pytest apps/data_hub/data_explorer/tests -q
npm --prefix apps/data_hub/data_explorer/frontend test
npm --prefix apps/data_hub/data_explorer/frontend run build
```
