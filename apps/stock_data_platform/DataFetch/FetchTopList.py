"""
龙虎榜数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=106
"""

from .BaseClass import BaseDataFetch


class TopListFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=106
    龙虎榜每日明细, 300积分
        获取沪深两市每日龙虎榜明细数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code", "name",
            "close", "pct_change", "turnover_rate",
            "amount",           # 成交额
            "l_sell",           # 龙虎榜卖出额
            "l_buy",            # 龙虎榜买入额
            "l_amount",         # 龙虎榜成交额
            "net_amount",       # 龙虎榜净买入额
            "net_rate",         # 净买入占比
            "amount_rate",      # 龙虎榜成交额占比
            "float_values",     # 当日流通市值
            "reason"            # 上榜原因
        ]
        return self.client.call(
            "top_list",
            fields=','.join(self.fields),
            **kwargs,
        )


class TopInstFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=107
    龙虎榜机构交易明细, 300积分
        获取沪深两市每日龙虎榜机构交易明细数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code",
            "exalter",      # 营业部名称
            "buy",          # 买入额(万)
            "buy_rate",     # 买入占比
            "sell",         # 卖出额(万)
            "sell_rate",    # 卖出占比
            "net_buy",      # 净买入
            "side"          # 买卖方向(BUY/SELL)
        ]
        return self.client.call(
            "top_inst",
            fields=','.join(self.fields),
            **kwargs,
        )
