# StockProject 文档门户

StockProject 是一个以 Python 为主的 A 股 monorepo，包含两个主应用：

- `apps/data_hub`：数据采集、入库、调度、浏览与监控
- `apps/quant_platform`：研究流程、回测、可视化以及对外应用 API

本门户是面向整个仓库的统一文档入口，服务两类用户：

- **开发者**：需要环境搭建、架构说明和运维命令
- **研究用户**：需要 `analysis`、`findings` 和 `quant_platform` 的研究入口

## 从这里开始

- 第一次接触本仓库 → [快速上手](getting-started.md)
- 负责数据采集与监控 → 进入 `Data Hub`
- 负责策略研究与回测 → 进入 `Quant Platform`
- 查环境变量、测试或常用命令 → 进入 `Ops / Dev`

## 主要章节

- `Data Hub`：生产数据流、数据浏览 UI、面向研究的 `analysis`
- `Quant Platform`：对外应用 + 因子与回测研究
- `Ops / Dev`：共享环境、测试、常用命令索引
- `Repo Governance`：仓库级边界与文档归属规则
