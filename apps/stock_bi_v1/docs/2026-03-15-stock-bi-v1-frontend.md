# Stock BI V1 Frontend Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js frontend for stock_bi_v1，Bloomberg 终端风格的股票数据可视化平台。

**Architecture:** Next.js 14+ App Router，shadcn/ui + TailwindCSS 定制 Bloomberg 暗色主题，ECharts 5 做图表，SWR 做数据加载和缓存。全部页面服务端/客户端混合渲染。

**Tech Stack:** Next.js 14+, TypeScript, shadcn/ui, TailwindCSS, ECharts 5, SWR

**Spec:** `docs/superpowers/specs/2026-03-15-stock-bi-v1-design.md`

**Backend API:** 假设后端已运行在 `http://localhost:8100`，API prefix `/api/`

**视觉稿参考:** `apps/stock_bi_v1/brainstorm/` 目录下 6 个 HTML 文件

---

## Chunk 1: 项目初始化 & 全局样式

### Task 1: Next.js 项目初始化

**Files:**
- Create: `apps/stock_bi_v1/frontend/` (Next.js 项目)

- [ ] **Step 1:** 在 `apps/stock_bi_v1/frontend/` 初始化 Next.js 14+ 项目 (App Router, TypeScript, TailwindCSS, ESLint)

- [ ] **Step 2:** 安装依赖: shadcn/ui, echarts, echarts-for-react, swr, clsx

- [ ] **Step 3:** 初始化 shadcn/ui (`npx shadcn@latest init`)，选暗色主题

- [ ] **Step 4:** Commit

---

### Task 2: Bloomberg 终端风全局样式

**Files:**
- Create/Modify: `apps/stock_bi_v1/frontend/src/styles/terminal.css`
- Modify: `apps/stock_bi_v1/frontend/tailwind.config.ts`
- Modify: `apps/stock_bi_v1/frontend/src/app/globals.css`

- [ ] **Step 1:** 定制 `tailwind.config.ts` — 扩展颜色:

| Token | 值 | 用途 |
|-------|-----|------|
| bg-terminal | #0a0a0a | 页面背景 |
| bg-panel | #111111 | 面板/卡片背景 |
| border-terminal | #222222 | 边框 |
| accent | #ff8c00 | 标题/标签/高亮 |
| up | #ff3333 | 涨 (红) |
| down | #33cc33 | 跌 (绿) |

- [ ] **Step 2:** 写 `terminal.css` — 全局 body 背景色 #0a0a0a, 字体 monospace, 紧凑间距。所有 shadcn/ui 组件覆写为暗色终端风

- [ ] **Step 3:** 在 `globals.css` 引入 terminal.css

- [ ] **Step 4:** Commit

---

### Task 3: 全局布局 & 顶栏

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/layout.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/ui/TopBar.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/ui/Breadcrumb.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/ui/SearchBox.tsx`

- [ ] **Step 1:** 写 `layout.tsx` — 全局布局，包含 TopBar，body 使用 terminal 样式

- [ ] **Step 2:** 写 `TopBar.tsx`:
  - 左侧: Logo "STOCK BI" (橙色等宽字体)
  - 中间: 全局搜索框 (调 `/api/stock/search?q=`，回车跳转 `/stock/[code]`)
  - 右侧: 当前日期显示

- [ ] **Step 3:** 写 `SearchBox.tsx` — 输入框 + 下拉建议列表 (debounced SWR 调搜索 API)，选中后 router.push(`/stock/${code}`)

- [ ] **Step 4:** 写 `Breadcrumb.tsx` — 面包屑导航组件，接收 `items: {label, href}[]`，支持点击回退

- [ ] **Step 5:** Commit

---

### Task 4: API 调用层 & 工具函数

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/lib/api.ts`
- Create: `apps/stock_bi_v1/frontend/src/lib/hooks.ts`
- Create: `apps/stock_bi_v1/frontend/src/lib/format.ts`

- [ ] **Step 1:** 写 `api.ts` — 统一 fetch 封装:
  - `API_BASE` = 环境变量或默认 `http://localhost:8100`
  - `fetcher(url)` — SWR 用的通用 fetcher
  - 每个模块的 API 函数 (如 `fetchOverview()`, `fetchKline(code, period)` 等)

