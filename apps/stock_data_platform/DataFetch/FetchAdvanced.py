"""
高级数据获取 (5000+积分)
TuShare API 文档: https://tushare.pro/document/2
"""

from .BaseClass import BaseDataFetch


class HKHoldFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=188
    沪深股通持股明细, 5000积分
        获取沪深港股通持股明细数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
        exchange: 类型(SH沪股通/SZ深股通)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "trade_date", "ts_code", "name",
            "vol",              # 持股数量(股)
            "ratio",            # 持股占比(%)
            "exchange"          # 类型(SH/SZ)
        ]
        return self.client.call(
            "hk_hold",
            fields=','.join(self.fields),
            **kwargs,
        )


class CyqPerfFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=293
    每日筹码及胜率, 5000积分
        获取每日筹码成本和胜率数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "his_low",          # 历史最低价
            "his_high",         # 历史最高价
            "cost_5pct",        # 5%成本价
            "cost_15pct",       # 15%成本价
            "cost_50pct",       # 50%成本价
            "cost_85pct",       # 85%成本价
            "cost_95pct",       # 95%成本价
            "weight_avg",       # 加权平均成本
            "winner_rate"       # 胜率(%)
        ]
        return self.client.call(
            "cyq_perf",
            fields=','.join(self.fields),
            **kwargs,
        )


class StkFactorFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=294
    股票技术面因子, 5000积分
        获取股票技术面因子数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "close",            # 收盘价
            "open", "high", "low",
            "vol", "amount",
            "macd_dif",         # MACD_DIF
            "macd_dea",         # MACD_DEA
            "macd",             # MACD
            "kdj_k",            # KDJ_K
            "kdj_d",            # KDJ_D
            "kdj_j",            # KDJ_J
            "rsi_6",            # RSI_6
            "rsi_12",           # RSI_12
            "rsi_24",           # RSI_24
            "boll_upper",       # BOLL上轨
            "boll_mid",         # BOLL中轨
            "boll_lower",       # BOLL下轨
            "cci"               # CCI指标
        ]
        return self.client.call(
            "stk_factor_pro",
            fields=','.join(self.fields),
            **kwargs,
        )


class StkAuctionFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=289
    股票开盘集合竞价数据, 5000积分
        获取股票每日开盘集合竞价数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "open",             # 开盘价
            "vol",              # 成交量(手)
            "amount",           # 成交额(千元)
        ]
        return self.client.call(
            "stk_auction",
            fields=','.join(self.fields),
            **kwargs,
        )


class BlockTradeFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=152
    大宗交易, 2000积分
        获取大宗交易数据
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date", "name",
            "price",            # 成交价
            "vol",              # 成交量(万股)
            "amount",           # 成交金额(万元)
            "buyer",            # 买方营业部
            "seller"            # 卖方营业部
        ]
        return self.client.call(
            "block_trade",
            fields=','.join(self.fields),
            **kwargs,
        )


class StkHolderNumberFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=166
    股东人数, 2000积分
        获取上市公司股东人数数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        end_date: 报告期
        start_date: 公告开始日期
        end_date: 公告结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "holder_num",       # 股东总数
            "holder_num_change",# 股东人数变化
            "holder_num_ratio", # 股东人数变化比例(%)
            "holder_num_pct"    # 较上期变动幅度(%)
        ]
        return self.client.call(
            "stk_holdernumber",
            fields=','.join(self.fields),
            **kwargs,
        )


class Top10HoldersFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=61
    前十大股东, 2000积分
        获取上市公司前十大股东数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        period: 报告期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "holder_name",      # 股东名称
            "hold_amount",      # 持股数量(股)
            "hold_ratio",       # 持股比例(%)
            "hold_change",      # 持股变化(股)
            "holder_type"       # 股东类型
        ]
        return self.client.call(
            "top10_holders",
            fields=','.join(self.fields),
            **kwargs,
        )


class Top10FloatHoldersFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=62
    前十大流通股东, 2000积分
        获取上市公司前十大流通股东数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        period: 报告期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "holder_name",      # 股东名称
            "hold_amount",      # 持股数量(股)
            "hold_ratio",       # 持股比例(%)
            "hold_change",      # 持股变化(股)
            "holder_type"       # 股东类型
        ]
        return self.client.call(
            "top10_floatholders",
            fields=','.join(self.fields),
            **kwargs,
        )


class DividendFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=103
    分红送股数据, 2000积分
        获取上市公司分红送股数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        record_date: 股权登记日期
        ex_date: 除权除息日
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "div_proc",         # 实施进度
            "stk_div",          # 每股送股比例
            "stk_bo_rate",      # 每股转增比例
            "stk_co_rate",      # 每股配股比例
            "cash_div",         # 每股分红(税后)
            "cash_div_tax",     # 每股分红(税前)
            "record_date",      # 股权登记日
            "ex_date",          # 除权除息日
            "pay_date"          # 派息日
        ]
        return self.client.call(
            "dividend",
            fields=','.join(self.fields),
            **kwargs,
        )


class ShareFloatFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=160
    限售股解禁, 3000积分
        获取限售股解禁数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        float_date: 解禁日期
        start_date: 解禁开始日期
        end_date: 解禁结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "float_date",
            "float_share",      # 解禁数量(万股)
            "float_ratio",      # 解禁比例(%)
            "holder_name",      # 股东名称
            "share_type"        # 股份类型
        ]
        return self.client.call(
            "share_float",
            fields=','.join(self.fields),
            **kwargs,
        )


class PledgeStatFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=110
    股权质押统计数据, 2000积分
        获取股权质押统计数据
    API params:
        ts_code: 股票代码
        end_date: 截止日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "end_date",
            "pledge_count",     # 质押次数
            "unrest_pledge",    # 无限售股质押数量(万股)
            "rest_pledge",      # 限售股份质押数量(万股)
            "total_share",      # 总股本(万股)
            "pledge_ratio"      # 质押比例(%)
        ]
        return self.client.call(
            "pledge_stat",
            fields=','.join(self.fields),
            **kwargs,
        )
