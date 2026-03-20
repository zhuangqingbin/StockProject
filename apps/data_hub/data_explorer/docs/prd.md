# data_explorer PRD

> Date: 2026-03-17
> Status: Ready for implementation planning
> Location: `apps/data_hub/data_explorer/docs`

## 1. Background

`data_hub` 已经把核心 A 股源数据写入 `stock_database_v1`，但当前使用方式仍然偏工程化，主要依赖数据库直接查询、notebook 和代码目录判断。缺少一个面向内部使用者的统一可视化入口，导致以下问题长期存在：

- 找表成本高，需要在数据库、README、`fetchers/tushare` 之间来回切换
- 认表成本高，不容易快速判断表用途、更新频率、结构定义
- 验表成本高，想看字段、索引、DDL、样例数据时没有统一界面
- 查状态成本高，任务执行情况和数据新鲜度需要单独排查

因此，本项目需要建设一个只读的数据库信息浏览与监控平台，用于统一展示 `stock_database_v1` 内的业务表、系统表和数据库结构信息。

## 2. Product Positioning

本产品不是主题 BI，也不是数据库管理后台。

本产品的定位是：

- 一个内部使用的数据库信息浏览平台
- 一个面向数据维护、数据验证、结构查看、状态排查的工作台
- 一个按 `fetchers/tushare` 目录心智组织的表目录与监控控制台

本产品明确不承担以下职责：

- 不做面向业务汇报的图表驾驶舱
- 不做下游 `precomputed_*` 结果展示
- 不做任意 SQL 执行
- 不做数据库写操作、改表、重跑任务等管理动作

## 3. Goals

### 3.1 Primary Goals

- 让用户快速知道 `stock_database_v1` 里有哪些表
- 让用户按 `tushare` 业务分类浏览表
- 让用户在单表层面查看结构信息、DDL、索引、主键、约束和样例数据
- 让用户快速判断一张表是否有数据、更新到了哪里、当前状态是否正常
- 让用户能从一个独立页面查看任务状态和表级新鲜度
- 让用户能查看数据库级别的元信息概览

### 3.2 Non-Goals

- 不做主题分析页
- 不做数据下载导出
- 不做移动端优先设计
- 不做权限系统、多租户系统
- 不做写入、修复、任务操作

## 4. Target Users

### 4.1 Primary Users

- 数据平台维护者
- 使用数据库做分析验证的内部用户
- 需要确认表结构和字段定义的下游开发者

### 4.2 Typical Questions

- 这个库里到底有哪些表？
- 某张表属于哪个业务分类？
- 这张表最近有没有更新？
- 这张表的字段、索引、DDL 是什么？
- 这张表的数据长什么样？
- 最近哪些任务失败了？哪些表延迟了？

## 5. Scope

### 5.1 In Scope

- 业务分类导航
- 分类内表列表
- 单表详情页
- 单表全字段只读分页预览
- 任务状态监控
- 表级新鲜度监控
- 数据库结构信息展示
- schema 级概览

### 5.2 Included Data Scope

- `basic_data`
- `stock_market_data`
- `financial_data`
- `money_flow_data`
- `margin_data`
- `board_data`
- `reference_data`
- `runtime`
- `database_metadata`

### 5.3 Excluded Data Scope

- `precomputed_market`
- `precomputed_industry`
- `precomputed_limit`

这些表属于下游结果表，不纳入首期范围。

## 6. Information Architecture

### 6.1 Main Navigation

主导航采用“业务分类为主”的方式，而不是“对象类型为主”。

一级导航如下：

- Basic Data
- Stock Market Data
- Financial Data
- Money Flow Data
- Margin Data
- Board Data
- Reference Data
- Runtime
- Database Metadata

说明：

- 前 7 个分类对应 `fetchers/tushare` 真实目录结构
- `Runtime` 用于系统表，例如 `job_run_log`
- `Database Metadata` 用于 schema 概览、DDL、索引、主键、约束等结构信息

左侧分类树必须显示每个分类的表数量。

### 6.2 Default Entry

平台默认首页进入目录页，不默认进入监控页。

### 6.3 Directory Search Scope

目录页搜索默认只作用于当前分类，不做全局搜索默认模式。

## 7. Page Requirements

## 7.1 Directory Page

### Purpose

让用户通过分类快速浏览当前库中的表。

### Layout

- 左侧：分类树
- 右侧：当前分类下的表列表

### Behavior

- 点击左侧分类后，右侧只显示该分类下全部表
- 不采用“全库混合大列表”作为默认模式
- 搜索和筛选基于当前分类结果集展开

### Table List Columns

右侧列表默认展示以下字段：

- 表名
- 中文说明
- 总行数（精确值）
- 最新数据日期
- 最近更新时间
- 状态

### Default Sorting

右侧列表默认排序规则：

