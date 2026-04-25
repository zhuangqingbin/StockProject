# 快速上手

## 环境基线

- Python `3.11+`
- 前端开发需要 Node.js `18+`
- MySQL，凭据从 `.env` 或 `.env.local` 加载

## 共享 Python 运行时

定位项目使用的 Python：

```bash
./shared/scripts/resolve_project_python.sh
```

创建共享虚拟环境 `apps/.venv` 并安装依赖：

```bash
bash apps/setup.sh
```

## 常用启动命令

启动 `data_explorer` 后端与前端：

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

启动 `quant_platform` 后端与前端：

```bash
bash apps/quant_platform/scripts/run.sh backend
bash apps/quant_platform/scripts/run.sh frontend
```

## 本地预览文档门户

使用项目共享 Python：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m mkdocs serve
```
