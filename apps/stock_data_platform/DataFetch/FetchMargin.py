"""
融资融券数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=58
"""

from .BaseClass import BaseDataFetch


class MarginFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=58
    融资融券每日交易汇总, 120积分
        获取融资融券每日交易汇总数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        exchange_id: 交易所(SSE上交所, SZSE深交所)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "exchange_id",
            "rzye",     # 融资余额(元)
            "rzmre",    # 融资买入额
            "rzche",    # 融资偿还额
            "rqye",     # 融券余额
            "rqmcl",    # 融券卖出量
            "rzrqye",   # 融资融券余额
            "rqyl"      # 融券余量
        ]
        return self.client.call(
            "margin",
            fields=','.join(self.fields),
            **kwargs,
        )


class MarginDetailFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=59
    融资融券交易明细, 120积分
        获取融资融券每日交易明细数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code", "name",
            "rzye",     # 融资余额(元)
            "rqye",     # 融券余额(元)
            "rzmre",    # 融资买入额(元)
            "rqyl",     # 融券余量(股)
            "rzche",    # 融资偿还额(元)
            "rqchl",    # 融券偿还量(股)
            "rqmcl",    # 融券卖出量(股)
            "rzrqye"    # 融资融券余额(元)
        ]
        return self.client.call(
            "margin_detail",
            fields=','.join(self.fields),
            **kwargs,
        )


class MarginTargetFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=60
    融资融券标的, 120积分
        获取融资融券标的股票列表
    API params:
        ts_code: 股票代码
        is_new: 是否最新(Y/N)
        mg_type: 标的类型(HT/SR, HT=航天证券, SR=上海融资融券)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "name",
            "mg_type",      # 标的类型
            "in_date",      # 纳入日期
            "out_date",     # 剔除日期
            "is_new"        # 是否最新
        ]
        return self.client.call(
            "margin_target",
            fields=','.join(self.fields),
            **kwargs,
        )
