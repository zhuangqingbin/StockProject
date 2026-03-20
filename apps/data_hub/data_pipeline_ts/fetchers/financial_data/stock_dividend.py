from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class DividendFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=103
    分红送股, 2000积分
        按公告日期提取全市场分红送股数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        record_date: 股权登记日(YYYYMMDD)
        ex_date: 除权除息日(YYYYMMDD)
        imp_ann_date: 实施公告日(YYYYMMDD)
    """

    fields = [
        "ts_code",  # TS代码
        "end_date",  # 分红年度
        "ann_date",  # 预案公告日
        "div_proc",  # 实施进度
        "stk_div",  # 每股送转
        "stk_bo_rate",  # 每股送股比例
        "stk_co_rate",  # 每股转增比例
        "cash_div",  # 每股分红（税后）
        "cash_div_tax",  # 每股分红（税前）
        "record_date",  # 股权登记日
        "ex_date",  # 除权除息日
        "pay_date",  # 派息日
        "div_listdate",  # 红股上市日
        "imp_ann_date",  # 实施公告日
        "base_date",  # 基准日
        "base_share",  # 基准股本（万）
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="分红年度"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="预案公告日"),
            "div_proc": ColumnDef("VARCHAR(32)", nullable=True, comment="实施进度"),
            "stk_div": ColumnDef("DOUBLE", nullable=True, comment="每股送转"),
            "stk_bo_rate": ColumnDef("DOUBLE", nullable=True, comment="每股送股比例"),
            "stk_co_rate": ColumnDef("DOUBLE", nullable=True, comment="每股转增比例"),
            "cash_div": ColumnDef("DOUBLE", nullable=True, comment="每股分红(税后)"),
            "cash_div_tax": ColumnDef("DOUBLE", nullable=True, comment="每股分红(税前)"),
            "record_date": ColumnDef("CHAR(8)", nullable=True, comment="股权登记日"),
            "ex_date": ColumnDef("CHAR(8)", nullable=True, comment="除权除息日"),
            "pay_date": ColumnDef("CHAR(8)", nullable=True, comment="派息日"),
            "div_listdate": ColumnDef("CHAR(8)", nullable=True, comment="红股上市日"),
            "imp_ann_date": ColumnDef("CHAR(8)", nullable=True, comment="实施公告日"),
            "base_date": ColumnDef("CHAR(8)", nullable=True, comment="基准日"),
            "base_share": ColumnDef("DOUBLE", nullable=True, comment="基准股本(万)"),
        },
        composite_indexes=[
            ("ann_date",),
            ("ann_date", "ts_code"),
            ("end_date",),
            ("end_date", "ts_code"),
            ("record_date",),
            ("record_date", "ts_code"),
            ("ex_date",),
            ("ex_date", "ts_code"),
            ("imp_ann_date",),
            ("imp_ann_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "dividend",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
