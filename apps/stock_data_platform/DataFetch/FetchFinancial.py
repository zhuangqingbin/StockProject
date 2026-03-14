"""
财务数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=33
"""

from .BaseClass import BaseDataFetch


class IncomeFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=33
    利润表, 2000积分
        获取上市公司利润表数据
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期(YYYYMMDD, 如20181231)
        report_type: 报告类型(1合并报表, 2单季度, 3调整后合并报表, 4调整后单季度)
        comp_type: 公司类型(1一般公司, 2银行, 3保险, 4证券)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "basic_eps",        # 基本每股收益
            "diluted_eps",      # 稀释每股收益
            "total_revenue",    # 营业总收入
            "revenue",          # 营业收入
            "total_cogs",       # 营业总成本
            "operate_profit",   # 营业利润
            "total_profit",     # 利润总额
            "n_income",         # 净利润
            "n_income_attr_p",  # 归母净利润
            "ebit",             # 息税前利润
            "ebitda"            # 息税折旧摊销前利润
        ]
        return self.client.call(
            "income",
            fields=','.join(self.fields),
            **kwargs,
        )


class IncomeVipFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=265
    利润表(VIP高积分版), 5000积分
        获取上市公司利润表数据(全市场全历史)
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期(YYYYMMDD)
        report_type: 报告类型
        comp_type: 公司类型
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "basic_eps", "diluted_eps",
            "total_revenue", "revenue",
            "total_cogs", "operate_profit",
            "total_profit", "n_income",
            "n_income_attr_p"
        ]
        return self.client.call(
            "income_vip",
            fields=','.join(self.fields),
            **kwargs,
        )


class BalanceSheetFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=36
    资产负债表, 2000积分
        获取上市公司资产负债表数据(需要ts_code)
    API params:
        ts_code: 股票代码(必填)
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期
        report_type: 报告类型
        comp_type: 公司类型
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "total_assets",         # 总资产
            "total_liab",           # 总负债
            "total_hldr_eqy_exc_min_int",  # 股东权益合计(不含少数股东权益)
            "total_hldr_eqy_inc_min_int",  # 股东权益合计(含少数股东权益)
            "total_cur_assets",     # 流动资产合计
            "total_nca",            # 非流动资产合计
            "total_cur_liab",       # 流动负债合计
            "total_ncl",            # 非流动负债合计
            "accounts_receiv",      # 应收账款
            "inventories",          # 存货
            "money_cap"             # 货币资金
        ]
        return self.client.call(
            "balancesheet",
            fields=','.join(self.fields),
            **kwargs,
        )


class BalanceSheetVipFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=36
    资产负债表(VIP版), 5000积分
        获取上市公司资产负债表数据(支持period获取全市场)
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期(YYYYMMDD,如20181231)
        report_type: 报告类型
        comp_type: 公司类型
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "total_assets", "total_liab",
            "total_hldr_eqy_exc_min_int", "total_hldr_eqy_inc_min_int",
            "total_cur_assets", "total_nca",
            "total_cur_liab", "total_ncl",
            "accounts_receiv", "inventories", "money_cap"
        ]
        return self.client.call(
            "balancesheet_vip",
            fields=','.join(self.fields),
            **kwargs,
        )


class CashFlowFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=44
    现金流量表, 2000积分
        获取上市公司现金流量表数据(需要ts_code)
    API params:
        ts_code: 股票代码(必填)
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期
        report_type: 报告类型
        comp_type: 公司类型
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "net_profit",           # 净利润
            "n_cashflow_act",       # 经营活动产生的现金流量净额
            "n_cashflow_inv_act",   # 投资活动产生的现金流量净额
            "n_cash_flows_fnc_act", # 筹资活动产生的现金流量净额
            "c_cash_equ_end_period", # 期末现金及现金等价物余额
            "c_cash_equ_beg_period"  # 期初现金及现金等价物余额
        ]
        return self.client.call(
            "cashflow",
            fields=','.join(self.fields),
            **kwargs,
        )


class CashFlowVipFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=44
    现金流量表(VIP版), 5000积分
        获取上市公司现金流量表数据(支持period获取全市场)
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期(YYYYMMDD)
        report_type: 报告类型
        comp_type: 公司类型
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "report_type", "comp_type",
            "net_profit", "n_cashflow_act",
            "n_cashflow_inv_act", "n_cash_flows_fnc_act",
            "c_cash_equ_end_period", "c_cash_equ_beg_period"
        ]
        return self.client.call(
            "cashflow_vip",
            fields=','.join(self.fields),
            **kwargs,
        )


class FinaIndicatorFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=79
    财务指标数据, 2000积分
        获取上市公司财务指标数据(需要ts_code)
    API params:
        ts_code: 股票代码(必填)
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "eps",              # 基本每股收益
            "dt_eps",           # 稀释每股收益
            "bps",              # 每股净资产
            "roe",              # 净资产收益率
            "roe_dt",           # 净资产收益率(扣非)
            "roa",              # 总资产净利率
            "current_ratio",    # 流动比率
            "quick_ratio",      # 速动比率
            "gross_margin",     # 毛利率
            "netprofit_margin", # 净利率
            "debt_to_assets",   # 资产负债率
            "op_yoy",           # 营业利润同比
            "profit_yoy"        # 净利润同比
        ]
        return self.client.call(
            "fina_indicator",
            fields=','.join(self.fields),
            **kwargs,
        )


class FinaIndicatorVipFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=79
    财务指标数据(VIP版), 5000积分
        获取上市公司财务指标数据(支持period获取全市场)
    API params:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期(YYYYMMDD)
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "ann_date", "end_date",
            "eps", "dt_eps", "bps",
            "roe", "roe_dt", "roa",
            "current_ratio", "quick_ratio",
            "gross_margin", "netprofit_margin",
            "debt_to_assets", "op_yoy", "profit_yoy"
        ]
        return self.client.call(
            "fina_indicator_vip",
            fields=','.join(self.fields),
            **kwargs,
        )
