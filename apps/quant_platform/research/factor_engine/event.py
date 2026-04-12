from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys, sort_panel


TURNAROUND_TYPES = {"扭亏", "首盈", "续盈"}


def _asof_merge_by_code(panel: pd.DataFrame, events: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    left = sort_panel(panel).copy()
    right = sort_panel(events).copy()
    left["trade_date_dt"] = pd.to_datetime(left["trade_date"])
    right["trade_date_dt"] = pd.to_datetime(right["trade_date"])
    merged = pd.merge_asof(
        left.sort_values("trade_date_dt"),
        right.sort_values("trade_date_dt")[["ts_code", "trade_date_dt", *value_columns]],
        on="trade_date_dt",
        by="ts_code",
        direction="backward",
    )
    merged["trade_date"] = merged["trade_date_dt"].dt.strftime("%Y-%m-%d")
    return merged.drop(columns=["trade_date_dt"])


class EventFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        forecast: pd.DataFrame | None = None,
        express: pd.DataFrame | None = None,
        report_rc: pd.DataFrame | None = None,
        disclosure_date: pd.DataFrame | None = None,
        survey: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        if forecast is not None and not forecast.empty:
            fc = forecast.copy()
            fc["forecast_surprise_mid"] = (fc.get("p_change_min", 0.0) + fc.get("p_change_max", 0.0)) / 2
            fc["turnaround_flag"] = fc.get("type", "").isin(TURNAROUND_TYPES).astype(float)
            factors = merge_on_panel_keys(factors, fc, value_columns=["forecast_surprise_mid", "turnaround_flag"])

        if express is not None and not express.empty:
            ex = express.copy()
            ex["express_profit_yoy"] = ex.get("yoy_dedu_np").fillna(ex.get("yoy_eps"))
            factors = merge_on_panel_keys(factors, ex, value_columns=["express_profit_yoy"])

        if report_rc is not None and not report_rc.empty:
            rc = report_rc.copy()
            rc["analyst_target_return"] = (
                (rc.get("max_price", 0.0) + rc.get("min_price", 0.0)) / 2
            )
            factors = _asof_merge_by_code(factors, rc, value_columns=["analyst_target_return"])
            factors["analyst_target_return"] = (
                factors["analyst_target_return"] / factors["close_qfq"].replace(0, pd.NA) - 1
            )
            rc["trade_date_dt"] = pd.to_datetime(rc["trade_date"])
            factors["trade_date_dt"] = pd.to_datetime(factors["trade_date"])
            attention_records: list[float] = []
            for row in factors.loc[:, ["ts_code", "trade_date_dt"]].itertuples(index=False):
                recent = rc.loc[
                    (rc["ts_code"] == row.ts_code)
                    & (rc["trade_date_dt"] <= row.trade_date_dt)
                    & (rc["trade_date_dt"] > row.trade_date_dt - pd.Timedelta(days=20))
                ]
                attention_records.append(float(recent["report_id"].nunique()))
            factors["analyst_attention_20d"] = attention_records
            factors = factors.drop(columns=["trade_date_dt"])

        if disclosure_date is not None and not disclosure_date.empty:
            dd = disclosure_date.copy()
            factors = merge_on_panel_keys(factors, dd, value_columns=["next_disclosure_date"])
            countdown = pd.to_datetime(factors.get("next_disclosure_date"), errors="coerce") - pd.to_datetime(
                factors["trade_date"], errors="coerce"
            )
            factors["disclosure_countdown"] = countdown.dt.days

        if survey is not None and not survey.empty:
            surv = survey.copy()
            surv["trade_date_dt"] = pd.to_datetime(surv["trade_date"])
            factors["trade_date_dt"] = pd.to_datetime(factors["trade_date"])
            heats: list[float] = []
            for row in factors.loc[:, ["ts_code", "trade_date_dt"]].itertuples(index=False):
                recent = surv.loc[
                    (surv["ts_code"] == row.ts_code)
                    & (surv["trade_date_dt"] <= row.trade_date_dt)
                    & (surv["trade_date_dt"] > row.trade_date_dt - pd.Timedelta(days=20))
                ]
                heats.append(float(len(recent)))
            factors["survey_heat"] = heats
            factors = factors.drop(columns=["trade_date_dt"], errors="ignore")

        return factors
