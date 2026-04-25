# Strategy Suite

Strategy Suite 是把所有稳定矩阵脚本一次跑完的统一入口。

## 入口

使用 `run_strategy_suite.py`：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.run_strategy_suite \
  --start-date 20240101 \
  --strategies bottom_volume_matrix,limit_inst_matrix,top_list_matrix
```

## 通用参数

- `--start-date`
- `--end-date`
- `--strategies`
- `--min-sample`
- `--top-n`
- `--output-dir`

## 输出结构

套件会在 `analysis/outputs/strategy_suite/` 下建立带时间戳的根目录，并产出：

- `suite_summary.csv`
- `suite_compact_ranking.csv`
- `suite_compact_by_strategy.csv`

每个子策略也仍然在自己对应的 suite 子目录下输出带时间戳的 CSV 与 Markdown 总结。
