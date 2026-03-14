"""
资金流向数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=170
"""

from .BaseClass import BaseDataFetch


class MoneyFlowFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=170
    个股资金流向, 2000积分
        获取沪深两市每日个股资金流向数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "buy_sm_vol", "buy_sm_amount",      # 小单买入
            "sell_sm_vol", "sell_sm_amount",    # 小单卖出
            "buy_md_vol", "buy_md_amount",      # 中单买入
            "sell_md_vol", "sell_md_amount",    # 中单卖出
            "buy_lg_vol", "buy_lg_amount",      # 大单买入
            "sell_lg_vol", "sell_lg_amount",    # 大单卖出
            "buy_elg_vol", "buy_elg_amount",    # 特大单买入
            "sell_elg_vol", "sell_elg_amount",  # 特大单卖出
            "net_mf_vol", "net_mf_amount"       # 净流入
        ]
        return self.client.call(
            "moneyflow",
            fields=','.join(self.fields),
            **kwargs,
        )


class MoneyFlowHSGTFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=47
    沪深港通资金流向, 120积分
        获取沪股通、深股通、港股通每日资金流向数据
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date",
            "ggt_ss",       # 港股通(沪)净流入
            "ggt_sz",       # 港股通(深)净流入
            "hgt",          # 沪股通净流入
            "sgt",          # 深股通净流入
            "north_money",  # 北向资金净流入
            "south_money"   # 南向资金净流入
        ]
        return self.client.call(
            "moneyflow_hsgt",
            fields=','.join(self.fields),
            **kwargs,
        )


class HSGTTop10Fetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=48
    沪深港通十大成交股, 120积分
        获取沪股通、深股通每日前十大成交详细数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
        market_type: 市场类型(1:沪股通, 2:深股通, 3:港股通-沪, 4:港股通-深)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code", "name",
            "close", "change", "rank",
            "market_type", "amount", "net_amount",
            "buy", "sell"
        ]
        return self.client.call(
            "hsgt_top10",
            fields=','.join(self.fields),
            **kwargs,
        )
