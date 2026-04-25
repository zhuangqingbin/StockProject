# data_explorer

`data_explorer` 是 `data_hub` 数据库的只读目录、预览与监控应用。

## 功能

- 表目录浏览
- 表结构与索引查看
- 分页数据预览
- 任务与运行监控
- 数据库级元数据视图

## 启动命令

启动后端：

```bash
./apps/data_hub/data_explorer/scripts/run.sh backend
```

启动前端：

```bash
./apps/data_hub/data_explorer/scripts/run.sh frontend
```

跑测试：

```bash
python -m pytest -q apps/data_hub/data_explorer/tests
npm --prefix apps/data_hub/data_explorer/frontend test
```
