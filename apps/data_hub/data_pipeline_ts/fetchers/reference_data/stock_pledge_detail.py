from __future__ import annotations

from typing import Any

import pandas as pd
from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class PledgeDetailFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=111
    股权质押明细, 500积分
        触发时遍历全市场股票代码提取股权质押明细, 并按传入的 snapshot_date 保存快照。
    API params:
        ts_code: 股票代码
    """
    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "holder_name",  # 股东名称
        "pledge_amount",  # 质押数量（万股）
        "start_date",  # 质押开始日期
        "end_date",  # 质押结束日期
        "is_release",  # 是否已解押
        "release_date",  # 解押日期
        "pledgor",  # 质押方
        "holding_amount",  # 持股总数（万股）
        "pledged_amount",  # 质押总数（万股）
        "p_total_ratio",  # 本次质押占总股本比例
        "h_total_ratio",  # 持股总数占总股本比例
        "is_buyback",  # 是否回购（0否 1是）
        "snapshot_date",  # 观测快照日期
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "holder_name": ColumnDef("VARCHAR(128)", nullable=True, comment="股东名称"),
            "pledge_amount": ColumnDef("DOUBLE", nullable=True, comment="质押数量（万股）"),
            "start_date": ColumnDef("CHAR(8)", nullable=True, comment="质押开始日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="质押结束日期"),
            "is_release": ColumnDef("TINYINT", nullable=True, comment="是否已解押"),
            "release_date": ColumnDef("CHAR(8)", nullable=True, comment="解押日期"),
            "pledgor": ColumnDef("VARCHAR(128)", nullable=True, comment="质押方"),
            "holding_amount": ColumnDef("DOUBLE", nullable=True, comment="持股总数（万股）"),
            "pledged_amount": ColumnDef("DOUBLE", nullable=True, comment="质押总数（万股）"),
            "p_total_ratio": ColumnDef("DOUBLE", nullable=True, comment="本次质押占总股本比例"),
            "h_total_ratio": ColumnDef("DOUBLE", nullable=True, comment="持股总数占总股本比例"),
            "is_buyback": ColumnDef("TINYINT", nullable=True, comment="是否回购（0否 1是）"),
            "snapshot_date": ColumnDef("CHAR(8)", nullable=True, comment="观测快照日期"),
        },
        composite_indexes=[
            ('snapshot_date',),
            ('snapshot_date', 'ts_code'),
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('end_date',),
            ('end_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any):
        snapshot_date = str(kwargs.pop("snapshot_date", "")).strip()
        if not snapshot_date:
            raise ValueError("pledge_detail fetches require snapshot_date")
        if "ts_code" in kwargs:
            raise ValueError("pledge_detail fetches require stock_codes")

        stock_codes = kwargs.pop("stock_codes", None)
        result = self.fanout_by_stock_codes(
            stock_codes=stock_codes,
            stock_basic_statuses=("L",), # 上市状态 L上市 D退市 G过会未交易 P暂停上市
            columns=self.fields[:-1],
            fetch_one=lambda stock_code: self.client.call(
                "pledge_detail",
                ts_code=stock_code,
                fields=",".join(self.fields[:-1]),
                **kwargs,
            ),
        )
        if result.empty:
            return pd.DataFrame(columns=self.fields)
        result["snapshot_date"] = snapshot_date
        return result.reindex(columns=self.fields)
