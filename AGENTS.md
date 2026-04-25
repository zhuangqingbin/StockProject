# Repository Guidelines

## 项目结构与模块组织
这是一个以 Python 为主的 A 股工具单仓库。当前生产工作主要集中在 `apps/data_hub/`：`data_pipeline_ts/` 负责 TuShare 抓取与调度，`data_pipeline_ak/` 负责 AkShare 辅助导入，`data_explorer/` 提供只读 FastAPI + React 浏览与监控界面。`apps/quant_platform/` 主要承载研究和下游消费。共享运行时能力位于 `shared/stock_core/`，长期文档放在 `docs/`。`experiments/`、`.cache/`、`dist/` 和 `node_modules/` 视为生成物或探索性内容。

## data_pipeline_ts 当前数据约定
`apps/data_hub/data_pipeline_ts/` 当前做日级研究、横截面扫描、事件回测、策略分析时，默认主表是 `stock_stk_factor_pro`。这张表已经覆盖日线行情、日线基础指标、估值/市值、换手率以及大批技术指标，后续分析应优先从它出发，再按 `(ts_code, trade_date)` 关联 `stock_money_flow`、`stock_cyq_perf`、`stock_margin_detail`、`stock_hk_hold`、`stock_limit_list_d`、`stock_top_inst` 等侧表。

- `stock_daily` 和 `stock_daily_basic` 仍然保留，主要是兼容历史表结构；新的历史回溯、新策略分析、新特征工程不要再把这两张表作为日级基表，统一以 `stk_factor_pro` / `stock_stk_factor_pro` 为准。
- 默认所有分析、筛选、回测、信号扫描所用数据都从数据库数据表读取；优先直接查询 `stock_stk_factor_pro` 及其关联表，不要把 TuShare/AkShare 实时接口返回、CSV/Excel、本地缓存文件或临时导出文件当作分析输入，除非用户明确要求。
- 日级收益和价格口径优先使用前复权字段，例如 `open_qfq`、`high_qfq`、`low_qfq`、`close_qfq`。`pre_close` 继承自 `daily` 接口的历史口径，与前一日 `close_qfq` 不严格对齐，策略计算里通常不要依赖。
- 当前分析脚本已经按这个约定实现：`analysis/cross_factor/analyze.py`、`analysis/daily_signal_scan.py`、`analysis/factor_importance.py` 等都以 `stock_stk_factor_pro` 为基础表。
- 当前 fetcher schema 中这张表共有 261 列，索引为 `trade_date`、`(trade_date, ts_code)`、`ts_code`。

### `stock_stk_factor_pro` 列信息
源定义以 `apps/data_hub/data_pipeline_ts/fetchers/special_data/stock_stk_factor_pro.py` 为准。读表时默认按下面的语义理解：

- 无后缀字段：不复权原始口径
- `_hfq`：后复权
- `_qfq`：前复权
- `_5`、`_10`、`_20`、`_30`、`_60`、`_90`、`_250` 等数字后缀：指标窗口参数

