"""
指数数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=95
"""

from .BaseClass import BaseDataFetch


# 常用指数代码
MAIN_INDEX_CODES = [
    "000001.SH",  # 上证指数
    "399001.SZ",  # 深证成指
    "399006.SZ",  # 创业板指
    "000688.SH",  # 科创50
    "000300.SH",  # 沪深300
    "000905.SH",  # 中证500
    "000016.SH",  # 上证50
    "399005.SZ",  # 中小100
]


class IndexDailyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=95
    指数日线行情, 120积分
        获取指数每日行情
    API params:
        ts_code: 指数代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "close", "open", "high", "low",
            "pre_close", "change", "pct_chg",
            "vol", "amount"
        ]
        return self.client.call(
            "index_daily",
            fields=','.join(self.fields),
            **kwargs,
        )


class IndexBasicFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=94
    指数基本信息, 120积分
        获取指数基础信息
    API params:
        ts_code: 指数代码
        market: 市场(MSCI/CSI/SSE/SZSE/CICC/SW/OTH)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "name", "fullname",
            "market", "publisher",
            "index_type", "category",
            "base_date", "base_point",
            "list_date", "weight_rule",
            "desc", "exp_date"
        ]
        return self.client.call(
            "index_basic",
            fields=','.join(self.fields),
            **kwargs,
        )


class SWIndexDailyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=298
    申万行业指数日线行情, 2000积分
        获取申万行业指数每日行情
    API params:
        ts_code: 指数代码(如 801010.SI)
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date", "name",
            "open", "low", "high", "close",
            "change", "pct_change",
            "vol", "amount",
            "pe", "pb"
        ]
        return self.client.call(
            "sw_daily",
            fields=','.join(self.fields),
            **kwargs,
        )


class IndexClassifyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=181
    申万行业分类, 120积分
        获取申万行业分类信息
    API params:
        index_code: 指数代码
        level: 行业分级(L1/L2/L3)
        src: 指数来源(SW申万)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "index_code", "industry_name",
            "level", "industry_code",
            "is_pub", "parent_code"
        ]
        return self.client.call(
            "index_classify",
            fields=','.join(self.fields),
            **kwargs,
        )


class IndexMemberFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=182
    申万行业成分股, 120积分
        获取申万行业成分股
    API params:
        index_code: 指数代码
        ts_code: 股票代码
        is_new: 是否最新(Y是, N否, 默认Y)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "index_code", "index_name",
            "con_code", "con_name",
            "in_date", "out_date",
            "is_new"
        ]
        return self.client.call(
            "index_member",
            fields=','.join(self.fields),
            **kwargs,
        )
