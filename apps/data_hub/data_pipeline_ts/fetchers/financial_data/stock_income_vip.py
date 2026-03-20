from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class IncomeVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=33
    利润表(VIP), 5000积分
        按公告日期提取每日增量利润表数据。
    API params:
        ann_date: 公告日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
        report_type: 报表类型
        comp_type: 公司类型
    """
    fields = [
        "ts_code",  # TS代码
        "ann_date",  # 公告日期
        "f_ann_date",  # 实际公告日期
        "end_date",  # 报告期
        "report_type",  # 报告类型 见底部表
        "comp_type",  # 公司类型(1一般工商业2银行3保险4证券)
        "end_type",  # 报告期类型
        "basic_eps",  # 基本每股收益
        "diluted_eps",  # 稀释每股收益
        "total_revenue",  # 营业总收入
        "revenue",  # 营业收入
        "int_income",  # 利息收入
        "prem_earned",  # 已赚保费
        "comm_income",  # 手续费及佣金收入
        "n_commis_income",  # 手续费及佣金净收入
        "n_oth_income",  # 其他经营净收益
        "n_oth_b_income",  # 加:其他业务净收益
        "prem_income",  # 保险业务收入
        "out_prem",  # 减:分出保费
        "une_prem_reser",  # 提取未到期责任准备金
        "reins_income",  # 其中:分保费收入
        "n_sec_tb_income",  # 代理买卖证券业务净收入
        "n_sec_uw_income",  # 证券承销业务净收入
        "n_asset_mg_income",  # 受托客户资产管理业务净收入
        "oth_b_income",  # 其他业务收入
        "fv_value_chg_gain",  # 加:公允价值变动净收益
        "invest_income",  # 加:投资净收益
        "ass_invest_income",  # 其中:对联营企业和合营企业的投资收益
        "forex_gain",  # 加:汇兑净收益
        "total_cogs",  # 营业总成本
        "oper_cost",  # 减:营业成本
        "int_exp",  # 减:利息支出
        "comm_exp",  # 减:手续费及佣金支出
        "biz_tax_surchg",  # 减:营业税金及附加
        "sell_exp",  # 减:销售费用
        "admin_exp",  # 减:管理费用
        "fin_exp",  # 减:财务费用
        "assets_impair_loss",  # 减:资产减值损失
        "prem_refund",  # 退保金
        "compens_payout",  # 赔付总支出
        "reser_insur_liab",  # 提取保险责任准备金
        "div_payt",  # 保户红利支出
        "reins_exp",  # 分保费用
        "oper_exp",  # 营业支出
        "compens_payout_refu",  # 减:摊回赔付支出
        "insur_reser_refu",  # 减:摊回保险责任准备金
        "reins_cost_refund",  # 减:摊回分保费用
        "other_bus_cost",  # 其他业务成本
        "operate_profit",  # 营业利润
        "non_oper_income",  # 加:营业外收入
        "non_oper_exp",  # 减:营业外支出
        "nca_disploss",  # 其中:减:非流动资产处置净损失
        "total_profit",  # 利润总额
        "income_tax",  # 所得税费用
        "n_income",  # 净利润(含少数股东损益)
        "n_income_attr_p",  # 净利润(不含少数股东损益)
        "minority_gain",  # 少数股东损益
        "oth_compr_income",  # 其他综合收益
        "t_compr_income",  # 综合收益总额
        "compr_inc_attr_p",  # 归属于母公司(或股东)的综合收益总额
        "compr_inc_attr_m_s",  # 归属于少数股东的综合收益总额
        "ebit",  # 息税前利润
        "ebitda",  # 息税折旧摊销前利润
        "insurance_exp",  # 保险业务支出
        "undist_profit",  # 年初未分配利润
        "distable_profit",  # 可分配利润
        "rd_exp",  # 研发费用
        "fin_exp_int_exp",  # 财务费用:利息费用
        "fin_exp_int_inc",  # 财务费用:利息收入
        "transfer_surplus_rese",  # 盈余公积转入
        "transfer_housing_imprest",  # 住房周转金转入
        "transfer_oth",  # 其他转入
        "adj_lossgain",  # 调整以前年度损益
        "withdra_legal_surplus",  # 提取法定盈余公积
        "withdra_legal_pubfund",  # 提取法定公益金
        "withdra_biz_devfund",  # 提取企业发展基金
        "withdra_rese_fund",  # 提取储备基金
        "withdra_oth_ersu",  # 提取任意盈余公积金
        "workers_welfare",  # 职工奖金福利
        "distr_profit_shrhder",  # 可供股东分配的利润
        "prfshare_payable_dvd",  # 应付优先股股利
        "comshare_payable_dvd",  # 应付普通股股利
        "capit_comstock_div",  # 转作股本的普通股股利
        "net_after_nr_lp_correct",  # 扣除非经常性损益后的净利润（更正前）
        "credit_impa_loss",  # 信用减值损失
        "net_expo_hedging_benefits",  # 净敞口套期收益
        "oth_impair_loss_assets",  # 其他资产减值损失
        "total_opcost",  # 营业总成本（二）
        "amodcost_fin_assets",  # 以摊余成本计量的金融资产终止确认收益
        "oth_income",  # 其他收益
        "asset_disp_income",  # 资产处置收益
        "continued_net_profit",  # 持续经营净利润
        "end_net_profit",  # 终止经营净利润
        "update_flag",  # 更新标识
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "f_ann_date": ColumnDef("CHAR(8)", nullable=True, comment="实际公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "report_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报告类型 见底部表"),
            "comp_type": ColumnDef("VARCHAR(8)", nullable=True, comment="公司类型(1一般工商业2银行3保险4证券)"),
            "end_type": ColumnDef("VARCHAR(8)", nullable=True, comment="报告期类型"),
            "basic_eps": ColumnDef("DOUBLE", nullable=True, comment="基本每股收益"),
            "diluted_eps": ColumnDef("DOUBLE", nullable=True, comment="稀释每股收益"),
            "total_revenue": ColumnDef("DOUBLE", nullable=True, comment="营业总收入"),
            "revenue": ColumnDef("DOUBLE", nullable=True, comment="营业收入"),
            "int_income": ColumnDef("DOUBLE", nullable=True, comment="利息收入"),
            "prem_earned": ColumnDef("DOUBLE", nullable=True, comment="已赚保费"),
            "comm_income": ColumnDef("DOUBLE", nullable=True, comment="手续费及佣金收入"),
            "n_commis_income": ColumnDef("DOUBLE", nullable=True, comment="手续费及佣金净收入"),
            "n_oth_income": ColumnDef("DOUBLE", nullable=True, comment="其他经营净收益"),
            "n_oth_b_income": ColumnDef("DOUBLE", nullable=True, comment="加:其他业务净收益"),
            "prem_income": ColumnDef("DOUBLE", nullable=True, comment="保险业务收入"),
            "out_prem": ColumnDef("DOUBLE", nullable=True, comment="减:分出保费"),
            "une_prem_reser": ColumnDef("DOUBLE", nullable=True, comment="提取未到期责任准备金"),
            "reins_income": ColumnDef("DOUBLE", nullable=True, comment="其中:分保费收入"),
            "n_sec_tb_income": ColumnDef("DOUBLE", nullable=True, comment="代理买卖证券业务净收入"),
            "n_sec_uw_income": ColumnDef("DOUBLE", nullable=True, comment="证券承销业务净收入"),
            "n_asset_mg_income": ColumnDef("DOUBLE", nullable=True, comment="受托客户资产管理业务净收入"),
            "oth_b_income": ColumnDef("DOUBLE", nullable=True, comment="其他业务收入"),
            "fv_value_chg_gain": ColumnDef("DOUBLE", nullable=True, comment="加:公允价值变动净收益"),
            "invest_income": ColumnDef("DOUBLE", nullable=True, comment="加:投资净收益"),
            "ass_invest_income": ColumnDef("DOUBLE", nullable=True, comment="其中:对联营企业和合营企业的投资收益"),
            "forex_gain": ColumnDef("DOUBLE", nullable=True, comment="加:汇兑净收益"),
            "total_cogs": ColumnDef("DOUBLE", nullable=True, comment="营业总成本"),
            "oper_cost": ColumnDef("DOUBLE", nullable=True, comment="减:营业成本"),
            "int_exp": ColumnDef("DOUBLE", nullable=True, comment="减:利息支出"),
            "comm_exp": ColumnDef("DOUBLE", nullable=True, comment="减:手续费及佣金支出"),
            "biz_tax_surchg": ColumnDef("DOUBLE", nullable=True, comment="减:营业税金及附加"),
            "sell_exp": ColumnDef("DOUBLE", nullable=True, comment="减:销售费用"),
            "admin_exp": ColumnDef("DOUBLE", nullable=True, comment="减:管理费用"),
            "fin_exp": ColumnDef("DOUBLE", nullable=True, comment="减:财务费用"),
            "assets_impair_loss": ColumnDef("DOUBLE", nullable=True, comment="减:资产减值损失"),
            "prem_refund": ColumnDef("DOUBLE", nullable=True, comment="退保金"),
            "compens_payout": ColumnDef("DOUBLE", nullable=True, comment="赔付总支出"),
            "reser_insur_liab": ColumnDef("DOUBLE", nullable=True, comment="提取保险责任准备金"),
            "div_payt": ColumnDef("DOUBLE", nullable=True, comment="保户红利支出"),
            "reins_exp": ColumnDef("DOUBLE", nullable=True, comment="分保费用"),
            "oper_exp": ColumnDef("DOUBLE", nullable=True, comment="营业支出"),
            "compens_payout_refu": ColumnDef("DOUBLE", nullable=True, comment="减:摊回赔付支出"),
            "insur_reser_refu": ColumnDef("DOUBLE", nullable=True, comment="减:摊回保险责任准备金"),
            "reins_cost_refund": ColumnDef("DOUBLE", nullable=True, comment="减:摊回分保费用"),
            "other_bus_cost": ColumnDef("DOUBLE", nullable=True, comment="其他业务成本"),
            "operate_profit": ColumnDef("DOUBLE", nullable=True, comment="营业利润"),
            "non_oper_income": ColumnDef("DOUBLE", nullable=True, comment="加:营业外收入"),
            "non_oper_exp": ColumnDef("DOUBLE", nullable=True, comment="减:营业外支出"),
            "nca_disploss": ColumnDef("DOUBLE", nullable=True, comment="其中:减:非流动资产处置净损失"),
            "total_profit": ColumnDef("DOUBLE", nullable=True, comment="利润总额"),
            "income_tax": ColumnDef("DOUBLE", nullable=True, comment="所得税费用"),
            "n_income": ColumnDef("DOUBLE", nullable=True, comment="净利润(含少数股东损益)"),
            "n_income_attr_p": ColumnDef("DOUBLE", nullable=True, comment="净利润(不含少数股东损益)"),
            "minority_gain": ColumnDef("DOUBLE", nullable=True, comment="少数股东损益"),
            "oth_compr_income": ColumnDef("DOUBLE", nullable=True, comment="其他综合收益"),
            "t_compr_income": ColumnDef("DOUBLE", nullable=True, comment="综合收益总额"),
            "compr_inc_attr_p": ColumnDef("DOUBLE", nullable=True, comment="归属于母公司(或股东)的综合收益总额"),
            "compr_inc_attr_m_s": ColumnDef("DOUBLE", nullable=True, comment="归属于少数股东的综合收益总额"),
            "ebit": ColumnDef("DOUBLE", nullable=True, comment="息税前利润"),
            "ebitda": ColumnDef("DOUBLE", nullable=True, comment="息税折旧摊销前利润"),
            "insurance_exp": ColumnDef("DOUBLE", nullable=True, comment="保险业务支出"),
            "undist_profit": ColumnDef("DOUBLE", nullable=True, comment="年初未分配利润"),
            "distable_profit": ColumnDef("DOUBLE", nullable=True, comment="可分配利润"),
            "rd_exp": ColumnDef("DOUBLE", nullable=True, comment="研发费用"),
            "fin_exp_int_exp": ColumnDef("DOUBLE", nullable=True, comment="财务费用:利息费用"),
            "fin_exp_int_inc": ColumnDef("DOUBLE", nullable=True, comment="财务费用:利息收入"),
            "transfer_surplus_rese": ColumnDef("DOUBLE", nullable=True, comment="盈余公积转入"),
            "transfer_housing_imprest": ColumnDef("DOUBLE", nullable=True, comment="住房周转金转入"),
            "transfer_oth": ColumnDef("DOUBLE", nullable=True, comment="其他转入"),
            "adj_lossgain": ColumnDef("DOUBLE", nullable=True, comment="调整以前年度损益"),
            "withdra_legal_surplus": ColumnDef("DOUBLE", nullable=True, comment="提取法定盈余公积"),
            "withdra_legal_pubfund": ColumnDef("DOUBLE", nullable=True, comment="提取法定公益金"),
            "withdra_biz_devfund": ColumnDef("DOUBLE", nullable=True, comment="提取企业发展基金"),
            "withdra_rese_fund": ColumnDef("DOUBLE", nullable=True, comment="提取储备基金"),
            "withdra_oth_ersu": ColumnDef("DOUBLE", nullable=True, comment="提取任意盈余公积金"),
            "workers_welfare": ColumnDef("DOUBLE", nullable=True, comment="职工奖金福利"),
            "distr_profit_shrhder": ColumnDef("DOUBLE", nullable=True, comment="可供股东分配的利润"),
            "prfshare_payable_dvd": ColumnDef("DOUBLE", nullable=True, comment="应付优先股股利"),
            "comshare_payable_dvd": ColumnDef("DOUBLE", nullable=True, comment="应付普通股股利"),
            "capit_comstock_div": ColumnDef("DOUBLE", nullable=True, comment="转作股本的普通股股利"),
            "net_after_nr_lp_correct": ColumnDef("DOUBLE", nullable=True, comment="扣除非经常性损益后的净利润(更正前)"),
            "credit_impa_loss": ColumnDef("DOUBLE", nullable=True, comment="信用减值损失"),
            "net_expo_hedging_benefits": ColumnDef("DOUBLE", nullable=True, comment="净敞口套期收益"),
            "oth_impair_loss_assets": ColumnDef("DOUBLE", nullable=True, comment="其他资产减值损失"),
            "total_opcost": ColumnDef("DOUBLE", nullable=True, comment="营业总成本(二)"),
            "amodcost_fin_assets": ColumnDef("DOUBLE", nullable=True, comment="以摊余成本计量的金融资产终止确认收益"),
            "oth_income": ColumnDef("DOUBLE", nullable=True, comment="其他收益"),
            "asset_disp_income": ColumnDef("DOUBLE", nullable=True, comment="资产处置收益"),
            "continued_net_profit": ColumnDef("DOUBLE", nullable=True, comment="持续经营净利润"),
            "end_net_profit": ColumnDef("DOUBLE", nullable=True, comment="终止经营净利润"),
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
            "income_vip",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
