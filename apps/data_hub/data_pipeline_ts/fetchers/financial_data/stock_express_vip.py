from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class ExpressVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=46
    业绩快报(VIP), 5000积分
        按公告日期提取全市场业绩快报数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
    """
    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "end_date",  # 报告期
        "revenue",  # 营业收入(元)
        "operate_profit",  # 营业利润(元)
        "total_profit",  # 利润总额(元)
        "n_income",  # 净利润(元)
        "total_assets",  # 总资产(元)
        "total_hldr_eqy_exc_min_int",  # 股东权益合计(不含少数股东权益)(元)
        "diluted_eps",  # 每股收益(摊薄)(元)
        "diluted_roe",  # 净资产收益率(摊薄)(%)
        "yoy_net_profit",  # 去年同期修正后净利润
        "bps",  # 每股净资产
        "yoy_sales",  # 同比增长率:营业收入
        "yoy_op",  # 同比增长率:营业利润
        "yoy_tp",  # 同比增长率:利润总额
        "yoy_dedu_np",  # 同比增长率:归属母公司股东的净利润
        "yoy_eps",  # 同比增长率:基本每股收益
        "yoy_roe",  # 同比增减:加权平均净资产收益率
        "growth_assets",  # 比年初增长率:总资产
        "yoy_equity",  # 比年初增长率:归属母公司的股东权益
        "growth_bps",  # 比年初增长率:归属于母公司股东的每股净资产
        "or_last_year",  # 去年同期营业收入
        "op_last_year",  # 去年同期营业利润
        "tp_last_year",  # 去年同期利润总额
        "np_last_year",  # 去年同期净利润
        "eps_last_year",  # 去年同期每股收益
        "open_net_assets",  # 期初净资产
        "open_bps",  # 期初每股净资产
        "perf_summary",  # 业绩简要说明
        "is_audit",  # 是否审计： 1是 0否
        "remark",  # 备注
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "revenue": ColumnDef("DOUBLE", nullable=True, comment="营业收入(元)"),
            "operate_profit": ColumnDef("DOUBLE", nullable=True, comment="营业利润(元)"),
            "total_profit": ColumnDef("DOUBLE", nullable=True, comment="利润总额(元)"),
            "n_income": ColumnDef("DOUBLE", nullable=True, comment="净利润(元)"),
            "total_assets": ColumnDef("DOUBLE", nullable=True, comment="总资产(元)"),
            "total_hldr_eqy_exc_min_int": ColumnDef("DOUBLE", nullable=True, comment="股东权益合计(不含少数股东权益)(元)"),
            "diluted_eps": ColumnDef("DOUBLE", nullable=True, comment="每股收益(摊薄)(元)"),
            "diluted_roe": ColumnDef("DOUBLE", nullable=True, comment="净资产收益率(摊薄)(%)"),
            "yoy_net_profit": ColumnDef("DOUBLE", nullable=True, comment="去年同期修正后净利润"),
            "bps": ColumnDef("DOUBLE", nullable=True, comment="每股净资产"),
            "yoy_sales": ColumnDef("DOUBLE", nullable=True, comment="同比增长率:营业收入"),
            "yoy_op": ColumnDef("DOUBLE", nullable=True, comment="同比增长率:营业利润"),
            "yoy_tp": ColumnDef("DOUBLE", nullable=True, comment="同比增长率:利润总额"),
            "yoy_dedu_np": ColumnDef("DOUBLE", nullable=True, comment="同比增长率:归属母公司股东的净利润"),
            "yoy_eps": ColumnDef("DOUBLE", nullable=True, comment="同比增长率:基本每股收益"),
            "yoy_roe": ColumnDef("DOUBLE", nullable=True, comment="同比增减:加权平均净资产收益率"),
            "growth_assets": ColumnDef("DOUBLE", nullable=True, comment="比年初增长率:总资产"),
            "yoy_equity": ColumnDef("DOUBLE", nullable=True, comment="比年初增长率:归属母公司的股东权益"),
            "growth_bps": ColumnDef("DOUBLE", nullable=True, comment="比年初增长率:归属于母公司股东的每股净资产"),
            "or_last_year": ColumnDef("DOUBLE", nullable=True, comment="去年同期营业收入"),
            "op_last_year": ColumnDef("DOUBLE", nullable=True, comment="去年同期营业利润"),
            "tp_last_year": ColumnDef("DOUBLE", nullable=True, comment="去年同期利润总额"),
            "np_last_year": ColumnDef("DOUBLE", nullable=True, comment="去年同期净利润"),
            "eps_last_year": ColumnDef("DOUBLE", nullable=True, comment="去年同期每股收益"),
            "open_net_assets": ColumnDef("DOUBLE", nullable=True, comment="期初净资产"),
            "open_bps": ColumnDef("DOUBLE", nullable=True, comment="期初每股净资产"),
            "perf_summary": ColumnDef("TEXT", nullable=True, comment="业绩简要说明"),
            "is_audit": ColumnDef("TINYINT", nullable=True, comment="是否审计:1是, 0否"),
            "remark": ColumnDef("TEXT", nullable=True, comment="备注"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('end_date',),
            ('end_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("express_vip", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
