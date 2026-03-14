"""
A股日线行情数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=27
"""

from .BaseClass import BaseDataFetch



class StockDailyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=27
    A股日线行情
        交易日每天15点-16点之间入库。本接口是未复权行情,停牌期间不提供数据
    API params:
        ts_code: 股票代码 (trade_date 二选一)
        trade_date: 交易日期(YYYYMMDD) (ts_code 二选一)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date", "open", "high", "low", "close", 
            "pre_close", "change", "pct_chg", "vol", "amount"
        ]
        return self.client.call(
            "daily",
            fields=','.join(self.fields),
            **kwargs,
        )


class StockDailyBasicFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=32
    每日指标, 2000积分
        获取全部股票每日重要的基本面指标, 6000, 可以根据交易所分批提取
    API params:
        ts_code: 股票代码 (trade_date 二选一)
        trade_date: 交易日期(YYYYMMDD) (ts_code 二选一)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    def read_data(self, **kwargs):
        self.fields =[
            "ts_code", "trade_date", "close", "turnover_rate", "turnover_rate_f", 
            "volume_ratio", "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio",
            "dv_ttm", "total_share", "float_share", "free_share", "total_mv", "circ_mv"
        ]
        return self.client.call(
            "daily_basic",
            fields=','.join(self.fields),
            **kwargs,
        )