1. 先按状态排序
2. 再按最近更新时间倒序

建议状态优先级：

1. 延迟 / 无数据 / 异常
2. 正常
3. 手工维护

## 7.2 Table Detail Page

### Purpose

让用户在单表层面理解一张表的结构、状态和数据。

### Default First Screen

单表详情默认先展示结构信息，不先展示数据预览。

推荐布局：

- 顶部：摘要卡片
- 中间：结构信息区
- 下方或次级 tab：数据预览区

### Summary Area

顶部摘要卡片建议包括：

- 表名
- 中文说明
- 所属分类
- 来源系统
- 关联 job
- trigger profile
- 总行数
- 最新数据日期
- 最近更新时间
- 状态

### Structure Area

结构信息首屏必须支持：

- 字段名
- 字段类型
- 默认值
- 可空信息
- 中文释义 / 注释
- 主键
- 唯一键
- 普通索引
- 约束信息

### DDL

`建表 SQL` 必须可查看，但默认折叠，不作为首屏展开内容。

## 7.3 Data Preview

### Scope

对所有纳入范围的表都必须提供数据预览。

### Preview Rules

- 只读
- 全字段展示
- 可持续翻页浏览整张表
- 不做“只看少量列”的简化模式

### Default Pagination

- 默认每页 50 行

### Default Sorting

- 默认按主日期列倒序
- 如果没有日期列，则回退到主键或第一索引排序

### Filters

优先支持：

- 主日期列筛选
- `ts_code` 筛选

## 7.4 Monitor Page

### Purpose

让用户快速查看任务状态和数据可用性。

### Structure

监控页包含两个并列 tab：

- 表视角
- 任务视角

### Default Tab

默认先落到表视角，任务视角作为并列 tab。

### Table Perspective

用于查看：

- 每张表最近更新时间
- 最新数据日期
- 是否延迟
- 是否无数据
- 当前状态

### Task Perspective

用于查看：

- 每个 job 最近一次执行状态
- 执行时间
- 失败情况
- 错误信息

## 7.5 Database Metadata Page

### Purpose

统一展示数据库层面的结构信息。

### Default Landing View

`Database Metadata` 默认先展示库级概览，再下钻明细。

### Default Overview Content

- schema 名称
- 表总数
- 分类分布
- 系统表数量
- 结构信息入口卡片

### Drill-down Content

需要支持查看：

- table DDL
- indexes
- primary keys
- constraints
- column metadata

## 8. Functional Requirements

### FR-1 Category Navigation

系统必须按 `tushare` 分类展示数据库表，并显示每类表数量。

### FR-2 Category Table Listing

系统必须在目录页右侧展示当前分类下的全部表，并支持当前分类内搜索。

### FR-3 Table Summary

系统必须在列表页和详情页展示精确总行数、最新数据日期、最近更新时间和状态。

### FR-4 Table Structure

系统必须支持查看字段、索引、主键、约束和建表 SQL。

### FR-5 Table Preview

系统必须对所有纳入范围的表提供全字段只读分页预览。

### FR-6 Monitoring

系统必须提供独立监控页，并同时支持表视角和任务视角。

### FR-7 Database Metadata

系统必须提供数据库结构信息页面，用于展示 schema 概览和结构明细。

## 9. Non-Functional Requirements

- 平台只读
- 不执行写操作
- 不提供任意 SQL 执行入口
- 文档和页面语言以中文为主，保留数据库对象原始英文标识
- 页面默认排序和默认入口应稳定，不依赖用户手动配置
- 首期以桌面端使用体验为主

## 10. Acceptance Criteria

满足以下条件可视为首期需求完成：

1. 用户可以从目录页按业务分类浏览所有纳入范围的表。
2. 左侧分类树显示每类表数量。
3. 右侧当前分类表列表能展示约定的摘要字段，并按约定规则排序。
4. 用户点进任意纳入范围表后，可以先看到结构信息，再切到数据预览。
5. 用户可以查看任意纳入范围表的字段、索引、主键、约束和建表 SQL。
6. 用户可以对任意纳入范围表进行全字段、只读、分页预览。
7. 监控页同时存在表视角和任务视角，默认先落到表视角。
8. `Database Metadata` 页面默认展示库级概览，并可下钻到结构明细。
9. 下游 `precomputed_*` 表不进入首期范围。

## 11. Artifacts In This Directory

- `requirements_brainstorm.md`: 已确认的 brainstorming 记录
- `table_inventory.md`: 按分类整理的表清单
- `prd.md`: 当前正式 PRD

## 12. Next Step

当前 PRD 已足够支撑下一步产出：

- 页面说明文档
- 实现计划
- 低保真页面结构稿

如果继续推进，下一份建议文档是“页面说明文档”，把每个页面拆成更细的模块和交互规则。