- [ ] **Step 2:** 写 `hooks.ts` — SWR hooks 封装:
  - `useOverview()`, `useIndices()`, `useDistribution()`
  - `useHeatmap()`, `useIndustryDetail(name)`, `useIndustryStocks(name)`
  - `useStockProfile(code)`, `useKline(code, period)`, `useValuation(code)`, `usePeers(code)`
  - `useNorthMoney(days)`, `useStockFlow(code, days)`
  - `useTopListDaily()`, `useTopListHistory(code)`

- [ ] **Step 3:** 写 `format.ts` — 数值格式化函数:
  - `formatAmount(val)` — 亿/万 自动单位
  - `formatPercent(val)` — 保留 2 位小数 + %
  - `formatPrice(val)` — 保留 2 位小数
  - `formatMV(val)` — 市值格式化 (亿)
  - `colorByChange(val)` — 返回涨色/跌色 CSS class

- [ ] **Step 4:** Commit

---

## Chunk 2: ECharts 图表组件

### Task 5: ECharts 封装组件

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/components/charts/KlineChart.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/charts/BarChart.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/charts/LineChart.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/charts/TreemapChart.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/charts/DistributionChart.tsx`

- [ ] **Step 1:** 写 `KlineChart.tsx` — K线图组件:
  - Props: data (KlineItem[]), period, indicators (MA/MACD/KDJ/BOLL 可选叠加)
  - 包含下方成交量柱状图 (红涨绿跌)
  - 日K/周K/月K 切换按钮
  - Bloomberg 风格: 黑色背景, 橙色十字线, 绿涨红跌 (中国反色)
  - 缩放/拖拽支持

- [ ] **Step 2:** 写 `TreemapChart.tsx` — 板块热力图:
  - Props: data (IndustryHeatmapItem[])
  - 颜色映射: avg_pct_chg > 0 红色渐变, < 0 绿色渐变
  - 显示: 行业名 + 涨跌幅百分比
  - 点击触发 onIndustryClick(name)

- [ ] **Step 3:** 写 `DistributionChart.tsx` — 涨跌分布柱状图:
  - Props: distribution dict
  - 横轴: 区间, 纵轴: 股票数量
  - 颜色: 涨区间红色, 跌区间绿色

- [ ] **Step 4:** 写 `LineChart.tsx` — 通用折线图:
  - Props: data, xField, yFields[], colors[]
  - 用于: 北向资金趋势, 估值趋势, 累计净流入

- [ ] **Step 5:** 写 `BarChart.tsx` — 通用柱状图:
  - Props: data, xField, yField, colorBySign (正负不同颜色)
  - 用于: 主力净流入, 资金流各档位

- [ ] **Step 6:** Commit

---

## Chunk 3: 首页仪表盘

### Task 6: 首页仪表盘页面

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/dashboard/IndexBar.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/dashboard/RankingCard.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/dashboard/NorthMoneyMini.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/dashboard/LimitSummary.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/dashboard/TopListSummary.tsx`

- [ ] **Step 1:** 写 `page.tsx` — 首页仪表盘，9 模块 Grid 布局:

```
┌─────────────── IndexBar (顶部通栏) ─────────────────┐
├──────────┬──────────────────────────────────────────┤
│ 涨跌分布  │          板块热力图 Treemap (2列宽)       │
├──────────┼──────────┬───────────────────────────────┤
│ 涨幅TOP  │ 跌幅TOP  │     北向资金 (30日折线)        │
├──────────┼──────────┼───────────────────────────────┤
│ 成交额TOP │ 换手率TOP │                              │
├──────────┴──────────┤      涨停分析                  │
│   龙虎榜摘要 (2列)   │                               │
└─────────────────────┴───────────────────────────────┘
```

每个模块右上角 "DRILL ›" 标识，点击跳转对应 Level 1 页面。

- [ ] **Step 2:** 写 `IndexBar.tsx` — 5 大指数横向排列，显示名称 + 点数 + 涨跌幅 (涨红跌绿)

- [ ] **Step 3:** 写 `RankingCard.tsx` — 复用排行卡片组件:
  - Props: title, items (TOP 5), drillPath
  - 每行: 代码 + 名称 + 涨跌幅 + 数值列
  - 点击行跳转个股详情

- [ ] **Step 4:** 写 `NorthMoneyMini.tsx` — 迷你折线图 (30 日北向净流入)，点击跳转 /flow

