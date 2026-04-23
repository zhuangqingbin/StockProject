# Project MkDocs Portal Design

## Background

当前仓库已经有多层级 Markdown 文档，但它们分散在不同位置：

- 根目录 `README.md` 说明仓库整体边界
- `apps/data_hub/README.md`、`apps/quant_platform/README.md` 说明两个主项目
- `apps/data_hub/data_pipeline_ts/analysis/README.md` 和 `FINDINGS.md` 承载研究入口与结果总结
- `docs/` 已被定义为 repo-level 文档目录，但其中仍有历史混合材料

这些文档本身并不缺，但缺少一个统一入口去服务两类读者：

- 开发维护者：需要看项目边界、环境、运行命令、目录和治理规则
- 研究使用者：需要看 analysis、strategy suite、findings、research 入口

因此需要补一个仓库级文档站，用统一导航把现有内容组织起来，而不是再维护一套脱离源码的平行文档体系。

## Goals

- 为整个仓库建立一个统一的 MkDocs 文档门户
- 同时服务开发维护者和研究使用者
- 让 `analysis` 成为站内重点栏目，而不是独立系统
- 优先复用现有 `README.md` / `FINDINGS.md` 作为内容源
- 只新增少量门户页、栏目页、汇总页
- 保持首版实现简单，可本地预览、后续易扩展

## Non-Goals

- 不重写整仓所有现有文档
- 不把 `analysis/outputs/**` 自动转成站点页面
- 不把 `docs/plans/**`、`docs/superpowers/**` 全量公开到主导航
- 不做 Python 脚本自动抽取文档元信息生成页面
- 不做多语言站点
- 不开发自定义 MkDocs 插件

## Options Considered

### Option A: 只聚合现有 README

做法：

- 直接把现有 Markdown 文件拼进导航
- 尽量不新增站点页

优点：

- 改动最小

缺点：

- 站点缺少统一导览层
- 文档粒度和风格不一致
- 对新读者不友好

### Option B: 单独维护完整 docs-site

做法：

- 新建独立文档树
- 用站点页完整重写仓库文档

优点：

- 信息架构最整齐

缺点：

- 重复维护成本高
- 容易和源码附近文档脱节

### Option C: 混合模式仓库门户

做法：

- 新建少量站点页负责统一入口和栏目导览
- 尽量复用现有 `README.md` / `FINDINGS.md`
- `analysis` 作为 `Data Hub` 下重点栏目

优点：

- 站点体验和维护成本平衡最好
- 不需要大规模搬迁文档
- 和仓库现有文档分布兼容

缺点：

- 首版仍会存在“站点页 + 原位文档”双层结构

## Chosen Approach

采用 `Option C: 混合模式仓库门户`。

核心判断：

- 这个仓库的文档已经足够多，问题主要不是“没有文档”，而是“没有统一入口”
- `docs/` 已经明确偏 repo-level，不适合作为整个站点的原始内容根目录
- `analysis` 对研究使用者很重要，但它不应成为站点根，而应成为 `Data Hub` 的一级重点栏目

## Site Boundary

### Configuration Root

在仓库根目录新增：

- `mkdocs.yml`

作为唯一站点配置入口。

### Docs Source Directory

新增：

- `site_docs/`

作为站点源目录，只承载：

- 首页
- 栏目页
- 导航汇总页
- 少量专题页

### Why Not Reuse `docs/` As `docs_dir`

不直接把现有 `docs/` 作为 `MkDocs docs_dir`，原因是：

- `docs/` 已被明确定位为 repo-level 文档目录
- 其中仍含历史混合材料
- 直接拿来做站点根会模糊 repo-level 与 project-local 的边界

因此，`docs/` 继续保留其当前职责，站点通过页面引用和整理其中的 repo-level 内容。

## Target Audience

站点同时面向两类读者：

- 开发维护者
- 研究使用者

首页需要明确分流到：

- `Data Hub`
- `Analysis`
- `Quant Platform`
- `Ops / Dev`

## Information Architecture

首版导航使用显式 `nav`，不做自动收录。

建议导航树：

```text
Home
Getting Started
Data Hub
  Overview
  data_pipeline_ts
  data_pipeline_ak
  data_explorer
  Analysis
    Overview
    Strategy Suite
    Findings
Quant Platform
  Overview
  Research
Ops / Dev
  Environment
  Testing
  Common Commands
Repo Governance
  Overview
  Inventory
```

## Content Source Rules

### New Site Pages

首版新增到 `site_docs/` 的页面：

- `index.md`
- `getting-started.md`
- `data-hub/index.md`
- `data-hub/data-pipeline-ts.md`
- `data-hub/data-pipeline-ak.md`
- `data-hub/data-explorer.md`
- `data-hub/analysis/index.md`
- `data-hub/analysis/strategy-suite.md`
- `data-hub/analysis/findings.md`
- `quant-platform/index.md`
- `quant-platform/research.md`
- `ops/environment.md`
- `ops/testing.md`
- `ops/common-commands.md`
- `repo-governance/index.md`
- `repo-governance/inventory.md`

这些页面负责：

- 统一入口
- 信息分层
- 提供链接和上下文
- 把同类命令、文档和说明收敛到同一层

### Existing Markdown Files To Reuse

首版尽量复用以下原位文档作为主体内容来源：

- `README.md`
- `apps/data_hub/README.md`
- `apps/data_hub/data_pipeline_ts/README.md`
- `apps/data_hub/data_explorer/README.md`
- `apps/data_hub/data_pipeline_ts/analysis/README.md`
- `apps/data_hub/data_pipeline_ts/analysis/FINDINGS.md`
- `apps/quant_platform/README.md`
- `apps/quant_platform/research/README.md`
- `docs/README.md`
- `docs/repo-governance.md`
- `docs/repo-doc-inventory.md`

