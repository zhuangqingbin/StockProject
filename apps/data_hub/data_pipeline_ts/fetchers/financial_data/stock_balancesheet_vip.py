from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class BalancesheetVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=36
    资产负债表(VIP), 5000积分
        按公告日期提取每日增量资产负债表数据。
    API params:
        ann_date: 公告日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
        report_type: 报表类型
        comp_type: 公司类型
    """
    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "f_ann_date",  # 实际公告日期
        "end_date",  # 报告期
        "report_type",  # 报表类型
        "comp_type",  # 公司类型(1一般工商业2银行3保险4证券)
        "end_type",  # 报告期类型
        "total_share",  # 期末总股本
        "cap_rese",  # 资本公积金
        "undistr_porfit",  # 未分配利润
        "surplus_rese",  # 盈余公积金
        "special_rese",  # 专项储备
        "money_cap",  # 货币资金
        "trad_asset",  # 交易性金融资产
        "notes_receiv",  # 应收票据
        "accounts_receiv",  # 应收账款
        "oth_receiv",  # 其他应收款
        "prepayment",  # 预付款项
        "div_receiv",  # 应收股利
        "int_receiv",  # 应收利息
        "inventories",  # 存货
        "amor_exp",  # 待摊费用
        "nca_within_1y",  # 一年内到期的非流动资产
        "sett_rsrv",  # 结算备付金
        "loanto_oth_bank_fi",  # 拆出资金
        "premium_receiv",  # 应收保费
        "reinsur_receiv",  # 应收分保账款
        "reinsur_res_receiv",  # 应收分保合同准备金
        "pur_resale_fa",  # 买入返售金融资产
        "oth_cur_assets",  # 其他流动资产
        "total_cur_assets",  # 流动资产合计
        "fa_avail_for_sale",  # 可供出售金融资产
        "htm_invest",  # 持有至到期投资
        "lt_eqt_invest",  # 长期股权投资
        "invest_real_estate",  # 投资性房地产
        "time_deposits",  # 定期存款
        "oth_assets",  # 其他资产
        "lt_rec",  # 长期应收款
        "fix_assets",  # 固定资产
        "cip",  # 在建工程
        "const_materials",  # 工程物资
        "fixed_assets_disp",  # 固定资产清理
        "produc_bio_assets",  # 生产性生物资产
        "oil_and_gas_assets",  # 油气资产
        "intan_assets",  # 无形资产
        "r_and_d",  # 研发支出
        "goodwill",  # 商誉
        "lt_amor_exp",  # 长期待摊费用
        "defer_tax_assets",  # 递延所得税资产
        "decr_in_disbur",  # 发放贷款及垫款
        "oth_nca",  # 其他非流动资产
        "total_nca",  # 非流动资产合计
        "cash_reser_cb",  # 现金及存放中央银行款项
        "depos_in_oth_bfi",  # 存放同业和其它金融机构款项
        "prec_metals",  # 贵金属
        "deriv_assets",  # 衍生金融资产
        "rr_reins_une_prem",  # 应收分保未到期责任准备金
        "rr_reins_outstd_cla",  # 应收分保未决赔款准备金
        "rr_reins_lins_liab",  # 应收分保寿险责任准备金
        "rr_reins_lthins_liab",  # 应收分保长期健康险责任准备金
        "refund_depos",  # 存出保证金
        "ph_pledge_loans",  # 保户质押贷款
        "refund_cap_depos",  # 存出资本保证金
        "indep_acct_assets",  # 独立账户资产
        "client_depos",  # 其中：客户资金存款
        "client_prov",  # 其中：客户备付金
        "transac_seat_fee",  # 其中:交易席位费
        "invest_as_receiv",  # 应收款项类投资
        "total_assets",  # 资产总计
        "lt_borr",  # 长期借款
        "st_borr",  # 短期借款
        "cb_borr",  # 向中央银行借款
        "depos_ib_deposits",  # 吸收存款及同业存放
        "loan_oth_bank",  # 拆入资金
        "trading_fl",  # 交易性金融负债
        "notes_payable",  # 应付票据
        "acct_payable",  # 应付账款
        "adv_receipts",  # 预收款项
        "sold_for_repur_fa",  # 卖出回购金融资产款
        "comm_payable",  # 应付手续费及佣金
        "payroll_payable",  # 应付职工薪酬
        "taxes_payable",  # 应交税费
        "int_payable",  # 应付利息
        "div_payable",  # 应付股利
        "oth_payable",  # 其他应付款
        "acc_exp",  # 预提费用
        "deferred_inc",  # 递延收益
        "st_bonds_payable",  # 应付短期债券
        "payable_to_reinsurer",  # 应付分保账款
        "rsrv_insur_cont",  # 保险合同准备金
        "acting_trading_sec",  # 代理买卖证券款
        "acting_uw_sec",  # 代理承销证券款
        "non_cur_liab_due_1y",  # 一年内到期的非流动负债
        "oth_cur_liab",  # 其他流动负债
        "total_cur_liab",  # 流动负债合计
        "bond_payable",  # 应付债券
        "lt_payable",  # 长期应付款
        "specific_payables",  # 专项应付款
        "estimated_liab",  # 预计负债
        "defer_tax_liab",  # 递延所得税负债
        "defer_inc_non_cur_liab",  # 递延收益-非流动负债
        "oth_ncl",  # 其他非流动负债
        "total_ncl",  # 非流动负债合计
        "depos_oth_bfi",  # 同业和其它金融机构存放款项
        "deriv_liab",  # 衍生金融负债
        "depos",  # 吸收存款
        "agency_bus_liab",  # 代理业务负债
        "oth_liab",  # 其他负债
        "prem_receiv_adva",  # 预收保费
        "depos_received",  # 存入保证金
        "ph_invest",  # 保户储金及投资款
        "reser_une_prem",  # 未到期责任准备金
        "reser_outstd_claims",  # 未决赔款准备金
        "reser_lins_liab",  # 寿险责任准备金
        "reser_lthins_liab",  # 长期健康险责任准备金
        "indept_acc_liab",  # 独立账户负债
        "pledge_borr",  # 其中:质押借款
        "indem_payable",  # 应付赔付款
        "policy_div_payable",  # 应付保单红利
        "total_liab",  # 负债合计
        "treasury_share",  # 减:库存股
        "ordin_risk_reser",  # 一般风险准备
        "forex_differ",  # 外币报表折算差额
        "invest_loss_unconf",  # 未确认的投资损失
        "minority_int",  # 少数股东权益
        "total_hldr_eqy_exc_min_int",  # 股东权益合计(不含少数股东权益)
        "total_hldr_eqy_inc_min_int",  # 股东权益合计(含少数股东权益)
        "total_liab_hldr_eqy",  # 负债及股东权益总计
        "lt_payroll_payable",  # 长期应付职工薪酬
        "oth_comp_income",  # 其他综合收益
        "oth_eqt_tools",  # 其他权益工具
        "oth_eqt_tools_p_shr",  # 其他权益工具(优先股)
        "lending_funds",  # 融出资金
        "acc_receivable",  # 应收款项
        "st_fin_payable",  # 应付短期融资款
        "payables",  # 应付款项
        "hfs_assets",  # 持有待售的资产
        "hfs_sales",  # 持有待售的负债
        "cost_fin_assets",  # 以摊余成本计量的金融资产
        "fair_value_fin_assets",  # 以公允价值计量且其变动计入其他综合收益的金融资产
        "cip_total",  # 在建工程(合计)(元)
        "oth_pay_total",  # 其他应付款(合计)(元)
        "long_pay_total",  # 长期应付款(合计)(元)
        "debt_invest",  # 债权投资(元)
        "oth_debt_invest",  # 其他债权投资(元)
        "oth_eq_invest",  # 其他权益工具投资(元)
        "oth_illiq_fin_assets",  # 其他非流动金融资产(元)
        "oth_eq_ppbond",  # 其他权益工具:永续债(元)
        "receiv_financing",  # 应收款项融资
        "use_right_assets",  # 使用权资产
        "lease_liab",  # 租赁负债
        "contract_assets",  # 合同资产
        "contract_liab",  # 合同负债
        "accounts_receiv_bill",  # 应收票据及应收账款
        "accounts_pay",  # 应付票据及应付账款
        "oth_rcv_total",  # 其他应收款(合计)（元）
        "fix_assets_total",  # 固定资产(合计)(元)
        "update_flag",  # 更新标识
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "f_ann_date": ColumnDef("CHAR(8)", nullable=True, comment="实际公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "report_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报表类型"),
            "comp_type": ColumnDef("VARCHAR(8)", nullable=True, comment="公司类型(1一般工商业2银行3保险4证券)"),
            "end_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报告期类型"),
            "total_share": ColumnDef("DOUBLE", nullable=True, comment="期末总股本"),
            "cap_rese": ColumnDef("DOUBLE", nullable=True, comment="资本公积金"),
            "undistr_porfit": ColumnDef("DOUBLE", nullable=True, comment="未分配利润"),
            "surplus_rese": ColumnDef("DOUBLE", nullable=True, comment="盈余公积金"),
            "special_rese": ColumnDef("DOUBLE", nullable=True, comment="专项储备"),
            "money_cap": ColumnDef("DOUBLE", nullable=True, comment="货币资金"),
            "trad_asset": ColumnDef("DOUBLE", nullable=True, comment="交易性金融资产"),
            "notes_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收票据"),
            "accounts_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收账款"),
            "oth_receiv": ColumnDef("DOUBLE", nullable=True, comment="其他应收款"),
            "prepayment": ColumnDef("DOUBLE", nullable=True, comment="预付款项"),
            "div_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收股利"),
            "int_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收利息"),
            "inventories": ColumnDef("DOUBLE", nullable=True, comment="存货"),
            "amor_exp": ColumnDef("DOUBLE", nullable=True, comment="待摊费用"),
            "nca_within_1y": ColumnDef("DOUBLE", nullable=True, comment="一年内到期的非流动资产"),
            "sett_rsrv": ColumnDef("DOUBLE", nullable=True, comment="结算备付金"),
            "loanto_oth_bank_fi": ColumnDef("DOUBLE", nullable=True, comment="拆出资金"),
            "premium_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收保费"),
            "reinsur_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收分保账款"),
            "reinsur_res_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收分保合同准备金"),
            "pur_resale_fa": ColumnDef("DOUBLE", nullable=True, comment="买入返售金融资产"),
            "oth_cur_assets": ColumnDef("DOUBLE", nullable=True, comment="其他流动资产"),
            "total_cur_assets": ColumnDef("DOUBLE", nullable=True, comment="流动资产合计"),
            "fa_avail_for_sale": ColumnDef("DOUBLE", nullable=True, comment="可供出售金融资产"),
            "htm_invest": ColumnDef("DOUBLE", nullable=True, comment="持有至到期投资"),
            "lt_eqt_invest": ColumnDef("DOUBLE", nullable=True, comment="长期股权投资"),
            "invest_real_estate": ColumnDef("DOUBLE", nullable=True, comment="投资性房地产"),
            "time_deposits": ColumnDef("DOUBLE", nullable=True, comment="定期存款"),
            "oth_assets": ColumnDef("DOUBLE", nullable=True, comment="其他资产"),
            "lt_rec": ColumnDef("DOUBLE", nullable=True, comment="长期应收款"),
            "fix_assets": ColumnDef("DOUBLE", nullable=True, comment="固定资产"),
            "cip": ColumnDef("DOUBLE", nullable=True, comment="在建工程"),
            "const_materials": ColumnDef("DOUBLE", nullable=True, comment="工程物资"),
            "fixed_assets_disp": ColumnDef("DOUBLE", nullable=True, comment="固定资产清理"),
            "produc_bio_assets": ColumnDef("DOUBLE", nullable=True, comment="生产性生物资产"),
            "oil_and_gas_assets": ColumnDef("DOUBLE", nullable=True, comment="油气资产"),
            "intan_assets": ColumnDef("DOUBLE", nullable=True, comment="无形资产"),
            "r_and_d": ColumnDef("DOUBLE", nullable=True, comment="研发支出"),
            "goodwill": ColumnDef("DOUBLE", nullable=True, comment="商誉"),
            "lt_amor_exp": ColumnDef("DOUBLE", nullable=True, comment="长期待摊费用"),
            "defer_tax_assets": ColumnDef("DOUBLE", nullable=True, comment="递延所得税资产"),
            "decr_in_disbur": ColumnDef("DOUBLE", nullable=True, comment="发放贷款及垫款"),
            "oth_nca": ColumnDef("DOUBLE", nullable=True, comment="其他非流动资产"),
            "total_nca": ColumnDef("DOUBLE", nullable=True, comment="非流动资产合计"),
            "cash_reser_cb": ColumnDef("DOUBLE", nullable=True, comment="现金及存放中央银行款项"),
            "depos_in_oth_bfi": ColumnDef("DOUBLE", nullable=True, comment="存放同业和其它金融机构款项"),
            "prec_metals": ColumnDef("DOUBLE", nullable=True, comment="贵金属"),
            "deriv_assets": ColumnDef("DOUBLE", nullable=True, comment="衍生金融资产"),
            "rr_reins_une_prem": ColumnDef("DOUBLE", nullable=True, comment="应收分保未到期责任准备金"),
            "rr_reins_outstd_cla": ColumnDef("DOUBLE", nullable=True, comment="应收分保未决赔款准备金"),
            "rr_reins_lins_liab": ColumnDef("DOUBLE", nullable=True, comment="应收分保寿险责任准备金"),
            "rr_reins_lthins_liab": ColumnDef("DOUBLE", nullable=True, comment="应收分保长期健康险责任准备金"),
            "refund_depos": ColumnDef("DOUBLE", nullable=True, comment="存出保证金"),
            "ph_pledge_loans": ColumnDef("DOUBLE", nullable=True, comment="保户质押贷款"),
            "refund_cap_depos": ColumnDef("DOUBLE", nullable=True, comment="存出资本保证金"),
            "indep_acct_assets": ColumnDef("DOUBLE", nullable=True, comment="独立账户资产"),
            "client_depos": ColumnDef("DOUBLE", nullable=True, comment="其中：客户资金存款"),
            "client_prov": ColumnDef("DOUBLE", nullable=True, comment="其中：客户备付金"),
            "transac_seat_fee": ColumnDef("DOUBLE", nullable=True, comment="其中:交易席位费"),
            "invest_as_receiv": ColumnDef("DOUBLE", nullable=True, comment="应收款项类投资"),
            "total_assets": ColumnDef("DOUBLE", nullable=True, comment="资产总计"),
            "lt_borr": ColumnDef("DOUBLE", nullable=True, comment="长期借款"),
            "st_borr": ColumnDef("DOUBLE", nullable=True, comment="短期借款"),
            "cb_borr": ColumnDef("DOUBLE", nullable=True, comment="向中央银行借款"),
            "depos_ib_deposits": ColumnDef("DOUBLE", nullable=True, comment="吸收存款及同业存放"),
            "loan_oth_bank": ColumnDef("DOUBLE", nullable=True, comment="拆入资金"),
            "trading_fl": ColumnDef("DOUBLE", nullable=True, comment="交易性金融负债"),
            "notes_payable": ColumnDef("DOUBLE", nullable=True, comment="应付票据"),
            "acct_payable": ColumnDef("DOUBLE", nullable=True, comment="应付账款"),
            "adv_receipts": ColumnDef("DOUBLE", nullable=True, comment="预收款项"),
            "sold_for_repur_fa": ColumnDef("DOUBLE", nullable=True, comment="卖出回购金融资产款"),
            "comm_payable": ColumnDef("DOUBLE", nullable=True, comment="应付手续费及佣金"),
            "payroll_payable": ColumnDef("DOUBLE", nullable=True, comment="应付职工薪酬"),
            "taxes_payable": ColumnDef("DOUBLE", nullable=True, comment="应交税费"),
            "int_payable": ColumnDef("DOUBLE", nullable=True, comment="应付利息"),
            "div_payable": ColumnDef("DOUBLE", nullable=True, comment="应付股利"),
            "oth_payable": ColumnDef("DOUBLE", nullable=True, comment="其他应付款"),
            "acc_exp": ColumnDef("DOUBLE", nullable=True, comment="预提费用"),
            "deferred_inc": ColumnDef("DOUBLE", nullable=True, comment="递延收益"),
            "st_bonds_payable": ColumnDef("DOUBLE", nullable=True, comment="应付短期债券"),
            "payable_to_reinsurer": ColumnDef("DOUBLE", nullable=True, comment="应付分保账款"),
            "rsrv_insur_cont": ColumnDef("DOUBLE", nullable=True, comment="保险合同准备金"),
            "acting_trading_sec": ColumnDef("DOUBLE", nullable=True, comment="代理买卖证券款"),
            "acting_uw_sec": ColumnDef("DOUBLE", nullable=True, comment="代理承销证券款"),
            "non_cur_liab_due_1y": ColumnDef("DOUBLE", nullable=True, comment="一年内到期的非流动负债"),
            "oth_cur_liab": ColumnDef("DOUBLE", nullable=True, comment="其他流动负债"),
            "total_cur_liab": ColumnDef("DOUBLE", nullable=True, comment="流动负债合计"),
            "bond_payable": ColumnDef("DOUBLE", nullable=True, comment="应付债券"),
            "lt_payable": ColumnDef("DOUBLE", nullable=True, comment="长期应付款"),
            "specific_payables": ColumnDef("DOUBLE", nullable=True, comment="专项应付款"),
            "estimated_liab": ColumnDef("DOUBLE", nullable=True, comment="预计负债"),
            "defer_tax_liab": ColumnDef("DOUBLE", nullable=True, comment="递延所得税负债"),
            "defer_inc_non_cur_liab": ColumnDef("DOUBLE", nullable=True, comment="递延收益-非流动负债"),
            "oth_ncl": ColumnDef("DOUBLE", nullable=True, comment="其他非流动负债"),
            "total_ncl": ColumnDef("DOUBLE", nullable=True, comment="非流动负债合计"),
            "depos_oth_bfi": ColumnDef("DOUBLE", nullable=True, comment="同业和其它金融机构存放款项"),
            "deriv_liab": ColumnDef("DOUBLE", nullable=True, comment="衍生金融负债"),
            "depos": ColumnDef("DOUBLE", nullable=True, comment="吸收存款"),
            "agency_bus_liab": ColumnDef("DOUBLE", nullable=True, comment="代理业务负债"),
            "oth_liab": ColumnDef("DOUBLE", nullable=True, comment="其他负债"),
            "prem_receiv_adva": ColumnDef("DOUBLE", nullable=True, comment="预收保费"),
            "depos_received": ColumnDef("DOUBLE", nullable=True, comment="存入保证金"),
            "ph_invest": ColumnDef("DOUBLE", nullable=True, comment="保户储金及投资款"),
            "reser_une_prem": ColumnDef("DOUBLE", nullable=True, comment="未到期责任准备金"),
            "reser_outstd_claims": ColumnDef("DOUBLE", nullable=True, comment="未决赔款准备金"),
            "reser_lins_liab": ColumnDef("DOUBLE", nullable=True, comment="寿险责任准备金"),
            "reser_lthins_liab": ColumnDef("DOUBLE", nullable=True, comment="长期健康险责任准备金"),
            "indept_acc_liab": ColumnDef("DOUBLE", nullable=True, comment="独立账户负债"),
            "pledge_borr": ColumnDef("DOUBLE", nullable=True, comment="其中:质押借款"),
            "indem_payable": ColumnDef("DOUBLE", nullable=True, comment="应付赔付款"),
            "policy_div_payable": ColumnDef("DOUBLE", nullable=True, comment="应付保单红利"),
            "total_liab": ColumnDef("DOUBLE", nullable=True, comment="负债合计"),
            "treasury_share": ColumnDef("DOUBLE", nullable=True, comment="减:库存股"),
            "ordin_risk_reser": ColumnDef("DOUBLE", nullable=True, comment="一般风险准备"),
            "forex_differ": ColumnDef("DOUBLE", nullable=True, comment="外币报表折算差额"),
            "invest_loss_unconf": ColumnDef("DOUBLE", nullable=True, comment="未确认的投资损失"),
            "minority_int": ColumnDef("DOUBLE", nullable=True, comment="少数股东权益"),
            "total_hldr_eqy_exc_min_int": ColumnDef("DOUBLE", nullable=True, comment="股东权益合计(不含少数股东权益)"),
            "total_hldr_eqy_inc_min_int": ColumnDef("DOUBLE", nullable=True, comment="股东权益合计(含少数股东权益)"),
            "total_liab_hldr_eqy": ColumnDef("DOUBLE", nullable=True, comment="负债及股东权益总计"),
            "lt_payroll_payable": ColumnDef("DOUBLE", nullable=True, comment="长期应付职工薪酬"),
            "oth_comp_income": ColumnDef("DOUBLE", nullable=True, comment="其他综合收益"),
            "oth_eqt_tools": ColumnDef("DOUBLE", nullable=True, comment="其他权益工具"),
            "oth_eqt_tools_p_shr": ColumnDef("DOUBLE", nullable=True, comment="其他权益工具(优先股)"),
            "lending_funds": ColumnDef("DOUBLE", nullable=True, comment="融出资金"),
            "acc_receivable": ColumnDef("DOUBLE", nullable=True, comment="应收款项"),
            "st_fin_payable": ColumnDef("DOUBLE", nullable=True, comment="应付短期融资款"),
            "payables": ColumnDef("DOUBLE", nullable=True, comment="应付款项"),
            "hfs_assets": ColumnDef("DOUBLE", nullable=True, comment="持有待售的资产"),
            "hfs_sales": ColumnDef("DOUBLE", nullable=True, comment="持有待售的负债"),
            "cost_fin_assets": ColumnDef("DOUBLE", nullable=True, comment="以摊余成本计量的金融资产"),
            "fair_value_fin_assets": ColumnDef("DOUBLE", nullable=True, comment="以公允价值计量且其变动计入其他综合收益的金融资产"),
            "cip_total": ColumnDef("DOUBLE", nullable=True, comment="在建工程(合计)(元)"),
            "oth_pay_total": ColumnDef("DOUBLE", nullable=True, comment="其他应付款(合计)(元)"),
            "long_pay_total": ColumnDef("DOUBLE", nullable=True, comment="长期应付款(合计)(元)"),
            "debt_invest": ColumnDef("DOUBLE", nullable=True, comment="债权投资(元)"),
            "oth_debt_invest": ColumnDef("DOUBLE", nullable=True, comment="其他债权投资(元)"),
            "oth_eq_invest": ColumnDef("DOUBLE", nullable=True, comment="其他权益工具投资(元)"),
            "oth_illiq_fin_assets": ColumnDef("DOUBLE", nullable=True, comment="其他非流动金融资产(元)"),
            "oth_eq_ppbond": ColumnDef("DOUBLE", nullable=True, comment="其他权益工具:永续债(元)"),
            "receiv_financing": ColumnDef("DOUBLE", nullable=True, comment="应收款项融资"),
            "use_right_assets": ColumnDef("DOUBLE", nullable=True, comment="使用权资产"),
            "lease_liab": ColumnDef("DOUBLE", nullable=True, comment="租赁负债"),
            "contract_assets": ColumnDef("DOUBLE", nullable=True, comment="合同资产"),
            "contract_liab": ColumnDef("DOUBLE", nullable=True, comment="合同负债"),
            "accounts_receiv_bill": ColumnDef("DOUBLE", nullable=True, comment="应收票据及应收账款"),
            "accounts_pay": ColumnDef("DOUBLE", nullable=True, comment="应付票据及应付账款"),
            "oth_rcv_total": ColumnDef("DOUBLE", nullable=True, comment="其他应收款(合计)（元）"),
            "fix_assets_total": ColumnDef("DOUBLE", nullable=True, comment="固定资产(合计)(元)"),
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
            "balancesheet_vip",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
