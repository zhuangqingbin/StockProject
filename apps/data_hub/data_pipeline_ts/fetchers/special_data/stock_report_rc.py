from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class ReportRCFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=292
    卖方盈利预测数据, 120积分试用 / 8000积分正式
        直接按传入参数抓取研报盈利预测数据。
    API params:
        report_date: 报告日期(YYYYMMDD)
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "ts_code",
        "name",
        "report_date",
        "report_title",
        "report_type",
        "classify",
        "org_name",
        "author_name",
        "quarter",
        "op_rt",
        "op_pr",
        "tp",
        "np",
        "eps",
        "pe",
        "rd",
        "roe",
        "ev_ebitda",
        "rating",
        "max_price",
        "min_price",
        "imp_dg",
        "create_time",
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "report_date": ColumnDef("CHAR(8)", nullable=True, comment="研报日期"),
            "report_title": ColumnDef("TEXT", nullable=True, comment="报告标题"),
            "report_type": ColumnDef("VARCHAR(32)", nullable=True, comment="报告类型"),
            "classify": ColumnDef("VARCHAR(32)", nullable=True, comment="报告分类"),
            "org_name": ColumnDef("VARCHAR(64)", nullable=True, comment="机构名称"),
            "author_name": ColumnDef("VARCHAR(64)", nullable=True, comment="作者"),
            "quarter": ColumnDef("VARCHAR(16)", nullable=True, comment="预测报告期"),
            "op_rt": ColumnDef("DOUBLE", nullable=True, comment="预测营业收入"),
            "op_pr": ColumnDef("DOUBLE", nullable=True, comment="预测营业利润"),
            "tp": ColumnDef("DOUBLE", nullable=True, comment="预测利润总额"),
            "np": ColumnDef("DOUBLE", nullable=True, comment="预测净利润"),
            "eps": ColumnDef("DOUBLE", nullable=True, comment="预测每股收益"),
            "pe": ColumnDef("DOUBLE", nullable=True, comment="预测市盈率"),
            "rd": ColumnDef("DOUBLE", nullable=True, comment="预测股息率"),
            "roe": ColumnDef("DOUBLE", nullable=True, comment="预测净资产收益率"),
            "ev_ebitda": ColumnDef("DOUBLE", nullable=True, comment="预测EV/EBITDA"),
            "rating": ColumnDef("VARCHAR(32)", nullable=True, comment="卖方评级"),
            "max_price": ColumnDef("DOUBLE", nullable=True, comment="预测最高目标价"),
            "min_price": ColumnDef("DOUBLE", nullable=True, comment="预测最低目标价"),
            "imp_dg": ColumnDef("VARCHAR(32)", nullable=True, comment="机构关注度"),
            "create_time": ColumnDef("DATETIME", nullable=True, comment="TS更新时间"),
        },
        composite_indexes=[
            ("report_date",),
            ("report_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "report_rc",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
