from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class FinaAuditFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=80
    财务审计意见, 500积分
        调度入口按公告日期触发, 内部遍历股票代码提取审计意见数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        start_date: 公告开始日期(YYYYMMDD)
        end_date: 公告结束日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
    Fetcher params:
        ann_date: 公告日期(YYYYMMDD)
        start_date: 公告开始日期(YYYYMMDD)
        end_date: 公告结束日期(YYYYMMDD)
        stock_codes: 可选股票代码列表, 未传时自动遍历全市场股票代码
    """

    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "end_date",  # 报告期
        "audit_result",  # 审计结果
        "audit_fees",  # 审计总费用（元）
        "audit_agency",  # 会计事务所
        "audit_sign",  # 签字会计师
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "audit_result": ColumnDef("VARCHAR(64)", nullable=True, comment="审计结果"),
            "audit_fees": ColumnDef("DOUBLE", nullable=True, comment="审计总费用(元)"),
            "audit_agency": ColumnDef("VARCHAR(128)", nullable=True, comment="会计事务所"),
            "audit_sign": ColumnDef("VARCHAR(128)", nullable=True, comment="签字会计师"),
        },
        composite_indexes=[
            ("ann_date",),
            ("ann_date", "ts_code"),
            ("end_date",),
            ("end_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        ann_date = str(kwargs.pop("ann_date", "")).strip()
        start_date = str(kwargs.get("start_date", "")).strip()
        end_date = str(kwargs.get("end_date", "")).strip()
        if not ann_date and not (start_date and end_date):
            raise ValueError("fina_audit fetches require ann_date or start_date/end_date")
        if "ts_code" in kwargs:
            raise ValueError("fina_audit fetches require stock_codes")
        stock_codes = kwargs.pop("stock_codes", None)
        request_kwargs = dict(kwargs)
        if ann_date:
            request_kwargs["ann_date"] = ann_date

        return self.fanout_by_stock_codes(
            stock_codes=stock_codes,
            stock_basic_statuses=("L",),  # 上市状态 L上市 D退市 P暂停上市
            columns=self.fields,
            fetch_one=lambda stock_code: self.client.call(
                "fina_audit",
                ts_code=stock_code,
                fields=",".join(self.fields),
                **request_kwargs,
            ),
        )