### Allowed README Adjustments

首版允许对现有 Markdown 做少量结构化调整：

- 补目录定位
- 补上下游关系说明
- 统一高频命令写法
- 为站点阅读补充开场导语

但不做大规模重写，也不做批量“补 README”运动。

## What Stays Out Of Main Navigation

首版不纳入主导航：

- `docs/plans/**`
- `docs/superpowers/plans/**`
- `docs/superpowers/specs/**`
- `apps/data_hub/data_pipeline_ts/analysis/outputs/**`
- 其它时间戳结果目录

原因：

- 这些内容更偏历史记录、设计草稿或运行产物
- 直接纳入主导航会稀释主要入口
- 其中不少内容不适合作为稳定用户文档

后续如果确实需要展示，可单独新增 `Archive` 或 `Research Records`，但不属于首版范围。

## Analysis Section Design

`Analysis` 是首版重点栏目，但它属于 `Data Hub` 下的专题，不单独起站。

### Analysis Overview

以 `apps/data_hub/data_pipeline_ts/analysis/README.md` 为主体，整理为：

- 目录定位
- 当前策略目录概览
- 可直接执行的矩阵脚本
- `run_strategy_suite.py` 的统一入口角色

### Strategy Suite

新增站点页专门解释：

- 统一入口脚本
- 适用场景
- 常用命令
- 参数含义
- suite 输出目录结构
- `suite_summary.csv` / compact 表怎么看

### Findings

以 `apps/data_hub/data_pipeline_ts/analysis/FINDINGS.md` 为主体，作为研究结果入口页。

首版不自动收录时间戳结果，不把 `outputs/` 目录暴露为站内导航树。

## Recommended MkDocs Stack

首版依赖建议保持最小化：

- `mkdocs`
- `mkdocs-material`
- `pymdown-extensions`

选择理由：

- `mkdocs` 足够胜任静态项目文档站
- `mkdocs-material` 提供更好的导航、搜索和阅读体验
- `pymdown-extensions` 足以覆盖代码块、提示块、表格和少量增强语法

首版不引入复杂 include/plugin 体系，不依赖自动跨目录拼接 Markdown。

## Proposed `mkdocs.yml` Shape

```yaml
site_name: StockProject Docs
docs_dir: site_docs
site_dir: site

theme:
  name: material
  features:
    - navigation.sections
    - navigation.instant
    - search.suggest
    - search.highlight

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Data Hub:
      - Overview: data-hub/index.md
      - data_pipeline_ts: data-hub/data-pipeline-ts.md
      - data_pipeline_ak: data-hub/data-pipeline-ak.md
      - data_explorer: data-hub/data-explorer.md
      - Analysis:
          - Overview: data-hub/analysis/index.md
          - Strategy Suite: data-hub/analysis/strategy-suite.md
          - Findings: data-hub/analysis/findings.md
  - Quant Platform:
      - Overview: quant-platform/index.md
      - Research: quant-platform/research.md
  - Ops / Dev:
      - Environment: ops/environment.md
      - Testing: ops/testing.md
      - Common Commands: ops/common-commands.md
  - Repo Governance:
      - Overview: repo-governance/index.md
      - Inventory: repo-governance/inventory.md

markdown_extensions:
  - admonition
  - tables
  - toc:
      permalink: true
  - pymdownx.superfences
  - pymdownx.tabbed
  - pymdownx.tasklist
```

## Implementation Phases

### Phase 1: Site Skeleton

新增：

- `mkdocs.yml`
- `site_docs/`
- 首页和一级栏目页

### Phase 2: Core Content Integration

先接入：

- 仓库总览
- `Data Hub`
- `Analysis`
- `Quant Platform`
- `Ops / Dev`
- `Repo Governance`

### Phase 3: Documentation Cleanup

按需对少量现有 Markdown 做结构优化，使其更适合站内阅读。

### Phase 4: Local Preview Validation

本地跑：

- `mkdocs serve`

验证：

- 导航结构
- 搜索
- 代码块
- 中文标题
- 链接跳转

## Acceptance Criteria

- 首页可以清晰分流到 `Data Hub`、`Analysis`、`Quant Platform`、`Ops / Dev`
- 主要 README 和 `FINDINGS.md` 都能在站内访问
- 环境、测试和常用命令有统一入口
- `analysis` 被纳入仓库级门户，而不是单独割裂
- 历史 plans、specs、时间戳产物不进入主导航
- 本地 `mkdocs serve` 可稳定预览

## Risks And Trade-Offs

### Risk: Site Pages And Source READMEs Drift

缓解方式：

- 站点页只做导览和汇总，避免重复复制大段正文
- 细节说明尽量仍由源码附近 README 维护

### Risk: Too Much Content Enters Navigation

缓解方式：

- 首版坚持显式 `nav`
- 不做自动收录

### Risk: `docs/` Boundary Becomes Fuzzy Again

缓解方式：

- 站点源目录单独放在 `site_docs/`
- `docs/` 继续只承担 repo-level 文档职责

## Rollout Recommendation

实施时先做最小可用门户：

1. 建立 `mkdocs.yml` 和 `site_docs/`
2. 跑通 `Home`、`Getting Started`、`Data Hub`、`Analysis`、`Quant Platform`
3. 再补 `Ops / Dev` 和 `Repo Governance`
4. 最后只对确有必要的现有 Markdown 做小范围修订

这样可以先尽快把“统一入口”做出来，而不是陷入长时间文档重构。