- [ ] **Step 5:** 写 `LimitSummary.tsx` — 涨停/跌停数 + 炸板率 + 连板梯队迷你条形图，点击跳转 /limit

- [ ] **Step 6:** 写 `TopListSummary.tsx` — 龙虎榜摘要 (TOP 5 上榜股)，点击跳转 /toplist

- [ ] **Step 7:** Commit

---

## Chunk 4: Level 1 钻取页

### Task 7: 行业详情页

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/industry/page.tsx`

- [ ] **Step 1:** 写 `industry/page.tsx` — 行业详情 (通过 query param `?name=` 传行业名):
  - 面包屑: 首页 › 行业名
  - 行业统计卡片 (涨跌家数, 平均涨幅, 成交额, 主力净流入) — 4 格横排
  - 行业内个股排行表格 (shadcn Table): 代码/名称/涨跌幅/价格/成交额/换手率/PE/主力净流入
  - 表格支持点击列头排序
  - 点击行跳转 `/stock/[code]`

- [ ] **Step 2:** Commit

---

### Task 8: 北向资金详情页

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/flow/page.tsx`

- [ ] **Step 1:** 写 `flow/page.tsx`:
  - 面包屑: 首页 › 北向资金
  - 沪股通 / 深股通 分项折线图 (双线对比)
  - 历史净流入趋势 (日/周/月 Tab 切换)
  - 今日北向净买入个股 TOP (表格，点击跳转个股)

- [ ] **Step 2:** Commit

---

### Task 9: 龙虎榜详情页

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/toplist/page.tsx`

- [ ] **Step 1:** 写 `toplist/page.tsx`:
  - 面包屑: 首页 › 龙虎榜
  - 今日上榜个股列表 (涨幅/换手/买卖额/原因)
  - 点击个股行展开/折叠营业部买卖明细
  - 点击股票名/代码跳转个股详情

- [ ] **Step 2:** Commit

---

### Task 10: 涨停详情页

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/limit/page.tsx`

- [ ] **Step 1:** 写 `limit/page.tsx`:
  - 面包屑: 首页 › 涨停分析
  - 涨停股完整列表 (代码/名称/涨幅/连板天数/行业/成交额)
  - 连板梯队可视化 (5板/4板/.../首板 分组显示)
  - 涨停行业分布 (基于 stock_basic.industry)
  - 点击跳转个股详情

- [ ] **Step 2:** Commit

---

## Chunk 5: 个股详情页 (Level 2)

### Task 11: 个股详情页 — 固定区域

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/stock/[code]/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/StockHeader.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/QuickIndicators.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/ValuationPanel.tsx`

- [ ] **Step 1:** 写 `page.tsx` — 个股详情页骨架:
  - 面包屑导航 (动态: 首页 › [来源页] › 股票名)
  - 上方固定区域 + 下方 Tab 区域

- [ ] **Step 2:** 写 `StockHeader.tsx` — 股票头部:
  - 名称 + 代码 + 行业 + 交易所
  - 当前价格 (大字) + 涨跌幅 (涨红跌绿)

- [ ] **Step 3:** 写 `QuickIndicators.tsx` — 快速指标条:
  - 一行显示: 开/高/低/昨收/成交量/成交额/换手率/振幅

- [ ] **Step 4:** K线图区域 (左侧 2/3):
  - 使用 KlineChart 组件
  - 周期切换按钮: 日K / 周K / 月K
  - 指标叠加选择: MA / MACD / KDJ / BOLL

- [ ] **Step 5:** 写 `ValuationPanel.tsx` — 估值面板 (右侧 1/3):
  - PE(TTM) / PB / PS(TTM) / 总市值 / 流通市值 / 总股本 / 流通股 / 换手率
  - 同板块个股排名 TOP 5 (使用 peers API)

- [ ] **Step 6:** Commit

---

### Task 12: 个股详情页 — 底部 5 个 Tab

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/components/stock/tabs/FlowTab.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/tabs/ValuationTab.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/tabs/OrderFlowTab.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/tabs/TopListTab.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/stock/tabs/HistoryTab.tsx`

- [ ] **Step 1:** 写 `FlowTab.tsx` — 资金流向:
  - 今日四档位 (特大/大/中/小单) 买卖明细表格
  - 近 30 日主力净流入柱状图 (正红负绿)
  - 累计净流入曲线

