from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StockCompanyFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=112
    上市公司基本信息, 120积分
        获取上市公司基础信息, 单次提取4500条, 可以根据交易所分批提取
    API params:
        ts_code: 股票代码
        exchange: 交易所代码, SSE上交所 SZSE深交所 BSE北交所
    """
    fields = [
        "ts_code",  # 股票代码
        "com_name",  # 公司全称
        "com_id",  # 统一社会信用代码
        "exchange",  # 交易所代码
        "chairman",  # 法人代表
        "manager",  # 总经理
        "secretary",  # 董秘
        "reg_capital",  # 注册资本(万元)
        "setup_date",  # 注册日期
        "province",  # 所在省份
        "city",  # 所在城市
        "introduction",  # 公司介绍
        "website",  # 公司主页
        "email",  # 电子邮件
        "office",  # 办公室
        "employees",  # 员工人数
        "main_business",  # 主要业务及产品
        "business_scope",  # 经营范围
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "com_name": ColumnDef("VARCHAR(255)", nullable=True, comment="公司全称"),
            "com_id": ColumnDef("VARCHAR(255)", nullable=True, comment="统一社会信用代码"),
            "exchange": ColumnDef("VARCHAR(128)", nullable=True, comment="交易所代码"),
            "chairman": ColumnDef("VARCHAR(128)", nullable=True, comment="法人代表"),
            "manager": ColumnDef("VARCHAR(128)", nullable=True, comment="总经理"),
            "secretary": ColumnDef("VARCHAR(128)", nullable=True, comment="董秘"),
            "reg_capital": ColumnDef("DOUBLE", nullable=True, comment="注册资本(万元)"),
            "setup_date": ColumnDef("CHAR(8)", nullable=True, comment="注册日期"),
            "province": ColumnDef("VARCHAR(255)", nullable=True, comment="所在省份"),
            "city": ColumnDef("VARCHAR(255)", nullable=True, comment="所在城市"),
            "introduction": ColumnDef("TEXT", nullable=True, comment="公司介绍"),
            "website": ColumnDef("TEXT", nullable=True, comment="公司主页"),
            "email": ColumnDef("VARCHAR(128)", nullable=True, comment="电子邮件"),
            "office": ColumnDef("TEXT", nullable=True, comment="办公室"),
            "employees": ColumnDef("INT", nullable=True, comment="员工人数"),
            "main_business": ColumnDef("TEXT", nullable=True, comment="主要业务及产品"),
            "business_scope": ColumnDef("TEXT", nullable=True, comment="经营范围"),
        },
        composite_indexes=[
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs):
        frame = self.client.call("stock_company", 
            exchange="",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
