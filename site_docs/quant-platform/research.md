# Research

`apps/quant_platform/research/` 是仓库的因子、排序与回测研究入口。

## 常用研究入口

直接从数据库做因子研究，使用 `research-factor --from-db`：

```bash
bash apps/quant_platform/scripts/run.sh research-factor \
  --from-db \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output-dir apps/quant_platform/research/output/full_research
```

跑完整 pipeline：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.quant_platform.research.scripts.run_full_pipeline \
  --start-date 2023-01-01 \
  --end-date 2025-12-31 \
  --max-factors 60
```

## 对外暴露

- 前端路由：`/research`
- 后端应用提供的 API 文档
- 通过 `research-assets` 提供的静态产出
