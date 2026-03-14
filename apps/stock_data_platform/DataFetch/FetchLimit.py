"""
涨跌停数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=198
"""

from .BaseClass import BaseDataFetch


class LimitListFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=198
    每日涨跌停统计, 5000积分 (实际需要5000+积分)
        获取沪深两市每日涨跌停股票统计数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        limit_type: U涨停 D跌停 Z炸板
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code", "name",
            "close", "pct_chg",
            "amp",          # 振幅
            "fc_ratio",     # 封单金额/流通市值
            "fl_ratio",     # 封单手数/流通股本
            "fd_amount",    # 封单金额(万)
            "first_time",   # 首次涨跌停时间
            "last_time",    # 最后涨跌停时间
            "open_times",   # 打开次数
            "strth",        # 涨跌停强度
            "limit"         # U涨停/D跌停/Z炸板
        ]
        return self.client.call(
            "limit_list_d",
            fields=','.join(self.fields),
            **kwargs,
        )


class StkLimitFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=183
    每日涨跌停价格, 120积分
        获取每日涨跌停价格
    API params:
        ts_code: 股票代码(支持多个, 逗号分隔)
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code",
            "pre_close",    # 昨日收盘价
            "up_limit",     # 涨停价
            "down_limit"    # 跌停价
        ]
        return self.client.call(
            "stk_limit",
            fields=','.join(self.fields),
            **kwargs,
        )
