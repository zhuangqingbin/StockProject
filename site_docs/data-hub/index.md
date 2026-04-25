# Data Hub

`data_hub` 是仓库内负责数据生产和可观测性的应用。

承担的职责：

- A 股数据采集与入库
- 每日调度与历史回填
- 只读浏览与监控
- 面向研究、直接读库的分析脚本

## 组件

- `data_pipeline_ts`：基于 TuShare 的生产 pipeline
- `data_pipeline_ak`：AkShare 辅助上下文，用于交易日历和兜底导入
- `data_explorer`：只读的 FastAPI + React 浏览与监控 UI
- `analysis`：基于数据库的研究脚本和策略矩阵

## 常用入口

- `bash apps/data_hub/setup.sh`
- `bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help`
- `./apps/data_hub/data_explorer/scripts/run.sh backend`
- `./apps/data_hub/data_explorer/scripts/run.sh frontend`