| 字段/字段组 | 说明 |
| --- | --- |
| `ts_code` | 股票代码 |
| `trade_date` | 交易日期 |
| `open` / `open_hfq` / `open_qfq` | 开盘价 / 开盘价(后复权) / 开盘价(前复权) |
| `high` / `high_hfq` / `high_qfq` | 最高价 / 最高价(后复权) / 最高价(前复权) |
| `low` / `low_hfq` / `low_qfq` | 最低价 / 最低价(后复权) / 最低价(前复权) |
| `close` / `close_hfq` / `close_qfq` | 收盘价 / 收盘价(后复权) / 收盘价(前复权) |
| `pre_close` | 昨收价(前复权)。来自 `daily` 接口历史口径，和前一日 `close_qfq` 可能对不上，策略分析里通常不用它做收益基准。 |
| `change` | 涨跌额 |
| `pct_chg` | 涨跌幅(除权后的涨跌幅) |
| `vol` | 成交量(手) |
| `amount` | 成交额(千元) |
| `turnover_rate` | 换手率(%) |
| `turnover_rate_f` | 换手率(自由流通股) |
| `volume_ratio` | 量比 |
| `pe` | 市盈率(总市值/净利润，亏损时为空) |
| `pe_ttm` | 市盈率(TTM，亏损时为空) |
| `pb` | 市净率(总市值/净资产) |
| `ps` / `ps_ttm` | 市销率 / 市销率(TTM) |
| `dv_ratio` / `dv_ttm` | 股息率(%) / 股息率(TTM)(%) |
| `total_share` / `float_share` / `free_share` | 总股本(万股) / 流通股本(万股) / 自由流通股本(万) |
| `total_mv` / `circ_mv` | 总市值(万元) / 流通市值(万元) |
| `adj_factor` | 复权因子 |
| `downdays` / `updays` | 连跌天数 / 连涨天数 |
| `lowdays` / `topdays` | `LOWRANGE(LOW)` / `TOPRANGE(HIGH)`，表示当前价位在最近区间中的极值位置 |
| `asi_[bfq\|hfq\|qfq]` / `asit_[bfq\|hfq\|qfq]` | 振动升降指标 ASI / ASIT，基于 `OPEN`、`CLOSE`、`HIGH`、`LOW` |
| `atr_[bfq\|hfq\|qfq]` | 真实波动均值 ATR，基于 `CLOSE`、`HIGH`、`LOW` |
| `bbi_[bfq\|hfq\|qfq]` | BBI 多空指标 |
| `bias1_[bfq\|hfq\|qfq]` / `bias2_[bfq\|hfq\|qfq]` / `bias3_[bfq\|hfq\|qfq]` | BIAS 乖离率 |
| `boll_lower_[bfq\|hfq\|qfq]` / `boll_mid_[bfq\|hfq\|qfq]` / `boll_upper_[bfq\|hfq\|qfq]` | BOLL 布林带下轨 / 中轨 / 上轨 |
| `brar_ar_[bfq\|hfq\|qfq]` / `brar_br_[bfq\|hfq\|qfq]` | BRAR 情绪指标 |
| `cci_[bfq\|hfq\|qfq]` | CCI 顺势指标 |
| `cr_[bfq\|hfq\|qfq]` | CR 价格动量指标 |
| `dfma_dif_[bfq\|hfq\|qfq]` / `dfma_difma_[bfq\|hfq\|qfq]` | 平行线差指标 DFMA |
| `dmi_adx_[bfq\|hfq\|qfq]` / `dmi_adxr_[bfq\|hfq\|qfq]` / `dmi_mdi_[bfq\|hfq\|qfq]` / `dmi_pdi_[bfq\|hfq\|qfq]` | DMI 动向指标族 |
| `dpo_[bfq\|hfq\|qfq]` / `madpo_[bfq\|hfq\|qfq]` | 区间震荡线 DPO / 平滑 DPO |
| `ema_[bfq\|hfq\|qfq]_{5,10,20,30,60,90,250}` | 指数移动平均 EMA，不同窗口 |
| `emv_[bfq\|hfq\|qfq]` / `maemv_[bfq\|hfq\|qfq]` | 简易波动指标 EMV / 平滑 EMV |
| `expma_12_[bfq\|hfq\|qfq]` / `expma_50_[bfq\|hfq\|qfq]` | EXPMA 指数平均数指标 |
| `kdj_[bfq\|hfq\|qfq]` / `kdj_d_[bfq\|hfq\|qfq]` / `kdj_k_[bfq\|hfq\|qfq]` | KDJ 指标及 K、D 分量 |
| `ktn_down_[bfq\|hfq\|qfq]` / `ktn_mid_[bfq\|hfq\|qfq]` / `ktn_upper_[bfq\|hfq\|qfq]` | 肯特纳通道下轨 / 中轨 / 上轨 |
| `ma_[bfq\|hfq\|qfq]_{5,10,20,30,60,90,250}` | 简单移动平均 MA，不同窗口 |
| `macd_[bfq\|hfq\|qfq]` / `macd_dea_[bfq\|hfq\|qfq]` / `macd_dif_[bfq\|hfq\|qfq]` | MACD 柱值 / DEA / DIF |
| `mass_[bfq\|hfq\|qfq]` / `ma_mass_[bfq\|hfq\|qfq]` | 梅斯线 MASS / 平滑 MASS |
| `mfi_[bfq\|hfq\|qfq]` | MFI 资金流量指标 |
| `mtm_[bfq\|hfq\|qfq]` / `mtmma_[bfq\|hfq\|qfq]` | 动量指标 MTM / 平滑 MTM |
| `obv_[bfq\|hfq\|qfq]` | OBV 能量潮指标 |
| `psy_[bfq\|hfq\|qfq]` / `psyma_[bfq\|hfq\|qfq]` | PSY 心理线 / 平滑心理线 |
| `roc_[bfq\|hfq\|qfq]` / `maroc_[bfq\|hfq\|qfq]` | ROC 变动率 / 平滑 ROC |
| `rsi_[bfq\|hfq\|qfq]_{6,12,24}` | RSI，不同窗口 |
| `taq_down_[bfq\|hfq\|qfq]` / `taq_mid_[bfq\|hfq\|qfq]` / `taq_up_[bfq\|hfq\|qfq]` | 唐安奇通道下轨 / 中轨 / 上轨 |
| `trix_[bfq\|hfq\|qfq]` / `trma_[bfq\|hfq\|qfq]` | TRIX 三重指数平滑平均线 / 平滑 TRIX |
| `vr_[bfq\|hfq\|qfq]` | VR 容量比率 |
| `wr_[bfq\|hfq\|qfq]` / `wr1_[bfq\|hfq\|qfq]` | 威廉指标 WR / WR1 |
| `xsii_td1_[bfq\|hfq\|qfq]` / `xsii_td2_[bfq\|hfq\|qfq]` / `xsii_td3_[bfq\|hfq\|qfq]` / `xsii_td4_[bfq\|hfq\|qfq]` | 薛斯通道 II 四条通道线 |

