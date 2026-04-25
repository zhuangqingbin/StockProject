# Analysis

`apps/data_hub/data_pipeline_ts/analysis/` 是 `data_hub` 内基于数据库的研究与策略矩阵区域。

## 包含的内容

- 策略族目录，如 `bottom_val_strategies`
- 顶层编排脚本，如 `run_strategy_suite.py`
- 从历史研究产出沉淀下来的 findings 总结

## 稳定的矩阵入口

- `bottom_volume_matrix`
- `flow_chip_northbound_matrix`
- `limit_inst_matrix`
- `supply_shock_matrix`
- `top_list_matrix`

## 常用命令

跑统一策略套件：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite \
  --start-date 20240101
```

直接跑单个矩阵：

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix \
  --start-date 20240101
```
