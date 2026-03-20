from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class FinaIndicatorVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=16
    财务指标(VIP), 5000积分
        按公告日期提取每日增量核心财务指标数据。
    API params:
        ann_date: 公告日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
    """
    fields = [
        "ts_code",  # TS代码
        "ann_date",  # 公告日期
        "end_date",  # 报告期
        "eps",  # 基本每股收益
        "dt_eps",  # 稀释每股收益
        "total_revenue_ps",  # 每股营业总收入
        "revenue_ps",  # 每股营业收入
        "capital_rese_ps",  # 每股资本公积
        "surplus_rese_ps",  # 每股盈余公积
        "undist_profit_ps",  # 每股未分配利润
        "extra_item",  # 非经常性损益
        "profit_dedt",  # 扣除非经常性损益后的净利润（扣非净利润）
        "gross_margin",  # 毛利
        "current_ratio",  # 流动比率
        "quick_ratio",  # 速动比率
        "cash_ratio",  # 保守速动比率
        "invturn_days",  # 存货周转天数
        "arturn_days",  # 应收账款周转天数
        "inv_turn",  # 存货周转率
        "ar_turn",  # 应收账款周转率
        "ca_turn",  # 流动资产周转率
        "fa_turn",  # 固定资产周转率
        "assets_turn",  # 总资产周转率
        "op_income",  # 经营活动净收益
        "valuechange_income",  # 价值变动净收益
        "interst_income",  # 利息费用
        "daa",  # 折旧与摊销
        "ebit",  # 息税前利润
        "ebitda",  # 息税折旧摊销前利润
        "fcff",  # 企业自由现金流量
        "fcfe",  # 股权自由现金流量
        "current_exint",  # 无息流动负债
        "noncurrent_exint",  # 无息非流动负债
        "interestdebt",  # 带息债务
        "netdebt",  # 净债务
        "tangible_asset",  # 有形资产
        "working_capital",  # 营运资金
        "networking_capital",  # 营运流动资本
        "invest_capital",  # 全部投入资本
        "retained_earnings",  # 留存收益
        "diluted2_eps",  # 期末摊薄每股收益
        "bps",  # 每股净资产
        "ocfps",  # 每股经营活动产生的现金流量净额
        "retainedps",  # 每股留存收益
        "cfps",  # 每股现金流量净额
        "ebit_ps",  # 每股息税前利润
        "fcff_ps",  # 每股企业自由现金流量
        "fcfe_ps",  # 每股股东自由现金流量
        "netprofit_margin",  # 销售净利率
        "grossprofit_margin",  # 销售毛利率
        "cogs_of_sales",  # 销售成本率
        "expense_of_sales",  # 销售期间费用率
        "profit_to_gr",  # 净利润/营业总收入
        "saleexp_to_gr",  # 销售费用/营业总收入
        "adminexp_of_gr",  # 管理费用/营业总收入
        "finaexp_of_gr",  # 财务费用/营业总收入
        "impai_ttm",  # 资产减值损失/营业总收入
        "gc_of_gr",  # 营业总成本/营业总收入
        "op_of_gr",  # 营业利润/营业总收入
        "ebit_of_gr",  # 息税前利润/营业总收入
        "roe",  # 净资产收益率
        "roe_waa",  # 加权平均净资产收益率
        "roe_dt",  # 净资产收益率(扣除非经常损益)
        "roa",  # 总资产报酬率
        "npta",  # 总资产净利润
        "roic",  # 投入资本回报率
        "roe_yearly",  # 年化净资产收益率
        "roa2_yearly",  # 年化总资产报酬率
        "roe_avg",  # 平均净资产收益率(增发条件)
        "opincome_of_ebt",  # 经营活动净收益/利润总额
        "investincome_of_ebt",  # 价值变动净收益/利润总额
        "n_op_profit_of_ebt",  # 营业外收支净额/利润总额
        "tax_to_ebt",  # 所得税/利润总额
        "dtprofit_to_profit",  # 扣除非经常损益后的净利润/净利润
        "salescash_to_or",  # 销售商品提供劳务收到的现金/营业收入
        "ocf_to_or",  # 经营活动产生的现金流量净额/营业收入
        "ocf_to_opincome",  # 经营活动产生的现金流量净额/经营活动净收益
        "capitalized_to_da",  # 资本支出/折旧和摊销
        "debt_to_assets",  # 资产负债率
        "assets_to_eqt",  # 权益乘数
        "dp_assets_to_eqt",  # 权益乘数(杜邦分析)
        "ca_to_assets",  # 流动资产/总资产
        "nca_to_assets",  # 非流动资产/总资产
        "tbassets_to_totalassets",  # 有形资产/总资产
        "int_to_talcap",  # 带息债务/全部投入资本
        "eqt_to_talcapital",  # 归属于母公司的股东权益/全部投入资本
        "currentdebt_to_debt",  # 流动负债/负债合计
        "longdeb_to_debt",  # 非流动负债/负债合计
        "ocf_to_shortdebt",  # 经营活动产生的现金流量净额/流动负债
        "debt_to_eqt",  # 产权比率
        "eqt_to_debt",  # 归属于母公司的股东权益/负债合计
        "eqt_to_interestdebt",  # 归属于母公司的股东权益/带息债务
        "tangibleasset_to_debt",  # 有形资产/负债合计
        "tangasset_to_intdebt",  # 有形资产/带息债务
        "tangibleasset_to_netdebt",  # 有形资产/净债务
        "ocf_to_debt",  # 经营活动产生的现金流量净额/负债合计
        "ocf_to_interestdebt",  # 经营活动产生的现金流量净额/带息债务
        "ocf_to_netdebt",  # 经营活动产生的现金流量净额/净债务
        "ebit_to_interest",  # 已获利息倍数(EBIT/利息费用)
        "longdebt_to_workingcapital",  # 长期债务与营运资金比率
        "ebitda_to_debt",  # 息税折旧摊销前利润/负债合计
        "turn_days",  # 营业周期
        "roa_yearly",  # 年化总资产净利率
        "roa_dp",  # 总资产净利率(杜邦分析)
        "fixed_assets",  # 固定资产合计
        "profit_prefin_exp",  # 扣除财务费用前营业利润
        "non_op_profit",  # 非营业利润
        "op_to_ebt",  # 营业利润／利润总额
        "nop_to_ebt",  # 非营业利润／利润总额
        "ocf_to_profit",  # 经营活动产生的现金流量净额／营业利润
        "cash_to_liqdebt",  # 货币资金／流动负债
        "cash_to_liqdebt_withinterest",  # 货币资金／带息流动负债
        "op_to_liqdebt",  # 营业利润／流动负债
        "op_to_debt",  # 营业利润／负债合计
        "roic_yearly",  # 年化投入资本回报率
        "total_fa_trun",  # 固定资产合计周转率
        "profit_to_op",  # 利润总额／营业收入
        "q_opincome",  # 经营活动单季度净收益
        "q_investincome",  # 价值变动单季度净收益
        "q_dtprofit",  # 扣除非经常损益后的单季度净利润
        "q_eps",  # 每股收益(单季度)
        "q_netprofit_margin",  # 销售净利率(单季度)
        "q_gsprofit_margin",  # 销售毛利率(单季度)
        "q_exp_to_sales",  # 销售期间费用率(单季度)
        "q_profit_to_gr",  # 净利润／营业总收入(单季度)
        "q_saleexp_to_gr",  # 销售费用／营业总收入 (单季度)
        "q_adminexp_to_gr",  # 管理费用／营业总收入 (单季度)
        "q_finaexp_to_gr",  # 财务费用／营业总收入 (单季度)
        "q_impair_to_gr_ttm",  # 资产减值损失／营业总收入(单季度)
        "q_gc_to_gr",  # 营业总成本／营业总收入 (单季度)
        "q_op_to_gr",  # 营业利润／营业总收入(单季度)
        "q_roe",  # 净资产收益率(单季度)
        "q_dt_roe",  # 净资产单季度收益率(扣除非经常损益)
        "q_npta",  # 总资产净利润(单季度)
        "q_opincome_to_ebt",  # 经营活动净收益／利润总额(单季度)
        "q_investincome_to_ebt",  # 价值变动净收益／利润总额(单季度)
        "q_dtprofit_to_profit",  # 扣除非经常损益后的净利润／净利润(单季度)
        "q_salescash_to_or",  # 销售商品提供劳务收到的现金／营业收入(单季度)
        "q_ocf_to_sales",  # 经营活动产生的现金流量净额／营业收入(单季度)
        "q_ocf_to_or",  # 经营活动产生的现金流量净额／经营活动净收益(单季度)
        "basic_eps_yoy",  # 基本每股收益同比增长率(%)
        "dt_eps_yoy",  # 稀释每股收益同比增长率(%)
        "cfps_yoy",  # 每股经营活动产生的现金流量净额同比增长率(%)
        "op_yoy",  # 营业利润同比增长率(%)
        "ebt_yoy",  # 利润总额同比增长率(%)
        "netprofit_yoy",  # 归属母公司股东的净利润同比增长率(%)
        "dt_netprofit_yoy",  # 归属母公司股东的净利润-扣除非经常损益同比增长率(%)
        "ocf_yoy",  # 经营活动产生的现金流量净额同比增长率(%)
        "roe_yoy",  # 净资产收益率(摊薄)同比增长率(%)
        "bps_yoy",  # 每股净资产相对年初增长率(%)
        "assets_yoy",  # 资产总计相对年初增长率(%)
        "eqt_yoy",  # 归属母公司的股东权益相对年初增长率(%)
        "tr_yoy",  # 营业总收入同比增长率(%)
        "or_yoy",  # 营业收入同比增长率(%)
        "q_gr_yoy",  # 营业总收入同比增长率(%)(单季度)
        "q_gr_qoq",  # 营业总收入环比增长率(%)(单季度)
        "q_sales_yoy",  # 营业收入同比增长率(%)(单季度)
        "q_sales_qoq",  # 营业收入环比增长率(%)(单季度)
        "q_op_yoy",  # 营业利润同比增长率(%)(单季度)
        "q_op_qoq",  # 营业利润环比增长率(%)(单季度)
        "q_profit_yoy",  # 净利润同比增长率(%)(单季度)
        "q_profit_qoq",  # 净利润环比增长率(%)(单季度)
        "q_netprofit_yoy",  # 归属母公司股东的净利润同比增长率(%)(单季度)
        "q_netprofit_qoq",  # 归属母公司股东的净利润环比增长率(%)(单季度)
        "equity_yoy",  # 净资产同比增长率
        "rd_exp",  # 研发费用
        "update_flag",  # 更新标识
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "eps": ColumnDef("DOUBLE", nullable=True, comment="基本每股收益"),
            "dt_eps": ColumnDef("DOUBLE", nullable=True, comment="稀释每股收益"),
            "total_revenue_ps": ColumnDef("DOUBLE", nullable=True, comment="每股营业总收入"),
            "revenue_ps": ColumnDef("DOUBLE", nullable=True, comment="每股营业收入"),
            "capital_rese_ps": ColumnDef("DOUBLE", nullable=True, comment="每股资本公积"),
            "surplus_rese_ps": ColumnDef("DOUBLE", nullable=True, comment="每股盈余公积"),
            "undist_profit_ps": ColumnDef("DOUBLE", nullable=True, comment="每股未分配利润"),
            "extra_item": ColumnDef("DOUBLE", nullable=True, comment="非经常性损益"),
            "profit_dedt": ColumnDef("DOUBLE", nullable=True, comment="扣除非经常性损益后的净利润（扣非净利润）"),
            "gross_margin": ColumnDef("DOUBLE", nullable=True, comment="毛利"),
            "current_ratio": ColumnDef("DOUBLE", nullable=True, comment="流动比率"),
            "quick_ratio": ColumnDef("DOUBLE", nullable=True, comment="速动比率"),
            "cash_ratio": ColumnDef("DOUBLE", nullable=True, comment="保守速动比率"),
            "invturn_days": ColumnDef("DOUBLE", nullable=True, comment="存货周转天数"),
            "arturn_days": ColumnDef("DOUBLE", nullable=True, comment="应收账款周转天数"),
            "inv_turn": ColumnDef("DOUBLE", nullable=True, comment="存货周转率"),
            "ar_turn": ColumnDef("DOUBLE", nullable=True, comment="应收账款周转率"),
            "ca_turn": ColumnDef("DOUBLE", nullable=True, comment="流动资产周转率"),
            "fa_turn": ColumnDef("DOUBLE", nullable=True, comment="固定资产周转率"),
            "assets_turn": ColumnDef("DOUBLE", nullable=True, comment="总资产周转率"),
            "op_income": ColumnDef("DOUBLE", nullable=True, comment="经营活动净收益"),
            "valuechange_income": ColumnDef("DOUBLE", nullable=True, comment="价值变动净收益"),
            "interst_income": ColumnDef("DOUBLE", nullable=True, comment="利息费用"),
            "daa": ColumnDef("DOUBLE", nullable=True, comment="折旧与摊销"),
            "ebit": ColumnDef("DOUBLE", nullable=True, comment="息税前利润"),
            "ebitda": ColumnDef("DOUBLE", nullable=True, comment="息税折旧摊销前利润"),
            "fcff": ColumnDef("DOUBLE", nullable=True, comment="企业自由现金流量"),
            "fcfe": ColumnDef("DOUBLE", nullable=True, comment="股权自由现金流量"),
            "current_exint": ColumnDef("DOUBLE", nullable=True, comment="无息流动负债"),
            "noncurrent_exint": ColumnDef("DOUBLE", nullable=True, comment="无息非流动负债"),
            "interestdebt": ColumnDef("DOUBLE", nullable=True, comment="带息债务"),
            "netdebt": ColumnDef("DOUBLE", nullable=True, comment="净债务"),
            "tangible_asset": ColumnDef("DOUBLE", nullable=True, comment="有形资产"),
            "working_capital": ColumnDef("DOUBLE", nullable=True, comment="营运资金"),
            "networking_capital": ColumnDef("DOUBLE", nullable=True, comment="营运流动资本"),
            "invest_capital": ColumnDef("DOUBLE", nullable=True, comment="全部投入资本"),
            "retained_earnings": ColumnDef("DOUBLE", nullable=True, comment="留存收益"),
            "diluted2_eps": ColumnDef("DOUBLE", nullable=True, comment="期末摊薄每股收益"),
            "bps": ColumnDef("DOUBLE", nullable=True, comment="每股净资产"),
            "ocfps": ColumnDef("DOUBLE", nullable=True, comment="每股经营活动产生的现金流量净额"),
            "retainedps": ColumnDef("DOUBLE", nullable=True, comment="每股留存收益"),
            "cfps": ColumnDef("DOUBLE", nullable=True, comment="每股现金流量净额"),
            "ebit_ps": ColumnDef("DOUBLE", nullable=True, comment="每股息税前利润"),
            "fcff_ps": ColumnDef("DOUBLE", nullable=True, comment="每股企业自由现金流量"),
            "fcfe_ps": ColumnDef("DOUBLE", nullable=True, comment="每股股东自由现金流量"),
            "netprofit_margin": ColumnDef("DOUBLE", nullable=True, comment="销售净利率"),
            "grossprofit_margin": ColumnDef("DOUBLE", nullable=True, comment="销售毛利率"),
            "cogs_of_sales": ColumnDef("DOUBLE", nullable=True, comment="销售成本率"),
            "expense_of_sales": ColumnDef("DOUBLE", nullable=True, comment="销售期间费用率"),
            "profit_to_gr": ColumnDef("DOUBLE", nullable=True, comment="净利润/营业总收入"),
            "saleexp_to_gr": ColumnDef("DOUBLE", nullable=True, comment="销售费用/营业总收入"),
            "adminexp_of_gr": ColumnDef("DOUBLE", nullable=True, comment="管理费用/营业总收入"),
            "finaexp_of_gr": ColumnDef("DOUBLE", nullable=True, comment="财务费用/营业总收入"),
            "impai_ttm": ColumnDef("DOUBLE", nullable=True, comment="资产减值损失/营业总收入"),
            "gc_of_gr": ColumnDef("DOUBLE", nullable=True, comment="营业总成本/营业总收入"),
            "op_of_gr": ColumnDef("DOUBLE", nullable=True, comment="营业利润/营业总收入"),
            "ebit_of_gr": ColumnDef("DOUBLE", nullable=True, comment="息税前利润/营业总收入"),
            "roe": ColumnDef("DOUBLE", nullable=True, comment="净资产收益率"),
            "roe_waa": ColumnDef("DOUBLE", nullable=True, comment="加权平均净资产收益率"),
            "roe_dt": ColumnDef("DOUBLE", nullable=True, comment="净资产收益率(扣除非经常损益)"),
            "roa": ColumnDef("DOUBLE", nullable=True, comment="总资产报酬率"),
            "npta": ColumnDef("DOUBLE", nullable=True, comment="总资产净利润"),
            "roic": ColumnDef("DOUBLE", nullable=True, comment="投入资本回报率"),
            "roe_yearly": ColumnDef("DOUBLE", nullable=True, comment="年化净资产收益率"),
            "roa2_yearly": ColumnDef("DOUBLE", nullable=True, comment="年化总资产报酬率"),
            "roe_avg": ColumnDef("DOUBLE", nullable=True, comment="平均净资产收益率(增发条件)"),
            "opincome_of_ebt": ColumnDef("DOUBLE", nullable=True, comment="经营活动净收益/利润总额"),
            "investincome_of_ebt": ColumnDef("DOUBLE", nullable=True, comment="价值变动净收益/利润总额"),
            "n_op_profit_of_ebt": ColumnDef("DOUBLE", nullable=True, comment="营业外收支净额/利润总额"),
            "tax_to_ebt": ColumnDef("DOUBLE", nullable=True, comment="所得税/利润总额"),
            "dtprofit_to_profit": ColumnDef("DOUBLE", nullable=True, comment="扣除非经常损益后的净利润/净利润"),
            "salescash_to_or": ColumnDef("DOUBLE", nullable=True, comment="销售商品提供劳务收到的现金/营业收入"),
            "ocf_to_or": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/营业收入"),
            "ocf_to_opincome": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/经营活动净收益"),
            "capitalized_to_da": ColumnDef("DOUBLE", nullable=True, comment="资本支出/折旧和摊销"),
            "debt_to_assets": ColumnDef("DOUBLE", nullable=True, comment="资产负债率"),
            "assets_to_eqt": ColumnDef("DOUBLE", nullable=True, comment="权益乘数"),
            "dp_assets_to_eqt": ColumnDef("DOUBLE", nullable=True, comment="权益乘数(杜邦分析)"),
            "ca_to_assets": ColumnDef("DOUBLE", nullable=True, comment="流动资产/总资产"),
            "nca_to_assets": ColumnDef("DOUBLE", nullable=True, comment="非流动资产/总资产"),
            "tbassets_to_totalassets": ColumnDef("DOUBLE", nullable=True, comment="有形资产/总资产"),
            "int_to_talcap": ColumnDef("DOUBLE", nullable=True, comment="带息债务/全部投入资本"),
            "eqt_to_talcapital": ColumnDef("DOUBLE", nullable=True, comment="归属于母公司的股东权益/全部投入资本"),
            "currentdebt_to_debt": ColumnDef("DOUBLE", nullable=True, comment="流动负债/负债合计"),
            "longdeb_to_debt": ColumnDef("DOUBLE", nullable=True, comment="非流动负债/负债合计"),
            "ocf_to_shortdebt": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/流动负债"),
            "debt_to_eqt": ColumnDef("DOUBLE", nullable=True, comment="产权比率"),
            "eqt_to_debt": ColumnDef("DOUBLE", nullable=True, comment="归属于母公司的股东权益/负债合计"),
            "eqt_to_interestdebt": ColumnDef("DOUBLE", nullable=True, comment="归属于母公司的股东权益/带息债务"),
            "tangibleasset_to_debt": ColumnDef("DOUBLE", nullable=True, comment="有形资产/负债合计"),
            "tangasset_to_intdebt": ColumnDef("DOUBLE", nullable=True, comment="有形资产/带息债务"),
            "tangibleasset_to_netdebt": ColumnDef("DOUBLE", nullable=True, comment="有形资产/净债务"),
            "ocf_to_debt": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/负债合计"),
            "ocf_to_interestdebt": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/带息债务"),
            "ocf_to_netdebt": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额/净债务"),
            "ebit_to_interest": ColumnDef("DOUBLE", nullable=True, comment="已获利息倍数(EBIT/利息费用)"),
            "longdebt_to_workingcapital": ColumnDef("DOUBLE", nullable=True, comment="长期债务与营运资金比率"),
            "ebitda_to_debt": ColumnDef("DOUBLE", nullable=True, comment="息税折旧摊销前利润/负债合计"),
            "turn_days": ColumnDef("DOUBLE", nullable=True, comment="营业周期"),
            "roa_yearly": ColumnDef("DOUBLE", nullable=True, comment="年化总资产净利率"),
            "roa_dp": ColumnDef("DOUBLE", nullable=True, comment="总资产净利率(杜邦分析)"),
            "fixed_assets": ColumnDef("DOUBLE", nullable=True, comment="固定资产合计"),
            "profit_prefin_exp": ColumnDef("DOUBLE", nullable=True, comment="扣除财务费用前营业利润"),
            "non_op_profit": ColumnDef("DOUBLE", nullable=True, comment="非营业利润"),
            "op_to_ebt": ColumnDef("DOUBLE", nullable=True, comment="营业利润／利润总额"),
            "nop_to_ebt": ColumnDef("DOUBLE", nullable=True, comment="非营业利润／利润总额"),
            "ocf_to_profit": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额／营业利润"),
            "cash_to_liqdebt": ColumnDef("DOUBLE", nullable=True, comment="货币资金／流动负债"),
            "cash_to_liqdebt_withinterest": ColumnDef("DOUBLE", nullable=True, comment="货币资金／带息流动负债"),
            "op_to_liqdebt": ColumnDef("DOUBLE", nullable=True, comment="营业利润／流动负债"),
            "op_to_debt": ColumnDef("DOUBLE", nullable=True, comment="营业利润／负债合计"),
            "roic_yearly": ColumnDef("DOUBLE", nullable=True, comment="年化投入资本回报率"),
            "total_fa_trun": ColumnDef("DOUBLE", nullable=True, comment="固定资产合计周转率"),
            "profit_to_op": ColumnDef("DOUBLE", nullable=True, comment="利润总额／营业收入"),
            "q_opincome": ColumnDef("DOUBLE", nullable=True, comment="经营活动单季度净收益"),
            "q_investincome": ColumnDef("DOUBLE", nullable=True, comment="价值变动单季度净收益"),
            "q_dtprofit": ColumnDef("DOUBLE", nullable=True, comment="扣除非经常损益后的单季度净利润"),
            "q_eps": ColumnDef("DOUBLE", nullable=True, comment="每股收益(单季度)"),
            "q_netprofit_margin": ColumnDef("DOUBLE", nullable=True, comment="销售净利率(单季度)"),
            "q_gsprofit_margin": ColumnDef("DOUBLE", nullable=True, comment="销售毛利率(单季度)"),
            "q_exp_to_sales": ColumnDef("DOUBLE", nullable=True, comment="销售期间费用率(单季度)"),
            "q_profit_to_gr": ColumnDef("DOUBLE", nullable=True, comment="净利润／营业总收入(单季度)"),
            "q_saleexp_to_gr": ColumnDef("DOUBLE", nullable=True, comment="销售费用／营业总收入 (单季度)"),
            "q_adminexp_to_gr": ColumnDef("DOUBLE", nullable=True, comment="管理费用／营业总收入 (单季度)"),
            "q_finaexp_to_gr": ColumnDef("DOUBLE", nullable=True, comment="财务费用／营业总收入 (单季度)"),
            "q_impair_to_gr_ttm": ColumnDef("DOUBLE", nullable=True, comment="资产减值损失／营业总收入(单季度)"),
            "q_gc_to_gr": ColumnDef("DOUBLE", nullable=True, comment="营业总成本／营业总收入 (单季度)"),
            "q_op_to_gr": ColumnDef("DOUBLE", nullable=True, comment="营业利润／营业总收入(单季度)"),
            "q_roe": ColumnDef("DOUBLE", nullable=True, comment="净资产收益率(单季度)"),
            "q_dt_roe": ColumnDef("DOUBLE", nullable=True, comment="净资产单季度收益率(扣除非经常损益)"),
            "q_npta": ColumnDef("DOUBLE", nullable=True, comment="总资产净利润(单季度)"),
            "q_opincome_to_ebt": ColumnDef("DOUBLE", nullable=True, comment="经营活动净收益／利润总额(单季度)"),
            "q_investincome_to_ebt": ColumnDef("DOUBLE", nullable=True, comment="价值变动净收益／利润总额(单季度)"),
            "q_dtprofit_to_profit": ColumnDef("DOUBLE", nullable=True, comment="扣除非经常损益后的净利润／净利润(单季度)"),
            "q_salescash_to_or": ColumnDef("DOUBLE", nullable=True, comment="销售商品提供劳务收到的现金／营业收入(单季度)"),
            "q_ocf_to_sales": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额／营业收入(单季度)"),
            "q_ocf_to_or": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额／经营活动净收益(单季度)"),
            "basic_eps_yoy": ColumnDef("DOUBLE", nullable=True, comment="基本每股收益同比增长率(%)"),
            "dt_eps_yoy": ColumnDef("DOUBLE", nullable=True, comment="稀释每股收益同比增长率(%)"),
            "cfps_yoy": ColumnDef("DOUBLE", nullable=True, comment="每股经营活动产生的现金流量净额同比增长率(%)"),
            "op_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业利润同比增长率(%)"),
            "ebt_yoy": ColumnDef("DOUBLE", nullable=True, comment="利润总额同比增长率(%)"),
            "netprofit_yoy": ColumnDef("DOUBLE", nullable=True, comment="归属母公司股东的净利润同比增长率(%)"),
            "dt_netprofit_yoy": ColumnDef("DOUBLE", nullable=True, comment="归属母公司股东的净利润-扣除非经常损益同比增长率(%)"),
            "ocf_yoy": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额同比增长率(%)"),
            "roe_yoy": ColumnDef("DOUBLE", nullable=True, comment="净资产收益率(摊薄)同比增长率(%)"),
            "bps_yoy": ColumnDef("DOUBLE", nullable=True, comment="每股净资产相对年初增长率(%)"),
            "assets_yoy": ColumnDef("DOUBLE", nullable=True, comment="资产总计相对年初增长率(%)"),
            "eqt_yoy": ColumnDef("DOUBLE", nullable=True, comment="归属母公司的股东权益相对年初增长率(%)"),
            "tr_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业总收入同比增长率(%)"),
            "or_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业收入同比增长率(%)"),
            "q_gr_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业总收入同比增长率(%)(单季度)"),
            "q_gr_qoq": ColumnDef("DOUBLE", nullable=True, comment="营业总收入环比增长率(%)(单季度)"),
            "q_sales_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业收入同比增长率(%)(单季度)"),
            "q_sales_qoq": ColumnDef("DOUBLE", nullable=True, comment="营业收入环比增长率(%)(单季度)"),
            "q_op_yoy": ColumnDef("DOUBLE", nullable=True, comment="营业利润同比增长率(%)(单季度)"),
            "q_op_qoq": ColumnDef("DOUBLE", nullable=True, comment="营业利润环比增长率(%)(单季度)"),
            "q_profit_yoy": ColumnDef("DOUBLE", nullable=True, comment="净利润同比增长率(%)(单季度)"),
            "q_profit_qoq": ColumnDef("DOUBLE", nullable=True, comment="净利润环比增长率(%)(单季度)"),
            "q_netprofit_yoy": ColumnDef("DOUBLE", nullable=True, comment="归属母公司股东的净利润同比增长率(%)(单季度)"),
            "q_netprofit_qoq": ColumnDef("DOUBLE", nullable=True, comment="归属母公司股东的净利润环比增长率(%)(单季度)"),
            "equity_yoy": ColumnDef("DOUBLE", nullable=True, comment="净资产同比增长率"),
            "rd_exp": ColumnDef("DOUBLE", nullable=True, comment="研发费用"),
            "update_flag": ColumnDef("TINYINT", nullable=True, comment="更新标识"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('end_date',),
            ('end_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "fina_indicator_vip",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
