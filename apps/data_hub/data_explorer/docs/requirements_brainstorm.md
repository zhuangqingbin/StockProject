# data_explorer Requirements Brainstorm

> Date: 2026-03-17
> Status: Validated for planning
> Scope: Requirement alignment only, no implementation in this document

## Validation Note

本轮页面结构与交互方向已完成确认，当前版本可作为下一步产出正式需求文档或实现计划的基线。

## 1. Why This Exists

`data_hub` 已经把大部分源数据写进 `stock_database_v1`，但当前数据消费方式仍偏开发者视角：
- 看表结构要进数据库或 notebook
- 看某张表归属哪个 TuShare 分类，需要回头查 `fetchers/tushare`
- 看某个表最近有没有更新，需要再去翻 `job_run_log` 或跑 SQL

所以这个可视化平台的首要目标，不是做“分析大盘走势”的成品 BI，而是做一个面向内部使用的数据目录和数据浏览器，让人能快速回答下面这些问题：
- 现在库里到底有哪些表
- 这些表分别属于哪个 TuShare 分类
- 每张表是干什么的，按什么频率更新
- 这张表最近有没有数据，最近更新到哪一天
- 我能不能先预览几行，再决定是否继续分析
- 这张表的字段、索引、主键、建表 SQL 是什么
- 这个数据库本身有哪些结构信息可以直接查看

当前已进一步确认一个范围边界：
- 这个平台只聚焦“数据库信息”
- 不承担下游主题分析页或结果展示页职责
- `precomputed_*` 不进入首期目录范围
- 样例数据预览是必需能力，不是可选能力
- 对纳入范围的表，要支持“完整浏览”，即全字段展示 + 分页查看全表数据
- 除业务表和系统表外，还要包含数据库底层元信息展示

## 2. Recommended Product Direction

这里有三个方向，建议先定一个。

### Option A: Data Catalog + Preview

这是推荐方案。

定位是“数据库可视化目录”。核心能力是：
- 按 `fetchers/tushare` 的文件夹分类展示表
- 提供表详情页
- 提供安全的数据预览
- 提供轻量的新鲜度状态

优点：
- 和你现在“数据都已经有了”的阶段最匹配
- 价值交付快，能马上提升找表、看表、验表效率
- 不要求先定义一堆业务指标和图表口径

缺点：
- 更像内部数据工作台，不是面向老板汇报的展示大屏

### Option B: Data Catalog + Ops Console

这个方案是在 Option A 之上，把任务执行状态、失败任务、延迟表也一起做成独立页面。

优点：
- 更适合你把它当“数据平台控制台”来用
- 对排查 nightly / daily 作业很有帮助

缺点：
- 需求会明显扩张，信息密度变高
- 首期会混合两类目标：数据消费和平台运维

### Option C: Topic BI Dashboard

这个方向是直接做行业、涨停、资金流、财务等主题图表页。

不建议放在首期。

原因：
- 这要求先定义稳定的指标体系
- 会跳过“数据目录”这个地基
- 很容易做成只覆盖少数高频表，其他表仍然找不到、看不懂

### Recommendation

当前已确认：
- 首期不是纯 Explorer
- 独立“运维监控页”进入第一版

所以建议按 `Option B` 落地，但仍然控制边界，只做只读监控，不做任务操作：
- 目录页和表详情页保留“最近更新时间 / 最新数据日期 / 是否过期”
- 同时增加一个独立监控页，集中展示任务状态和数据新鲜度

这样平台会更像完整的内部数据控制台，但仍然保持在“浏览 + 判断 + 排查”的范围内。

## 3. Users And Use Cases

### Primary User

首期默认按“内部使用者”设计，优先服务下面三类人：
- 你自己这类平台维护者，需要知道表是否完整、是否更新
- 做数据分析或策略验证的人，需要先找到正确的数据表
- 做下游开发的人，需要快速确认字段、粒度和样例数据

### Core Use Cases

1. 我知道大类，但不知道表名
   例子：我想看财务类和资金流类有哪些表，逐层点开即可

2. 我知道表名，但不知道它有没有数据
   例子：点开 `stock_money_flow`，立刻看到总行数、日期范围、最近更新时间

3. 我想知道一张表怎么用
   例子：表详情页展示字段、粒度、触发频率、业务说明、关联 job

4. 我想先看一眼数据长什么样
   例子：预览最近 50 行，并按日期、股票代码做最小过滤

5. 我想快速发现“哪些表最近没更新”
   例子：按分类或状态筛出 stale 表

## 4. Scope Recommendation

### In Scope For V1

- 分类导航
  - 按 `tushare` 目录分类展示
  - 支持搜索表名、中文说明、关键字

- 表目录页
  - 展示每个分类下的表清单
  - 每张表展示简要说明、总行数、最近更新时间、最新数据日期

