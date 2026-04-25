# 测试

## Python 测试套件

跑维护中的 Python 测试：

```bash
python -m pytest -q
```

## 按应用范围跑

`data_hub` 测试：

```bash
python -m pytest -q \
  apps/data_hub/tests \
  apps/data_hub/data_explorer/tests \
  apps/data_hub/data_pipeline_ts/tests \
  apps/data_hub/data_pipeline_ak/tests
```

`data_explorer` 前端测试：

```bash
npm --prefix apps/data_hub/data_explorer/frontend test
```

`quant_platform` 测试：

```bash
python -m pytest -q apps/quant_platform/tests
```