## 构建、测试与开发命令
使用 Python 3.11+，并优先通过 `./shared/scripts/resolve_project_python.sh` 解析仓库运行时。`bash apps/setup.sh` 会创建共享虚拟环境 `apps/.venv`。`python -m pytest -q` 运行维护中的 Python 测试集。`bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --help` 用于查看抓取入口参数。`./apps/data_hub/data_explorer/scripts/run.sh backend` 启动后端 API，`./apps/data_hub/data_explorer/scripts/run.sh frontend` 启动前端 Vite 开发服务。前端单测使用 `npm --prefix apps/data_hub/data_explorer/frontend test`。

## 代码风格与命名约定
优先遵循局部既有风格，不要做大范围格式化。Python 使用 4 空格缩进、类型标注、`snake_case` 模块名，以及 `create_app()` 风格的 FastAPI 入口工厂。TypeScript/React 使用 2 空格缩进、双引号、`PascalCase` 组件名，例如 `CategoryTree.tsx`，以及 `camelCase` 的工具函数或状态仓库名，例如 `navigationStore.ts`。仓库没有统一格式化器，改动应尽量小且与周边代码保持一致。

## 测试规范
`pyproject.toml` 已配置 pytest 搜索路径，包括 `apps/data_hub/tests`、`apps/data_hub/data_explorer/tests`、`apps/data_hub/data_pipeline_ts/tests`、`apps/data_hub/data_pipeline_ak/tests` 和 `apps/quant_platform/tests`。Python 测试文件命名为 `test_*.py`；前端测试使用 `*.test.ts` 或 `*.test.tsx`。凡是修改调度链路、后端模块或 UI 流程，都应补充针对性的回归测试。

## 提交与合并请求规范
近期提交历史遵循 Conventional Commit 前缀，如 `feat:`、`fix:`、`docs:`、`refactor:` 和 `chore:`。每次提交应尽量只覆盖一个应用或一个共享模块。Pull Request 需要说明影响范围、列出已执行命令、注明 `.env` 或数据表结构变更，并在前端修改时附上截图。

## 安全与配置提示
不要提交任何密钥或凭据。请从 `env.example` 开始配置，真实值放在 `.env` 或 `.env.local` 中；新增环境变量时同步补充文档说明。共享 MySQL 和行情数据凭据必须通过环境变量加载，不能写死在代码里。