- 表详情页
  - 展示表用途、来源分类、关联 job、触发频率、主粒度
  - 展示字段清单和字段类型
  - 展示索引、主键、约束、建表 SQL 等结构信息
  - 展示日期范围、样本规模、更新状态

- 数据预览
  - 对所有纳入范围的表都提供
  - 只读分页浏览
  - 全字段展示，不做字段裁剪版预览
  - 支持持续翻页查看整张表，不是只看固定前几十行
  - 默认每页 50 行
  - 默认按主日期列倒序；若无日期列，则按主键或第一索引排序
  - 按安全字段过滤，优先支持日期和股票代码
  - 默认展示最近数据

- 轻量状态标签
  - 正常 / 延迟 / 无数据 / 手工维护
  - 让用户不用切走就知道表是否可用

- 独立运维监控页
  - 同时覆盖任务视角和表视角
  - 展示 job 最近执行状态
  - 展示表级新鲜度
  - 支持按状态筛选失败、延迟、无数据项

- 数据库元信息视图
  - 展示 schema 层级概览
  - 展示对象清单
  - 展示 DDL、索引、主键、约束、字段注释等底层结构信息

### Out Of Scope For V1

- 复杂图表分析页
- 自定义 SQL 编辑器
- 数据下载和导出
- 用户权限与多租户
- 移动端深度适配
- 配置中心、调度中心、任务重跑入口

## 5. Information Architecture

### Recommended Navigation

建议左侧主导航直接按“数据域”组织，而不是按技术来源组织得太细。

已确认：
- 使用“业务分类为主”的主导航
- 保留单独的 `Database Metadata` 入口
- 不采用“表 / 索引 / DDL / 约束”这种对象类型优先的主导航
- 左侧分类树显示每个分类的表数量

一级建议如下：
- Basic Data
- Stock Market Data
- Financial Data
- Money Flow Data
- Margin Data
- Board Data
- Reference Data
- Runtime
- Database Metadata

其中：
- `Runtime` 放 `job_run_log`
- `Database Metadata` 放 schema 概览、DDL、索引、主键、约束等结构信息入口

这样做的原因很直接：
- 前 7 类对应 `fetchers/tushare` 的真实目录结构
- `Runtime` 是数据库内的系统信息补充层
- `Database Metadata` 承接“底层库结构也要看”的需求
- `Downstream` 不纳入首期，避免平台定位从“数据库信息浏览”漂移到“业务结果展示”

这个选择的好处是：
- 找表路径更符合你当前的数据组织方式
- 业务表浏览和数据库结构浏览不会混在一起
- 后面即使扩展更多元信息页，也不会破坏业务导航心智
- 分类计数能让用户快速判断分类规模和导航价值

`Database Metadata` 入口默认首页已确认：
- 先展示库级概览
- 再下钻到 DDL / 索引 / 约束等明细

推荐首屏内容：
- schema 名称
- 表总数
- 分类分布
- 系统表数量
- 结构信息入口卡片

### Page Layout

建议首期只保留两个层级：

1. 目录页
   左侧分类树 + 当前分类表列表

2. 表详情页
   头部信息卡 + 结构信息优先 + 数据预览

3. 监控页
   任务状态视图 + 表状态视图

4. 数据库结构页
   schema 概览 + 对象清单 + DDL / 索引 / 约束

### Default Entry

已确认：
- 平台打开后默认进入“目录页”
- 监控页作为顶部一级入口或明显 tab 入口

这样更符合首期主目标：
- 先解决“找表、认表、看表”
- 再解决“任务是否失败、数据是否延迟”

相比默认落到监控页，这个路径对大多数日常使用更自然，也更贴合平台的基础定位。

### Directory Page Listing Strategy

已确认：
- 目录页不是“全库一张大表”
- 左侧点哪个分类，右侧就展示该分类下的全部表
- 搜索和筛选基于当前分类结果集展开
- 搜索默认只作用于当前分类

推荐具体方式：
- 左侧保留分类树
- 右侧主区域展示当前分类表列表
- 用户如果切换到 `financial_data`，右侧只看财务类表
- 用户如果切换到 `Database Metadata`，右侧显示数据库结构相关入口
- 每张表默认展示固定摘要字段，方便快速扫描

默认摘要字段已确认：
- 表名
- 中文说明
- 总行数（精确值）
- 最新数据日期
- 最近更新时间
- 状态

默认排序已确认：
- 先按状态排序
- 再按最近更新时间倒序

推荐状态优先级：
- 延迟 / 无数据 / 异常
- 正常
- 手工维护

统计口径已确认：
- `总行数` 默认显示精确值
- 不使用近似值作为默认展示口径
- 目录页和表详情页都以精确值为准

这样做的好处：
- 导航和结果区有明确映射关系
- 不会把几十张表一次性铺开导致认知噪音
- 更适合你当前“按 tushare 文件夹分类看数据库信息”的目标
- 搜索范围更可控，结果更符合当前浏览上下文

