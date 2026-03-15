"""
涨跌停数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=198
"""

from .BaseClass import BaseDataFetch


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