- [ ] **Step 2:** 写 `ValuationTab.tsx` — 估值趋势:
  - PE/PB/PS 历史走势图 (可叠加，checkbox 切换)
  - 当前百分位计算显示
  - 估值带 (均值 ± 标准差)

- [ ] **Step 3:** 写 `OrderFlowTab.tsx` — 大单明细:
  - 各档位买卖量趋势图
  - 主力净流入占比

- [ ] **Step 4:** 写 `TopListTab.tsx` — 龙虎榜记录:
  - 历史上榜日期列表
  - 每行: 日期 + 收盘价 + 涨幅 + 营业部买卖额 + 上榜原因

- [ ] **Step 5:** 写 `HistoryTab.tsx` — 历史行情:
  - 可滚动表格 (日期/开高低收/量/额/涨跌幅)
  - 分页加载 (page + size 参数)

- [ ] **Step 6:** Commit

---

## Chunk 6: 高级筛选页

### Task 13: 高级筛选器

**Files:**
- Create: `apps/stock_bi_v1/frontend/src/app/screener/page.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/filters/FilterTag.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/filters/FilterBuilder.tsx`
- Create: `apps/stock_bi_v1/frontend/src/components/tables/ScreenerTable.tsx`

- [ ] **Step 1:** 写 `FilterBuilder.tsx` — 筛选条件构建器:
  - 动态添加/删除条件 (Tag 式)
  - 每个条件: 字段下拉 (从 /api/screener/filters 获取) + 运算符下拉 (介于/大于/小于/等于) + 值输入
  - "筛选" 按钮触发 POST /api/screener/query

- [ ] **Step 2:** 写 `FilterTag.tsx` — 单个筛选条件 Tag 组件:
  - 显示: "PE(TTM) > 5" 格式
  - 可关闭 (删除条件)

- [ ] **Step 3:** 写 `ScreenerTable.tsx` — 筛选结果表格:
  - 列: 代码/名称/涨跌幅/PE/PB/市值/换手/主力净流入/行业
  - 点击列头排序 (更新 sort_by 重新请求)
  - 分页控件
  - 点击行跳转个股详情
  - "导出 CSV" 按钮 (POST /api/screener/export，下载文件)

- [ ] **Step 4:** 写 `screener/page.tsx` — 组装 FilterBuilder + ScreenerTable

- [ ] **Step 5:** Commit

---

## Chunk 7: 收尾

### Task 14: 页面间导航 & 响应式适配

- [ ] **Step 1:** 确保所有钻取链接正确:
  - 仪表盘各模块 → 对应 Level 1 页面
  - Level 1 表格行 → /stock/[code]
  - 面包屑 → 回退到任意层级

- [ ] **Step 2:** 响应式适配: 确保仪表盘在 1440px+ 宽屏下信息密度最高，在 1024px 以下适当折叠

- [ ] **Step 3:** Commit

---

### Task 15: 全量验证

- [ ] **Step 1:** 前端 dev server 启动验证: `cd apps/stock_bi_v1/frontend && npm run dev`

- [ ] **Step 2:** 逐页面检查:
  - 首页仪表盘 9 模块全部渲染
  - 行业/北向/龙虎榜/涨停 4 个 Level 1 页面
  - 个股详情页 5 个 Tab
  - 高级筛选器条件添加 + 查询 + 导出

- [ ] **Step 3:** Final commit

---

## Summary

| Chunk | Tasks | 交付物 |
|-------|-------|--------|
| 1: 初始化 & 样式 | 1-4 | Next.js 项目 + Bloomberg 主题 + 全局布局 + API 层 |
| 2: 图表组件 | 5 | K线/Treemap/分布/折线/柱状 5 个 ECharts 封装 |
| 3: 首页仪表盘 | 6 | 9 模块 Dashboard + 钻取入口 |
| 4: Level 1 页面 | 7-10 | 行业/北向/龙虎榜/涨停 4 个钻取页 |
| 5: 个股详情 | 11-12 | 固定区域 + 5 个 Tab |
| 6: 高级筛选 | 13 | 动态条件构建 + 结果表格 + CSV 导出 |
| 7: 收尾 | 14-15 | 导航验证 + 响应式 + 全量检查 |

**Total: 15 tasks, ~40 steps**
