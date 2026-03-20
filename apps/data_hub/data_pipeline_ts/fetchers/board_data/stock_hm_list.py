from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class HMListFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=311
    市场游资最全名录
        触发时直接调用 hm_list 接口, 并按传入的 snapshot_date 保存快照。
    API params:
        name: 游资名称
    """
    fields = [
        "name",  # 游资名称
        "desc",  # 说明
        "orgs",  # 关联机构
        "snapshot_date",  # 观测快照日期
    ]
    table_schema = TableSchema(
        columns={
            "name": ColumnDef("VARCHAR(255)", nullable=True, comment="游资名称"),
            "desc": ColumnDef("TEXT", nullable=True, comment="说明"),
            "orgs": ColumnDef("TEXT", nullable=True, comment="关联机构"),
            "snapshot_date": ColumnDef("CHAR(8)", nullable=True, comment="观测快照日期"),
        },
        composite_indexes=[
            ('snapshot_date',),
            ('snapshot_date', 'name'),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:

        snapshot_date = str(kwargs.pop("snapshot_date", "")).strip()
        if not snapshot_date:
            raise ValueError("hm_list fetches require snapshot_date")
        frame = self.client.call("hm_list", 
            fields=",".join(self.fields[:-1]),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        result = pd.DataFrame(frame).reindex(columns=self.fields[:-1])
        result["snapshot_date"] = snapshot_date
        return result.reindex(columns=self.fields)
