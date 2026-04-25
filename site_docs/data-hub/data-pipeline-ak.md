# data_pipeline_ak

`data_pipeline_ak` 是 `data_hub` 内的 AkShare 辅助上下文。

## 当前定位

- 提供 AkShare 一侧的导入能力
- 作为 TuShare runner 之外、轻量的兜底与扩展点
- 当前主要服务于交易日历相关的导入

## 当前结构

- `apps/data_hub/data_pipeline_ak/calendar.py`
- `apps/data_hub/data_pipeline_ak/fetchers/calendar.py`
- `apps/data_hub/data_pipeline_ak/provider/client.py`
- `apps/data_hub/data_pipeline_ak/tests/test_calendar.py`

## 备注

这个上下文体量明显比 `data_pipeline_ts` 小。仓库级文档应该把它定位为"AkShare 支持模块"，而不是另一个完整的生产调度器。