### Table Detail Default View

已确认：
- 点进单表后，默认先看“结构信息”
- 数据预览不是首屏，而是后一个 tab 或下一个分区

推荐具体方式：
- 表详情页顶部先放摘要卡片
- 中间主区域默认展示字段、索引、主键、约束、DDL
- 数据预览作为次级 tab
- `建表 SQL` 默认折叠，按需展开

这样更符合你当前“看数据库信息”的目标，避免用户一进来就先掉进数据值本身，而忽略结构定义。

### Monitoring Page Recommendation

既然你已经明确“都要”，那监控页建议不要混成一张超长表，而是拆成两个一级视图：

1. 任务视角
   看每个 job 最近一次执行结果，适合排查失败、超时、空写入

2. 表视角
   看每张表最近更新时间、最新数据日期、是否 stale，适合判断数据可用性

推荐交互：
- 同一个“监控页”内做两个 tab，避免菜单过多
- 两个视图共用状态筛选，例如 `失败`、`延迟`、`无数据`、`手工维护`
- 任务视角偏运维排查
- 表视角偏数据消费前检查
- 默认先落到表视角

这样既满足“都要”，又不会把用户带进一页里两套混杂口径的数据。

不建议首期做太多独立菜单，否则很快就会出现空页面或价值很薄的页面。

## 6. Table Detail Model

每张表详情页建议统一展示以下信息：

- 基本身份
  - 表名
  - 中文说明
  - 所属分类
  - 来源系统（TuShare / system / downstream）

- 更新信息
  - 关联 job 名
  - trigger profile
  - 最近执行时间
  - 最近成功时间
  - 最新数据日期
  - 是否延迟

- 数据概况
  - 总行数
  - 日期范围
  - 主粒度字段
  - 是否支持按日期过滤

- 结构信息
  - 字段名
  - 字段类型
  - 中文释义
  - 是否索引字段
  - 主键 / 唯一键 / 普通索引
  - 约束信息
  - 建表 SQL（默认折叠）

- 预览区
  - 默认每页 50 行
  - 默认按主日期列倒序；无日期列时回退到主键或第一索引
  - 允许按主日期列和 `ts_code` 过滤
  - 支持继续翻页浏览整张表
  - 所有字段都可见，不做“只挑部分列”的简化模式
  - 但不是默认首屏

这套模型的价值是让用户不必切回代码、registry、数据库三头找信息。

### Preview Requirement Clarification

你这里说“要，而且要全部的”，当前我按下面这个定义落文档：

- 不是只给少数核心表做预览，而是所有纳入范围的表都要能预览
- 不是只给几列样本，而是每张表都按真实字段完整展示
- 不是只给固定 20 或 50 行静态样本，而是支持翻页把整张表浏览完
- 但仍然是 Web 平台里的安全只读浏览，不等于一次性把整张大表全量加载到页面

这个定义兼顾了你的“全部都要”和页面可用性。

### Database Metadata Clarification

你这里说“都有”，当前我按下面这个定义落文档：

- 业务表要看
- 系统表要看
- 数据库底层结构信息也要看

具体包括：
- 字段定义
- 主键 / 索引 / 约束
- 建表 SQL
- schema 级概览
- 对象清单和结构统计

但边界仍然是：
- 平台只读
- 不做在线改表
- 不做任意 SQL 执行

## 7. Metadata Strategy For Product Design

虽然当前文档不进入实现，但需求上要先约定元数据来自哪里，否则页面定义不稳定。

建议按下面这套优先级理解：
- 分类来源：`fetchers/tushare/*` 文件夹
- 表清单来源：fetcher 文件 + `data_pipeline_ts/jobs/catalog.py` + 补充表
- 表用途说明：先复用已有 README 和 fetcher 业务语义，后续再逐步补中文描述
- 更新状态来源：`job_run_log`
- 数据规模和日期范围来源：数据库实时查询

这意味着首期产品上必须接受一个现实：
- 部分表的中文说明可能先不完整
- 但这不应该阻塞上线

换句话说，V1 更应该优先做到“找得到、看得见、能判断有没有更新”，而不是一开始就把所有字段注释补满。

## 8. Suggested Milestones

### Milestone 1: Data Catalog

目标：
- 先把所有分类和表列出来
- 让人能从导航找到每一张表

验收感受：
- “我终于不用翻代码找表了”

### Milestone 2: Table Detail + Preview

目标：
- 让每张表都有可读的详情页
- 让用户先看样本数据再决定下一步

验收感受：
- “我不用连数据库也能判断这张表是不是我要的”

### Milestone 3: Freshness And Ops Signals

目标：
- 增加更新时间、延迟判断、最近任务状态

验收感受：
- “我能快速发现哪些表最近没刷出来”

