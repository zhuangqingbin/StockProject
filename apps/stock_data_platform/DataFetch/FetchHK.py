"""
港股数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=191

注意: 港股日线行情(hk_daily)需要单独购买权限(1000元/年)，不是积分制度
      本模块只包含积分可用的接口
"""

from .BaseClass import BaseDataFetch


class HKBasicFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=189
    港股基础信息, 120积分
        获取港股基础信息
    API params:
        ts_code: 股票代码
        list_status: 上市状态(L/D/P)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "name", "fullname",
            "enname", "cn_spell",
            "market", "list_status",
            "list_date", "delist_date",
            "trade_unit", "isin", "curr_type"
        ]
        return self.client.call(
            "hk_basic",
            fields=','.join(self.fields),
            **kwargs,
        )


class GGTDailyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=196
    港股通每日成交统计(市场汇总), 2000积分
        获取港股通每日成交统计数据(市场整体,非单股)
    API params:
        trade_date: 交易日期(YYYYMMDD,支持多日逗号分隔)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date",
            "buy_amount",   # 买入成交金额(亿元)
            "buy_volume",   # 买入成交笔数(万笔)
            "sell_amount",  # 卖出成交金额(亿元)
            "sell_volume"   # 卖出成交笔数(万笔)
        ]
        return self.client.call(
            "ggt_daily",
            fields=','.join(self.fields),
            **kwargs,
        )
