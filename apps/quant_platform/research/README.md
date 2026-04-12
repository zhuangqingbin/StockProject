# Quant Research

## 启动命令

以下命令都在项目根目录 `/Users/qingbin.zhuang/Personal/StockProject` 下执行。

```bash
# 1. 启动后端 API（默认 8202）
bash apps/quant_platform/scripts/run.sh backend

# 2. 启动前端开发服务器（默认 3001）
bash apps/quant_platform/scripts/run.sh frontend

# 3. 打开 research notebooks
bash apps/quant_platform/scripts/run.sh research-notebook

# 4. 直接从 tushare_database 生成多表研究产物
bash apps/quant_platform/scripts/run.sh research-factor \
  --from-db \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output-dir apps/quant_platform/research/output/full_research

# 5. 发布前端研究快照：因子清单、推荐股票、单股钻取
bash apps/quant_platform/scripts/run.sh research-publish \
  --from-db \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output-dir apps/quant_platform/research/output/full_research

# 6. 跑完整 overnight pipeline：因子筛选 + 组合因子 + 策略比较
apps/.venv/bin/python -m apps.quant_platform.research.scripts.run_full_pipeline \
  --start-date 2023-01-01 \
  --end-date 2025-12-31 \
  --max-factors 60

# 7. 对已有 panel.csv 跑多因子排行
bash apps/quant_platform/scripts/run.sh research-factor \
  --panel-csv /path/to/panel.csv \
  --factor pct_chg \
  --factor net_mf_rate

# 8. 对已有 panel.csv 跑组合因子回测
bash apps/quant_platform/scripts/run.sh research-backtest \
  --panel-csv /path/to/panel.csv \
  --factor alpha_1 \
  --factor alpha_2
```

启动后可访问：

- 前端研究页：`http://localhost:3001/research`
- 后端文档：`http://localhost:8202/docs`
- 研究产出静态资源：`http://localhost:8202/research-assets/...`

如果你已经用 `data_hub` 的 `run_daily.sh` 跑 nightly profile，那么 `reference_calendar_nightly` 成功后会默认自动触发一次 `research-publish`。也就是说，数据库夜间更新完成后，`/research` 页会自动刷新到最新快照；如需关闭，可设置：

```bash
export QV_RESEARCH_AUTO_PUBLISH_ENABLED=0
```

## 模块目标

这个目录是 `quant_platform` 里的 A 股因子研究与组合回测模块，直接读取 `tushare_database`，研究目标是：

```text
overnight_return = (T+1 open - T close) / T close
```

主链路包括：

- 多表数据加载与事件时效性处理
- 股票池过滤
- 多层因子构建
- 因子标准化、IC/分层/相关性分析
- 组合因子合成
- 向量化组合回测
- HTML / CSV / PNG 研究产出
- 发布 serving snapshot，给 `/research` 提供因子推荐股票与单股钻取
- Web UI 集成到 `/research`

## 目录说明

```text
apps/quant_platform/research/
├── README.md
├── REQUIREMENTS.md
├── config.py
├── data_loader.py
├── pipeline.py
├── universe.py
├── factor_engine/
├── analyzer/
├── strategy/
├── scripts/
├── notebooks/
└── output/
```

重点目录：

- `factor_engine/`: 技术、资金流、筹码、北向、两融、涨跌停、龙虎榜、股东、事件、财务、行业、市场、组合因子
- `analyzer/`: IC、分层回测、相关性、报告生成
- `strategy/`: 信号生成、退出规则、A 股约束、向量化组合回测
- `scripts/`: 命令行入口
- `notebooks/`: 从数据探索到策略回测的 5 本工作簿
- `output/`: 研究产物目录，已加入 `.gitignore`

## 主要入口

### 1. `run_single_factor.py`

单因子分析入口，适合快速验证一个因子：

- 输出 IC 指标
- 输出分层回测结果

### 2. `run_factor_research.py`

多因子研究入口，有两种常用方式：

- `--panel-csv`: 对现成面板跑排行
- `--from-db`: 从数据库加载完整研究面板并产出分样本报告

主要产物：

- `factor_ranking.csv`
- `factor_ranking.html`
- `*_detail.html`
- `*_summary.csv`
- `*_ic.png`
- `*_layered.png`
- `*_correlation.png`
- `split_factor_summary.csv`
- `qualified_factor_summary.csv`

### 3. `run_full_pipeline.py`

完整研究流水线：

- 加载主表和辅助表
- 构建全量因子
- 标准化
- 因子筛选
- 组合因子生成
- 多策略组合回测
- 输出策略比较报告

主要产物：

- `factor_ranking_full.csv`
- `factor_ranking_full.html`
- `strategy_comparison.csv`
- `strategy_comparison.html`
- `strategy_comparison_sharpe.png`
- `best_strategy.json`

### 4. `run_strategy_backtest.py`

对已有因子面板跑组合回测，默认写出：

- `apps/quant_platform/research/output/backtest_results/strategy_summary.json`

## Notebook 路线

`notebooks/` 里的 5 个文件对应标准研究顺序：

1. `01_data_exploration.ipynb`
   数据基座、缺失率、覆盖率检查
2. `02_single_factor_analysis.ipynb`
   单因子 IC 与分层分析
3. `03_factor_screening.ipynb`
   多因子排行、覆盖率和稳定性筛选
4. `04_composite_factor.ipynb`
   等权 / IC 加权 / PCA / ML 组合因子对比
5. `05_strategy_backtest.ipynb`
   组合因子回测与 NAV 对比

## 输出目录

常见输出位置：

- `output/ic_reports/`
  单因子报告、排行、相关性图
- `output/full_research/`
  `--from-db` 生成的全量研究面板与 split summary
- `output/backtest_results/`
  回测 summary JSON
- `output/notebook_*` / `output/notebook_exports/`
  notebook 导出的临时结果

如果后端已启动，这些产物会通过 `/research-assets/*` 自动暴露给前端研究页。

## 依赖与环境

默认使用共享虚拟环境 `apps/.venv`。

研究链路依赖：

- `pandas`
- `numpy`
- `scikit-learn`
- `scipy`
- `matplotlib`
- `seaborn`
- `lightgbm`
- `xgboost`
- `jupyterlab`

数据库相关配置复用项目根目录环境变量，至少需要：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_CHARSET`
- `TUSHARE_TOKEN`

## 建议使用顺序

如果要完整跑一遍，建议顺序是：

1. 启动 `backend`
2. 启动 `frontend`
3. 执行 `research-factor --from-db`
4. 打开 `/research` 看 factor ranking、qualified summary、detail HTML
5. 如需更深分析，打开 `research-notebook`
6. 如需策略比较，执行 `run_full_pipeline.py`

## 相关文件

- 需求文档：[REQUIREMENTS.md](/Users/qingbin.zhuang/Personal/StockProject/apps/quant_platform/research/REQUIREMENTS.md)
- 平台总说明：[README.md](/Users/qingbin.zhuang/Personal/StockProject/apps/quant_platform/README.md)
- 统一启动脚本：[run.sh](/Users/qingbin.zhuang/Personal/StockProject/apps/quant_platform/scripts/run.sh)
