from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from .config import build_tushare_db_url
from .data_loader import ResearchDataLoader, _normalize_query_date, build_forward_overnight_returns
from .factor_engine import (
    ChipFactorBuilder,
    CrossFeatureBuilder,
    DragonFactorBuilder,
    EventFactorBuilder,
    FundamentalFactorBuilder,
    IndustryFactorBuilder,
    LimitFactorBuilder,
    MarginFactorBuilder,
    MarketFactorBuilder,
    MoneyFlowFactorBuilder,
    NorthboundFactorBuilder,
    OwnershipFactorBuilder,
    TechnicalFactorBuilder,
    generate_event_features,
    generate_time_series_features,
    run_standard_factor_pipeline,
)
from .factor_engine.base import FactorPipelineConfig
from .universe import UniverseFilter


@dataclass(frozen=True)
class FullResearchPipelineConfig:
    time_series_windows: tuple[int, ...] = (5, 10, 20, 60)
    event_windows: tuple[int, ...] = (3, 5, 10, 20)
    train_end_date: str = "2023-12-31"
    validation_end_date: str = "2025-06-30"
    include_chip_distribution: bool = True
    factor_pipeline_config: FactorPipelineConfig = FactorPipelineConfig()


@dataclass
class FullResearchBuildResult:
    panel: pd.DataFrame
    factor_catalog: dict[str, list[str]]
    sample_panels: dict[str, pd.DataFrame]
    factor_columns: list[str]


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame()


def _quote_identifier(identifier: str) -> str:
    cleaned = identifier.strip("`")
    return f"`{cleaned}`"


def _normalize_trade_date(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values.astype(str), errors="coerce")


def _format_trade_date(values: pd.Series) -> pd.Series:
    return _normalize_trade_date(values).dt.strftime("%Y-%m-%d")


def _map_to_trade_calendar(values: pd.Series, trade_calendar: pd.DatetimeIndex, lag: int) -> pd.Series:
    source_dates = _normalize_trade_date(values)
    positions = trade_calendar.searchsorted(source_dates, side="left") + lag
    mapped = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    valid = source_dates.notna() & (positions >= 0) & (positions < len(trade_calendar))
    if valid.any():
        mapped.loc[valid] = trade_calendar.take(positions[valid])
    return mapped


def _shift_non_key_columns(frame: pd.DataFrame, lag: int) -> pd.DataFrame:
    if lag <= 0 or frame.empty:
        return frame
    shifted = frame.sort_values(["ts_code", "trade_date"]) if "ts_code" in frame.columns else frame.sort_values("trade_date")
    key_columns = ["trade_date"]
    if "ts_code" in shifted.columns:
        key_columns.insert(0, "ts_code")
    value_columns = [column for column in shifted.columns if column not in key_columns]
    if not value_columns:
        return shifted
    if "ts_code" in shifted.columns:
        shifted[value_columns] = shifted.groupby("ts_code", sort=False)[value_columns].shift(lag)
    else:
        shifted[value_columns] = shifted[value_columns].shift(lag)
    return shifted