### Milestone 4: Topic Pages

这是未来扩展，不放进当前立项范围。

适合后续基于 `precomputed_*` 做：
- 大盘页
- 行业页
- 涨跌停页
- 资金流页

## 9. Decisions Still Needed

下面这些问题会直接影响首期页面数量和复杂度。

### Q1. First Release Is Explorer Or Console?

已确认答案：
- 首发做 Console 化的一版
- 即目录 + 详情 + 预览 + 独立监控页

### Q1.5. Monitor Needs Both Task And Table Perspectives?

已确认答案：
- 都要
- 推荐放在同一监控页内，以两个 tab 或两个清晰分区呈现

### Q1.6. Default Home Page?

已确认答案：
- 默认首页是目录页
- 监控页不是 landing page，而是次一级入口

### Q2. Do We Show Raw Tables Only, Or Also Downstream Tables?

已确认答案：
- 首期只看数据库信息
- 不把 `precomputed_market`、`precomputed_industry`、`precomputed_limit` 放进目录范围

这也意味着首期聚焦：
- 原始数据表
- 基础信息表
- 系统信息表（例如 `job_run_log`）

### Q2.5. Preview Is Optional Or Full-Coverage?

已确认答案：
- 预览不是可选项
- 所有纳入范围的表都要支持预览
- 预览必须支持全字段和分页浏览整张表

### Q2.6. Database Metadata Is Included?

已确认答案：
- 包含
- 不只看业务表数据，也看数据库底层结构信息
- 首期需要把 DDL、索引、字段结构等纳入可视化范围

### Q2.7. Main Navigation Uses Business Categories Or Object Types?

已确认答案：
- 采用业务分类为主的导航
- 单独补一个 `Database Metadata` 入口
- 不采用对象类型优先导航

### Q2.8. Table Detail Defaults To Structure Or Preview?

已确认答案：
- 默认先看结构信息
- 数据预览放后一个 tab 或次级分区

### Q2.9. Directory Page Shows Current Category Or Whole Database?

已确认答案：
- 左侧选分类
- 右侧展示该分类下的全部表
- 不采用全库混合大列表作为默认模式

### Q2.10. What Summary Fields Show In The Category Table List?

已确认答案：
- 表名
- 中文说明
- 总行数
- 最新数据日期
- 最近更新时间
- 状态

### Q2.11. Which Monitor Tab Is The Default?

已确认答案：
- 默认是表视角
- 任务视角作为并列 tab
- 默认优先检查数据可用性，再进入任务排查

### Q2.12. Should DDL SQL Be Expanded By Default?

已确认答案：
- 不默认展开
- `建表 SQL` 默认折叠
- 首屏优先展示字段、索引、主键、约束

### Q2.13. Should The Left Category Tree Show Counts?

已确认答案：
- 显示
- 每个分类节点都展示该分类下的表数量

### Q2.14. Should Directory Search Be Global Or Current-Category By Default?

已确认答案：
- 默认只搜当前分类
- 不做全局搜索默认模式

### Q2.15. What Is The Default Landing View Inside `Database Metadata`?

已确认答案：
- 默认先看库级概览
- 再进入 DDL / 索引 / 约束等结构明细

### Q2.16. How Should The Category Table List Be Sorted By Default?

已确认答案：
- 先按状态排序
- 再按最近更新时间倒序

### Q2.17. Should Row Count Be Exact Or Approximate By Default?

已确认答案：
- 默认显示精确值
- 不采用近似值作为默认口径

### Q2.18. What Is The Default Page Size For Data Preview?

已确认答案：
- 默认每页 50 行

### Q2.19. What Is The Default Sort Order In Data Preview?

已确认答案：
- 默认按主日期列倒序
- 如果没有日期列，则回退到主键或第一索引

### Q3. Is The Audience Mostly Technical Or Mixed?

如果以技术用户为主：
- 英文表名 + 简短中文说明就够

如果混合业务用户：
- 需要补更多中文解释、推荐入口和场景化命名

### Q4. Do You Want A Separate Home Page?

建议答案：
- 首期不需要复杂首页
- 默认直接进目录页，顶部只放少量 summary

## 10. Recommended Decision For Now

如果现在先不继续追问太多，我建议把首期需求暂时冻结成下面这一句：

> 做一个内部使用的数据库信息浏览与监控平台，按 `fetchers/tushare` 文件夹分类展示 `stock_database_v1` 中的原始表和系统表，并补充数据库底层结构信息展示；支持表搜索、表详情、对所有纳入范围表的全字段只读分页预览、任务状态查看、数据新鲜度查看，以及 DDL/索引/主键等结构信息查看；不纳入 `precomputed_*` 这类下游结果表，也不做主题分析页。

这版定义足够清楚，也足够克制，适合作为后续 UI 设计和实现计划的起点。
