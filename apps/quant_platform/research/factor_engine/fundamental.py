from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys


AUDIT_RISK_MAP = {
    "标准无保留意见": 0.0,
    "带强调事项段无保留意见": 0.2,
    "保留意见": 0.6,
    "否定意见": 1.0,
    "无法表示意见": 1.0,
}


class FundamentalFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        fina_indicator: pd.DataFrame | None = None,
        income: pd.DataFrame | None = None,
        balancesheet: pd.DataFrame | None = None,
        cashflow: pd.DataFrame | None = None,
        audit: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()
        factors = merge_on_panel_keys(
            factors,
            fina_indicator,
            value_columns=["q_roe", "gross_margin", "q_gr_yoy", "q_profit_yoy"],
        )
        factors = merge_on_panel_keys(factors, income, value_columns=["revenue"])
        factors = merge_on_panel_keys(factors, balancesheet, value_columns=["total_assets", "total_liab"])
        factors = merge_on_panel_keys(factors, cashflow, value_columns=["n_cashflow_act"])
        factors["q_ocf_to_sales"] = factors.get("n_cashflow_act", 0.0) / factors.get("revenue", 0.0).replace(0, pd.NA)
        factors["debt_to_assets"] = factors.get("total_liab", 0.0) / factors.get("total_assets", 0.0).replace(0, pd.NA)
        if audit is not None and not audit.empty:
            factors = merge_on_panel_keys(factors, audit, value_columns=["audit_result"])
            factors["audit_opinion_risk"] = factors["audit_result"].map(AUDIT_RISK_MAP).fillna(0.5)
        return factors