def _prepare_dense_source(
    frame: pd.DataFrame | None,
    source_date_col: str = "trade_date",
    available_lag: int = 0,
    rename_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return _empty_frame()
    prepared = frame.rename(columns=rename_map or {}).copy()
    if source_date_col != "trade_date" and source_date_col in prepared.columns:
        prepared = prepared.rename(columns={source_date_col: "trade_date"})
    if "trade_date" not in prepared.columns:
        return prepared
    prepared["trade_date"] = _format_trade_date(prepared["trade_date"])
    prepared = prepared.dropna(subset=["trade_date"])
    return _shift_non_key_columns(prepared, available_lag)


def _prepare_event_source(
    frame: pd.DataFrame | None,
    trade_calendar: pd.DatetimeIndex,
    source_date_col: str,
    available_lag: int = 1,
    rename_map: dict[str, str] | None = None,
    extra_columns: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return _empty_frame()
    prepared = frame.rename(columns=rename_map or {}).copy()
    if extra_columns:
        for column, value in extra_columns.items():
            prepared[column] = value(prepared) if callable(value) else value
    if source_date_col not in prepared.columns:
        return prepared
    prepared["trade_date"] = _map_to_trade_calendar(prepared[source_date_col], trade_calendar, available_lag).dt.strftime("%Y-%m-%d")
    return prepared.dropna(subset=["trade_date"])


class FullResearchPipeline:
    panel_columns = [
        "ts_code", "trade_date", "open", "close", "pct_chg", "roc_qfq", "mtm_qfq",
        "ma_qfq_5", "ma_qfq_20", "ma_qfq_60", "ema_qfq_10", "ema_qfq_60", "atr_qfq", "close_qfq",
        "boll_upper_qfq", "boll_lower_qfq", "macd_dif_qfq", "macd_dea_qfq", "macd_qfq",
        "dmi_pdi_qfq", "dmi_mdi_qfq", "dmi_adx_qfq", "dmi_adxr_qfq", "trix_qfq", "cr_qfq",
        "topdays", "lowdays", "volume_ratio", "turnover_rate_f", "obv_qfq", "mfi_qfq",
        "rsi_qfq_6", "rsi_qfq_12", "rsi_qfq_24", "kdj_k_qfq", "kdj_d_qfq", "wr_qfq", "cci_qfq",
        "psy_qfq", "bias1_qfq", "bias2_qfq", "bias3_qfq", "pe_ttm", "pb", "ps_ttm", "dv_ttm",
        "total_mv", "circ_mv", "amount",
    ]
    time_series_base_columns = [
        "pct_chg", "net_mf_rate", "winner_rate", "hk_hold_chg",
        "rzmre_intensity", "forecast_surprise_mid", "analyst_target_return", "q_roe",
    ]
    event_state_base_columns = [
        "forecast_surprise_mid", "turnaround_flag", "express_profit_yoy",
        "insider_net_increase", "repurchase_amount_to_mv", "unlock_ratio", "survey_heat",
    ]

    def __init__(self, config: FullResearchPipelineConfig | None = None):
        self.config = config or FullResearchPipelineConfig()

    def _capture_new_columns(self, before: set[str], frame: pd.DataFrame) -> list[str]:
        return sorted(
            column
            for column in frame.columns
            if column not in before and pd.api.types.is_numeric_dtype(frame[column])
        )

    def split_panel_by_sample(self, panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
        trade_dates = _normalize_trade_date(panel["trade_date"])
        train_end = pd.Timestamp(self.config.train_end_date)
        validation_end = pd.Timestamp(self.config.validation_end_date)
        return {
            "train": panel.loc[trade_dates <= train_end].copy(),
            "validation": panel.loc[(trade_dates > train_end) & (trade_dates <= validation_end)].copy(),
            "test": panel.loc[trade_dates > validation_end].copy(),
        }

    def build_from_dataset(self, dataset: dict[str, pd.DataFrame]) -> FullResearchBuildResult:
        panel = dataset["panel"].copy()
        if "overnight_return" not in panel.columns:
            panel = build_forward_overnight_returns(panel)

        stock_basic = dataset.get("stock_basic", _empty_frame())
        panel = UniverseFilter().apply(
            panel,
            stock_basic=stock_basic,
            st_flags=dataset.get("stock_st"),
            suspensions=dataset.get("stock_suspend_d"),
        )
        if not stock_basic.empty and "industry" not in panel.columns:
            panel = panel.merge(stock_basic.loc[:, ["ts_code", "industry"]].drop_duplicates("ts_code"), on="ts_code", how="left")
        trade_calendar = pd.DatetimeIndex(sorted(_normalize_trade_date(panel["trade_date"]).dropna().unique()))
        factor_catalog: dict[str, list[str]] = {}

        panel = TechnicalFactorBuilder().build(panel)
        factor_catalog["technical"] = [column for column in TechnicalFactorBuilder.factor_columns if column in panel.columns]

        before = set(panel.columns)
        panel = MoneyFlowFactorBuilder().build(
            panel,
            money_flow=_prepare_dense_source(dataset.get("stock_money_flow")),
            money_flow_dc=_prepare_dense_source(dataset.get("stock_money_flow_dc")),
        )
        factor_catalog["money_flow"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = ChipFactorBuilder().build(
            panel,
            chip_perf=_prepare_dense_source(dataset.get("stock_cyq_perf")),
            chip_distribution=_prepare_dense_source(dataset.get("stock_cyq_chips"))
            if self.config.include_chip_distribution
            else _empty_frame(),
        )
        factor_catalog["chip"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = NorthboundFactorBuilder().build(
            panel,
            hk_hold=_prepare_dense_source(dataset.get("stock_hk_hold"), available_lag=1),
            hsgt_top10=_prepare_dense_source(dataset.get("stock_hsgt_top10")),
            ccass_hold=_prepare_dense_source(dataset.get("stock_ccass_hold"), available_lag=1),
        )
        factor_catalog["northbound"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = MarginFactorBuilder().build(
            panel,
            margin_detail=_prepare_dense_source(dataset.get("stock_margin_detail"), available_lag=1),
        )
        factor_catalog["margin"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = LimitFactorBuilder().build(
            panel,
            limit_list=_prepare_dense_source(dataset.get("stock_limit_list_d")),
            limit_price=_prepare_dense_source(dataset.get("stock_stk_limit")),
        )
        factor_catalog["limit"] = [
            column
            for column in self._capture_new_columns(before, panel)
            if column
            not in {
                "limit_pre_close",
                "limit_up_price",
                "limit_down_price",
                "close_limit_up_flag",
                "close_limit_down_flag",
                "one_word_limit_up_flag",
            }
        ]

        before = set(panel.columns)
        panel = DragonFactorBuilder().build(
            panel,
            top_list=_prepare_dense_source(dataset.get("stock_top_list")),
            top_inst=_prepare_dense_source(dataset.get("stock_top_inst")),
            block_trade=_prepare_dense_source(dataset.get("stock_block_trade")),
        )
        factor_catalog["dragon"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = OwnershipFactorBuilder().build(
            panel,
            holder_number=_prepare_event_source(dataset.get("stock_stk_holdernumber"), trade_calendar, "ann_date"),
            holder_trade=_prepare_event_source(dataset.get("stock_stk_holdertrade"), trade_calendar, "ann_date"),
            repurchase=_prepare_event_source(dataset.get("stock_repurchase"), trade_calendar, "ann_date"),
            share_float=_prepare_event_source(dataset.get("stock_share_float"), trade_calendar, "float_date"),
            pledge_stat=_prepare_event_source(dataset.get("stock_pledge_stat"), trade_calendar, "end_date"),
            top10_holders=_prepare_event_source(dataset.get("stock_top10_holders"), trade_calendar, "ann_date"),
            top10_floatholders=_prepare_event_source(
                dataset.get("stock_top10_floatholders"),
                trade_calendar,
                "ann_date",
            ),
        )
        factor_catalog["ownership"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = EventFactorBuilder().build(
            panel,
            forecast=_prepare_event_source(dataset.get("stock_forecast_vip"), trade_calendar, "ann_date"),
            express=_prepare_event_source(dataset.get("stock_express_vip"), trade_calendar, "ann_date"),
            report_rc=_prepare_event_source(
                dataset.get("stock_report_rc"),
                trade_calendar,
                "report_date",
                extra_columns={
                    "report_id": lambda frame: frame.get("report_title").fillna(
                        pd.Series(frame.index.astype(str), index=frame.index)
                    )
                },
            ),
            disclosure_date=_prepare_event_source(
                dataset.get("stock_disclosure_date"),
                trade_calendar,
                "ann_date",
                extra_columns={"next_disclosure_date": lambda frame: frame.get("actual_date").fillna(frame.get("pre_date"))},
            ),
            survey=_prepare_event_source(dataset.get("stock_stk_surv"), trade_calendar, "surv_date"),
        )
        factor_catalog["event"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = FundamentalFactorBuilder().build(
            panel,
            fina_indicator=_prepare_event_source(dataset.get("stock_fina_indicator_vip"), trade_calendar, "ann_date"),
            income=_prepare_event_source(dataset.get("stock_income_vip"), trade_calendar, "ann_date"),
            balancesheet=_prepare_event_source(dataset.get("stock_balancesheet_vip"), trade_calendar, "ann_date"),
            cashflow=_prepare_event_source(dataset.get("stock_cashflow_vip"), trade_calendar, "ann_date"),
            audit=_prepare_event_source(dataset.get("stock_fina_audit"), trade_calendar, "ann_date"),
        )
        factor_catalog["fundamental"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = generate_time_series_features(
            panel,
            factor_cols=[column for column in self.time_series_base_columns if column in panel.columns],
            windows=self.config.time_series_windows,
        )
        factor_catalog["time_series"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = generate_event_features(
            panel,
            event_cols=[column for column in self.event_state_base_columns if column in panel.columns],
            windows=self.config.event_windows,
        )
        factor_catalog["event_state"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = CrossFeatureBuilder().build(panel)
        factor_catalog["cross_feature"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = IndustryFactorBuilder().build(panel)
        factor_catalog["industry"] = self._capture_new_columns(before, panel)

        before = set(panel.columns)
        panel = MarketFactorBuilder().build(
            panel,
            market_money_flow=_prepare_dense_source(
                dataset.get("stock_money_flow_mkt_dc"),
                rename_map={"net_amount": "net_mf_amount"},
            ),
            market_hsgt=_prepare_dense_source(dataset.get("stock_money_flow_hsgt")),
            market_margin=_prepare_dense_source(dataset.get("stock_margin"), available_lag=1),
            ah_comparison=_prepare_dense_source(dataset.get("stock_stk_ah_comparison")),
        )
        factor_catalog["market"] = self._capture_new_columns(before, panel)

        factor_columns = sorted({column for columns in factor_catalog.values() for column in columns})
        panel = run_standard_factor_pipeline(
            panel,
            factor_cols=factor_columns,
            config=self.config.factor_pipeline_config,
            industry_col="industry",
        )
        return FullResearchBuildResult(
            panel=panel,
            factor_catalog=factor_catalog,
            sample_panels=self.split_panel_by_sample(panel),
            factor_columns=factor_columns,
        )

    def load_dataset_from_database(self, start_date: str, end_date: str | None = None) -> dict[str, pd.DataFrame]:
        loader = ResearchDataLoader(engine=create_engine(build_tushare_db_url()))
        engine = loader.get_engine()
        normalized_start_date = _normalize_query_date(start_date)
        normalized_end_date = _normalize_query_date(end_date)
        dataset = {
            "panel": loader.load_panel(
                start_date=normalized_start_date,
                end_date=normalized_end_date,
                columns=self.panel_columns,
            )
        }
        table_specs = {
            "stock_basic": ("stock_basic", ["ts_code", "list_date", "industry"], None),
            "stock_st": ("stock_st", ["ts_code", "trade_date", "type_name"], "trade_date"),
            "stock_suspend_d": ("stock_suspend_d", ["ts_code", "trade_date", "suspend_type"], "trade_date"),
            "stock_money_flow": ("stock_money_flow", ["ts_code", "trade_date", "buy_sm_amount", "sell_sm_amount", "buy_lg_amount", "sell_lg_amount", "buy_elg_amount", "sell_elg_amount", "net_mf_amount"], "trade_date"),
            "stock_money_flow_dc": ("stock_money_flow_dc", ["ts_code", "trade_date", "net_amount", "net_amount_rate", "buy_elg_amount_rate", "buy_sm_amount_rate"], "trade_date"),
            "stock_cyq_perf": ("stock_cyq_perf", ["ts_code", "trade_date", "winner_rate", "weight_avg", "cost_5pct", "cost_15pct", "cost_50pct", "cost_85pct", "cost_95pct"], "trade_date"),
            "stock_hk_hold": ("stock_hk_hold", ["ts_code", "trade_date", "ratio", "vol"], "trade_date"),
            "stock_hsgt_top10": ("stock_hsgt_top10", ["ts_code", "trade_date", "net_amount"], "trade_date"),
            "stock_ccass_hold": ("stock_ccass_hold", ["ts_code", "trade_date", "hold_nums", "hold_ratio"], "trade_date"),
            "stock_margin_detail": ("stock_margin_detail", ["ts_code", "trade_date", "rzye", "rqye", "rzmre"], "trade_date"),
            "stock_margin": ("stock_margin", ["trade_date", "rzrqye"], "trade_date"),
            "stock_limit_list_d": ("stock_limit_list_d", ["ts_code", "trade_date", "limit", "fd_amount", "float_mv", "open_times", "limit_times"], "trade_date"),
            "stock_top_list": ("stock_top_list", ["ts_code", "trade_date", "net_rate", "net_amount"], "trade_date"),
            "stock_top_inst": ("stock_top_inst", ["ts_code", "trade_date", "net_buy", "buy", "sell"], "trade_date"),
            "stock_block_trade": ("stock_block_trade", ["ts_code", "trade_date", "price", "amount"], "trade_date"),
            "stock_stk_limit": ("stock_stk_limit", ["ts_code", "trade_date", "pre_close", "up_limit", "down_limit"], "trade_date"),
            "stock_stk_ah_comparison": (
                "stock_stk_ah_comparison",
                ["ts_code", "trade_date", "ah_comparison", "ah_premium"],
                "trade_date",
            ),
            "stock_stk_holdernumber": ("stock_stk_holdernumber", ["ts_code", "ann_date", "end_date", "holder_num"], "ann_date"),
            "stock_stk_holdertrade": ("stock_stk_holdertrade", ["ts_code", "ann_date", "in_de", "change_ratio"], "ann_date"),
            "stock_repurchase": ("stock_repurchase", ["ts_code", "ann_date", "amount", "high_limit"], "ann_date"),
            "stock_share_float": ("stock_share_float", ["ts_code", "float_date", "float_ratio"], "float_date"),
            "stock_pledge_stat": ("stock_pledge_stat", ["ts_code", "end_date", "pledge_ratio"], "end_date"),
            "stock_top10_holders": (
                "stock_top10_holders",
                ["ts_code", "ann_date", "end_date", "hold_ratio", "hold_float_ratio", "hold_change"],
                "ann_date",
            ),
            "stock_top10_floatholders": (
                "stock_top10_floatholders",
                ["ts_code", "ann_date", "end_date", "hold_ratio", "hold_float_ratio", "hold_change"],
                "ann_date",
            ),
            "stock_forecast_vip": ("stock_forecast_vip", ["ts_code", "ann_date", "type", "p_change_min", "p_change_max"], "ann_date"),
            "stock_express_vip": ("stock_express_vip", ["ts_code", "ann_date", "yoy_dedu_np", "yoy_eps"], "ann_date"),
            "stock_report_rc": ("stock_report_rc", ["ts_code", "report_date", "report_title", "max_price", "min_price"], "report_date"),
            "stock_disclosure_date": ("stock_disclosure_date", ["ts_code", "ann_date", "pre_date", "actual_date"], "ann_date"),
            "stock_stk_surv": ("stock_stk_surv", ["ts_code", "surv_date", "name"], "surv_date"),
            "stock_fina_indicator_vip": ("stock_fina_indicator_vip", ["ts_code", "ann_date", "q_roe", "gross_margin", "q_gr_yoy", "q_profit_yoy"], "ann_date"),
            "stock_income_vip": ("stock_income_vip", ["ts_code", "ann_date", "revenue"], "ann_date"),
            "stock_balancesheet_vip": ("stock_balancesheet_vip", ["ts_code", "ann_date", "total_assets", "total_liab"], "ann_date"),
            "stock_cashflow_vip": ("stock_cashflow_vip", ["ts_code", "ann_date", "n_cashflow_act"], "ann_date"),
            "stock_fina_audit": ("stock_fina_audit", ["ts_code", "ann_date", "audit_result"], "ann_date"),
            "stock_money_flow_hsgt": ("stock_money_flow_hsgt", ["trade_date", "north_money"], "trade_date"),
            "stock_money_flow_mkt_dc": (
                "stock_money_flow_mkt_dc",
                ["trade_date", "net_amount", "net_amount_rate", "buy_elg_amount_rate", "buy_sm_amount_rate"],
                "trade_date",
            ),
        }
        if self.config.include_chip_distribution:
            table_specs["stock_cyq_chips"] = ("stock_cyq_chips", ["ts_code", "trade_date", "price", "percent"], "trade_date")
        with engine.connect() as conn:
            for key, (table_name, columns, date_column) in table_specs.items():
                quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
                query = [f"SELECT {quoted_columns} FROM {_quote_identifier(table_name)}"]
                params: dict[str, Any] = {}
                if date_column is not None:
                    quoted_date_column = _quote_identifier(date_column)
                    query.append(f"WHERE {quoted_date_column} >= :start_date")
                    params["start_date"] = normalized_start_date
                    if normalized_end_date:
                        query.append(f"AND {quoted_date_column} <= :end_date")
                        params["end_date"] = normalized_end_date
                dataset[key] = pd.read_sql_query(text("\n".join(query)), conn, params=params)
        return dataset


def save_factor_catalog(catalog: dict[str, list[str]], output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
