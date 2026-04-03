from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class CashflowVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=44
    现金流量表(VIP), 5000积分
        按公告日期提取每日增量现金流量表数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        f_ann_date: 实际公告日期(YYYYMMDD)
        start_date: 公告日开始日期(YYYYMMDD)
        end_date: 公告日结束日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
        report_type: 报告类型
        comp_type: 公司类型
        is_calc: 是否计算报表
    """
    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "f_ann_date",  # 实际公告日期
        "end_date",  # 报告期
        "comp_type",  # 公司类型(1一般工商业2银行3保险4证券)
        "report_type",  # 报表类型
        "end_type",  # 报告期类型
        "net_profit",  # 净利润
        "finan_exp",  # 财务费用
        "c_fr_sale_sg",  # 销售商品、提供劳务收到的现金
        "recp_tax_rends",  # 收到的税费返还
        "n_depos_incr_fi",  # 客户存款和同业存放款项净增加额
        "n_incr_loans_cb",  # 向中央银行借款净增加额
        "n_inc_borr_oth_fi",  # 向其他金融机构拆入资金净增加额
        "prem_fr_orig_contr",  # 收到原保险合同保费取得的现金
        "n_incr_insured_dep",  # 保户储金净增加额
        "n_reinsur_prem",  # 收到再保业务现金净额
        "n_incr_disp_tfa",  # 处置交易性金融资产净增加额
        "ifc_cash_incr",  # 收取利息和手续费净增加额
        "n_incr_disp_faas",  # 处置可供出售金融资产净增加额
        "n_incr_loans_oth_bank",  # 拆入资金净增加额
        "n_cap_incr_repur",  # 回购业务资金净增加额
        "c_fr_oth_operate_a",  # 收到其他与经营活动有关的现金
        "c_inf_fr_operate_a",  # 经营活动现金流入小计
        "c_paid_goods_s",  # 购买商品、接受劳务支付的现金
        "c_paid_to_for_empl",  # 支付给职工以及为职工支付的现金
        "c_paid_for_taxes",  # 支付的各项税费
        "n_incr_clt_loan_adv",  # 客户贷款及垫款净增加额
        "n_incr_dep_cbob",  # 存放央行和同业款项净增加额
        "c_pay_claims_orig_inco",  # 支付原保险合同赔付款项的现金
        "pay_handling_chrg",  # 支付手续费的现金
        "pay_comm_insur_plcy",  # 支付保单红利的现金
        "oth_cash_pay_oper_act",  # 支付其他与经营活动有关的现金
        "st_cash_out_act",  # 经营活动现金流出小计
        "n_cashflow_act",  # 经营活动产生的现金流量净额
        "oth_recp_ral_inv_act",  # 收到其他与投资活动有关的现金
        "c_disp_withdrwl_invest",  # 收回投资收到的现金
        "c_recp_return_invest",  # 取得投资收益收到的现金
        "n_recp_disp_fiolta",  # 处置固定资产、无形资产和其他长期资产收回的现金净额
        "n_recp_disp_sobu",  # 处置子公司及其他营业单位收到的现金净额
        "stot_inflows_inv_act",  # 投资活动现金流入小计
        "c_pay_acq_const_fiolta",  # 购建固定资产、无形资产和其他长期资产支付的现金
        "c_paid_invest",  # 投资支付的现金
        "n_disp_subs_oth_biz",  # 取得子公司及其他营业单位支付的现金净额
        "oth_pay_ral_inv_act",  # 支付其他与投资活动有关的现金
        "n_incr_pledge_loan",  # 质押贷款净增加额
        "stot_out_inv_act",  # 投资活动现金流出小计
        "n_cashflow_inv_act",  # 投资活动产生的现金流量净额
        "c_recp_borrow",  # 取得借款收到的现金
        "proc_issue_bonds",  # 发行债券收到的现金
        "oth_cash_recp_ral_fnc_act",  # 收到其他与筹资活动有关的现金
        "stot_cash_in_fnc_act",  # 筹资活动现金流入小计
        "free_cashflow",  # 企业自由现金流量
        "c_prepay_amt_borr",  # 偿还债务支付的现金
        "c_pay_dist_dpcp_int_exp",  # 分配股利、利润或偿付利息支付的现金
        "incl_dvd_profit_paid_sc_ms",  # 其中:子公司支付给少数股东的股利、利润
        "oth_cashpay_ral_fnc_act",  # 支付其他与筹资活动有关的现金
        "stot_cashout_fnc_act",  # 筹资活动现金流出小计
        "n_cash_flows_fnc_act",  # 筹资活动产生的现金流量净额
        "eff_fx_flu_cash",  # 汇率变动对现金的影响
        "n_incr_cash_cash_equ",  # 现金及现金等价物净增加额
        "c_cash_equ_beg_period",  # 期初现金及现金等价物余额
        "c_cash_equ_end_period",  # 期末现金及现金等价物余额
        "c_recp_cap_contrib",  # 吸收投资收到的现金
        "incl_cash_rec_saims",  # 其中:子公司吸收少数股东投资收到的现金
        "uncon_invest_loss",  # 未确认投资损失
        "prov_depr_assets",  # 加:资产减值准备
        "depr_fa_coga_dpba",  # 固定资产折旧、油气资产折耗、生产性生物资产折旧
        "amort_intang_assets",  # 无形资产摊销
        "lt_amort_deferred_exp",  # 长期待摊费用摊销
        "decr_deferred_exp",  # 待摊费用减少
        "incr_acc_exp",  # 预提费用增加
        "loss_disp_fiolta",  # 处置固定、无形资产和其他长期资产的损失
        "loss_scr_fa",  # 固定资产报废损失
        "loss_fv_chg",  # 公允价值变动损失
        "invest_loss",  # 投资损失
        "decr_def_inc_tax_assets",  # 递延所得税资产减少
        "incr_def_inc_tax_liab",  # 递延所得税负债增加
        "decr_inventories",  # 存货的减少
        "decr_oper_payable",  # 经营性应收项目的减少
        "incr_oper_payable",  # 经营性应付项目的增加
        "others",  # 其他
        "im_net_cashflow_oper_act",  # 经营活动产生的现金流量净额(间接法)
        "conv_debt_into_cap",  # 债务转为资本
        "conv_copbonds_due_within_1y",  # 一年内到期的可转换公司债券
        "fa_fnc_leases",  # 融资租入固定资产
        "im_n_incr_cash_equ",  # 现金及现金等价物净增加额(间接法)
        "net_dism_capital_add",  # 拆出资金净增加额
        "net_cash_rece_sec",  # 代理买卖证券收到的现金净额(元)
        "credit_impa_loss",  # 信用减值损失
        "use_right_asset_dep",  # 使用权资产折旧
        "oth_loss_asset",  # 其他资产减值损失
        "end_bal_cash",  # 现金的期末余额
        "beg_bal_cash",  # 减:现金的期初余额
        "end_bal_cash_equ",  # 加:现金等价物的期末余额
        "beg_bal_cash_equ",  # 减:现金等价物的期初余额
        "update_flag",  # 更新标志(1最新）
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "f_ann_date": ColumnDef("CHAR(8)", nullable=True, comment="实际公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "comp_type": ColumnDef("VARCHAR(8)", nullable=True, comment="公司类型(1一般工商业2银行3保险4证券)"),
            "report_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报表类型"),
            "end_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报告期类型"),
            "net_profit": ColumnDef("DOUBLE", nullable=True, comment="净利润"),
            "finan_exp": ColumnDef("DOUBLE", nullable=True, comment="财务费用"),
            "c_fr_sale_sg": ColumnDef("DOUBLE", nullable=True, comment="销售商品、提供劳务收到的现金"),
            "recp_tax_rends": ColumnDef("DOUBLE", nullable=True, comment="收到的税费返还"),
            "n_depos_incr_fi": ColumnDef("DOUBLE", nullable=True, comment="客户存款和同业存放款项净增加额"),
            "n_incr_loans_cb": ColumnDef("DOUBLE", nullable=True, comment="向中央银行借款净增加额"),
            "n_inc_borr_oth_fi": ColumnDef("DOUBLE", nullable=True, comment="向其他金融机构拆入资金净增加额"),
            "prem_fr_orig_contr": ColumnDef("DOUBLE", nullable=True, comment="收到原保险合同保费取得的现金"),
            "n_incr_insured_dep": ColumnDef("DOUBLE", nullable=True, comment="保户储金净增加额"),
            "n_reinsur_prem": ColumnDef("DOUBLE", nullable=True, comment="收到再保业务现金净额"),
            "n_incr_disp_tfa": ColumnDef("DOUBLE", nullable=True, comment="处置交易性金融资产净增加额"),
            "ifc_cash_incr": ColumnDef("DOUBLE", nullable=True, comment="收取利息和手续费净增加额"),
            "n_incr_disp_faas": ColumnDef("DOUBLE", nullable=True, comment="处置可供出售金融资产净增加额"),
            "n_incr_loans_oth_bank": ColumnDef("DOUBLE", nullable=True, comment="拆入资金净增加额"),
            "n_cap_incr_repur": ColumnDef("DOUBLE", nullable=True, comment="回购业务资金净增加额"),
            "c_fr_oth_operate_a": ColumnDef("DOUBLE", nullable=True, comment="收到其他与经营活动有关的现金"),
            "c_inf_fr_operate_a": ColumnDef("DOUBLE", nullable=True, comment="经营活动现金流入小计"),
            "c_paid_goods_s": ColumnDef("DOUBLE", nullable=True, comment="购买商品、接受劳务支付的现金"),
            "c_paid_to_for_empl": ColumnDef("DOUBLE", nullable=True, comment="支付给职工以及为职工支付的现金"),
            "c_paid_for_taxes": ColumnDef("DOUBLE", nullable=True, comment="支付的各项税费"),
            "n_incr_clt_loan_adv": ColumnDef("DOUBLE", nullable=True, comment="客户贷款及垫款净增加额"),
            "n_incr_dep_cbob": ColumnDef("DOUBLE", nullable=True, comment="存放央行和同业款项净增加额"),
            "c_pay_claims_orig_inco": ColumnDef("DOUBLE", nullable=True, comment="支付原保险合同赔付款项的现金"),
            "pay_handling_chrg": ColumnDef("DOUBLE", nullable=True, comment="支付手续费的现金"),
            "pay_comm_insur_plcy": ColumnDef("DOUBLE", nullable=True, comment="支付保单红利的现金"),
            "oth_cash_pay_oper_act": ColumnDef("DOUBLE", nullable=True, comment="支付其他与经营活动有关的现金"),
            "st_cash_out_act": ColumnDef("DOUBLE", nullable=True, comment="经营活动现金流出小计"),
            "n_cashflow_act": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额"),
            "oth_recp_ral_inv_act": ColumnDef("DOUBLE", nullable=True, comment="收到其他与投资活动有关的现金"),
            "c_disp_withdrwl_invest": ColumnDef("DOUBLE", nullable=True, comment="收回投资收到的现金"),
            "c_recp_return_invest": ColumnDef("DOUBLE", nullable=True, comment="取得投资收益收到的现金"),
            "n_recp_disp_fiolta": ColumnDef("DOUBLE", nullable=True, comment="处置固定资产、无形资产和其他长期资产收回的现金净额"),
            "n_recp_disp_sobu": ColumnDef("DOUBLE", nullable=True, comment="处置子公司及其他营业单位收到的现金净额"),
            "stot_inflows_inv_act": ColumnDef("DOUBLE", nullable=True, comment="投资活动现金流入小计"),
            "c_pay_acq_const_fiolta": ColumnDef("DOUBLE", nullable=True, comment="购建固定资产、无形资产和其他长期资产支付的现金"),
            "c_paid_invest": ColumnDef("DOUBLE", nullable=True, comment="投资支付的现金"),
            "n_disp_subs_oth_biz": ColumnDef("DOUBLE", nullable=True, comment="取得子公司及其他营业单位支付的现金净额"),
            "oth_pay_ral_inv_act": ColumnDef("DOUBLE", nullable=True, comment="支付其他与投资活动有关的现金"),
            "n_incr_pledge_loan": ColumnDef("DOUBLE", nullable=True, comment="质押贷款净增加额"),
            "stot_out_inv_act": ColumnDef("DOUBLE", nullable=True, comment="投资活动现金流出小计"),
            "n_cashflow_inv_act": ColumnDef("DOUBLE", nullable=True, comment="投资活动产生的现金流量净额"),
            "c_recp_borrow": ColumnDef("DOUBLE", nullable=True, comment="取得借款收到的现金"),
            "proc_issue_bonds": ColumnDef("DOUBLE", nullable=True, comment="发行债券收到的现金"),
            "oth_cash_recp_ral_fnc_act": ColumnDef("DOUBLE", nullable=True, comment="收到其他与筹资活动有关的现金"),
            "stot_cash_in_fnc_act": ColumnDef("DOUBLE", nullable=True, comment="筹资活动现金流入小计"),
            "free_cashflow": ColumnDef("DOUBLE", nullable=True, comment="企业自由现金流量"),
            "c_prepay_amt_borr": ColumnDef("DOUBLE", nullable=True, comment="偿还债务支付的现金"),
            "c_pay_dist_dpcp_int_exp": ColumnDef("DOUBLE", nullable=True, comment="分配股利、利润或偿付利息支付的现金"),
            "incl_dvd_profit_paid_sc_ms": ColumnDef("DOUBLE", nullable=True, comment="其中:子公司支付给少数股东的股利、利润"),
            "oth_cashpay_ral_fnc_act": ColumnDef("DOUBLE", nullable=True, comment="支付其他与筹资活动有关的现金"),
            "stot_cashout_fnc_act": ColumnDef("DOUBLE", nullable=True, comment="筹资活动现金流出小计"),
            "n_cash_flows_fnc_act": ColumnDef("DOUBLE", nullable=True, comment="筹资活动产生的现金流量净额"),
            "eff_fx_flu_cash": ColumnDef("DOUBLE", nullable=True, comment="汇率变动对现金的影响"),
            "n_incr_cash_cash_equ": ColumnDef("DOUBLE", nullable=True, comment="现金及现金等价物净增加额"),
            "c_cash_equ_beg_period": ColumnDef("DOUBLE", nullable=True, comment="期初现金及现金等价物余额"),
            "c_cash_equ_end_period": ColumnDef("DOUBLE", nullable=True, comment="期末现金及现金等价物余额"),
            "c_recp_cap_contrib": ColumnDef("DOUBLE", nullable=True, comment="吸收投资收到的现金"),
            "incl_cash_rec_saims": ColumnDef("DOUBLE", nullable=True, comment="其中:子公司吸收少数股东投资收到的现金"),
            "uncon_invest_loss": ColumnDef("DOUBLE", nullable=True, comment="未确认投资损失"),
            "prov_depr_assets": ColumnDef("DOUBLE", nullable=True, comment="加:资产减值准备"),
            "depr_fa_coga_dpba": ColumnDef("DOUBLE", nullable=True, comment="固定资产折旧、油气资产折耗、生产性生物资产折旧"),
            "amort_intang_assets": ColumnDef("DOUBLE", nullable=True, comment="无形资产摊销"),
            "lt_amort_deferred_exp": ColumnDef("DOUBLE", nullable=True, comment="长期待摊费用摊销"),
            "decr_deferred_exp": ColumnDef("DOUBLE", nullable=True, comment="待摊费用减少"),
            "incr_acc_exp": ColumnDef("DOUBLE", nullable=True, comment="预提费用增加"),
            "loss_disp_fiolta": ColumnDef("DOUBLE", nullable=True, comment="处置固定、无形资产和其他长期资产的损失"),
            "loss_scr_fa": ColumnDef("DOUBLE", nullable=True, comment="固定资产报废损失"),
            "loss_fv_chg": ColumnDef("DOUBLE", nullable=True, comment="公允价值变动损失"),
            "invest_loss": ColumnDef("DOUBLE", nullable=True, comment="投资损失"),
            "decr_def_inc_tax_assets": ColumnDef("DOUBLE", nullable=True, comment="递延所得税资产减少"),
            "incr_def_inc_tax_liab": ColumnDef("DOUBLE", nullable=True, comment="递延所得税负债增加"),
            "decr_inventories": ColumnDef("DOUBLE", nullable=True, comment="存货的减少"),
            "decr_oper_payable": ColumnDef("DOUBLE", nullable=True, comment="经营性应收项目的减少"),
            "incr_oper_payable": ColumnDef("DOUBLE", nullable=True, comment="经营性应付项目的增加"),
            "others": ColumnDef("DOUBLE", nullable=True, comment="其他"),
            "im_net_cashflow_oper_act": ColumnDef("DOUBLE", nullable=True, comment="经营活动产生的现金流量净额(间接法)"),
            "conv_debt_into_cap": ColumnDef("DOUBLE", nullable=True, comment="债务转为资本"),
            "conv_copbonds_due_within_1y": ColumnDef("DOUBLE", nullable=True, comment="一年内到期的可转换公司债券"),
            "fa_fnc_leases": ColumnDef("DOUBLE", nullable=True, comment="融资租入固定资产"),
            "im_n_incr_cash_equ": ColumnDef("DOUBLE", nullable=True, comment="现金及现金等价物净增加额(间接法)"),
            "net_dism_capital_add": ColumnDef("DOUBLE", nullable=True, comment="拆出资金净增加额"),
            "net_cash_rece_sec": ColumnDef("DOUBLE", nullable=True, comment="代理买卖证券收到的现金净额(元)"),
            "credit_impa_loss": ColumnDef("DOUBLE", nullable=True, comment="信用减值损失"),
            "use_right_asset_dep": ColumnDef("DOUBLE", nullable=True, comment="使用权资产折旧"),
            "oth_loss_asset": ColumnDef("DOUBLE", nullable=True, comment="其他资产减值损失"),
            "end_bal_cash": ColumnDef("DOUBLE", nullable=True, comment="现金的期末余额"),
            "beg_bal_cash": ColumnDef("DOUBLE", nullable=True, comment="减:现金的期初余额"),
            "end_bal_cash_equ": ColumnDef("DOUBLE", nullable=True, comment="加:现金等价物的期末余额"),
            "beg_bal_cash_equ": ColumnDef("DOUBLE", nullable=True, comment="减:现金等价物的期初余额"),
            "update_flag": ColumnDef("TINYINT", nullable=True, comment="更新标志(1最新）"),
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
            "cashflow_vip",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
