from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import ResearchConfig, build_tushare_db_url
from .factor_engine.base import generate_event_features


def _normalize_query_date(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed):
        return value
    return parsed.strftime("%Y%m%d")


def _sort_panel(panel: pd.DataFrame, group_key: str = "ts_code", date_col: str = "trade_date") -> pd.DataFrame:
    if panel.empty:
        return panel.copy()
    return panel.sort_values([group_key, date_col]).reset_index(drop=True)


def apply_available_lag(
    panel: pd.DataFrame,
    lag_by_column: Mapping[str, int],
    group_key: str = "ts_code",
    date_col: str = "trade_date",
) -> pd.DataFrame:
    shifted = _sort_panel(panel, group_key=group_key, date_col=date_col)
    for column, lag in lag_by_column.items():
        if column not in shifted.columns or lag <= 0:
            continue
        shifted[column] = shifted.groupby(group_key, sort=False)[column].shift(lag)
    return shifted


def build_forward_overnight_returns(
    panel: pd.DataFrame,
    open_col: str = "open",
    close_col: str = "close",
    output_col: str = "overnight_return",
    group_key: str = "ts_code",
    date_col: str = "trade_date",
) -> pd.DataFrame:
    enriched = _sort_panel(panel, group_key=group_key, date_col=date_col)
    next_open = enriched.groupby(group_key, sort=False)[open_col].shift(-1)
    enriched[output_col] = (next_open - enriched[close_col]) / enriched[close_col]
    return enriched


@dataclass(frozen=True)
class DataSourceSpec:
    table_name: str
    available_lag: int = 0
    key_columns: Sequence[str] = ("ts_code", "trade_date")
    date_column: str = "trade_date"
    effective_date_column: str | None = None
    sparse_event: bool = False


DEFAULT_SOURCE_SPECS: dict[str, DataSourceSpec] = {
    "panel": DataSourceSpec(table_name="stock_stk_factor_pro", available_lag=0),
    "money_flow": DataSourceSpec(table_name="stock_money_flow", available_lag=0),
    "money_flow_dc": DataSourceSpec(table_name="stock_money_flow_dc", available_lag=0),
    "hk_hold": DataSourceSpec(table_name="stock_hk_hold", available_lag=1),
    "ccass_hold": DataSourceSpec(table_name="stock_ccass_hold", available_lag=1),
    "margin_detail": DataSourceSpec(table_name="stock_margin_detail", available_lag=1),
    "holder_trade": DataSourceSpec(table_name="stock_stk_holdertrade", available_lag=1, date_column="ann_date", effective_date_column="ann_date", sparse_event=True),
    "forecast": DataSourceSpec(table_name="stock_forecast_vip", available_lag=1, date_column="ann_date", effective_date_column="ann_date", sparse_event=True),
    "express": DataSourceSpec(table_name="stock_express_vip", available_lag=1, date_column="ann_date", effective_date_column="ann_date", sparse_event=True),
    "report_rc": DataSourceSpec(table_name="stock_report_rc", available_lag=1, date_column="report_date", effective_date_column="report_date", sparse_event=True),
    "survey": DataSourceSpec(table_name="stock_stk_surv", available_lag=1, date_column="surv_date", effective_date_column="surv_date", sparse_event=True),
}


class ResearchDataLoader:
    def __init__(
        self,
        config: ResearchConfig | None = None,
        engine: Engine | None = None,
        source_specs: Mapping[str, DataSourceSpec] | None = None,
    ):
        self.config = config or ResearchConfig()
        self.engine = engine
        self.source_specs = dict(DEFAULT_SOURCE_SPECS)
        if source_specs:
            self.source_specs.update(source_specs)

    def get_engine(self) -> Engine:
        if self.engine is not None:
            return self.engine
        return create_engine(build_tushare_db_url(self.config.database_env_name))

    def load_panel(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        selected_columns = list(columns or ("ts_code", "trade_date", "open", "close"))
        quoted = [f"`{c}`" if not c.startswith("`") else c for c in selected_columns]
        sql = [
            f"SELECT {', '.join(quoted)}",
            f"FROM {self.config.panel_table}",
            "WHERE trade_date >= :start_date",
        ]
        params = {"start_date": _normalize_query_date(start_date or self.config.start_date)}
        if end_date or self.config.end_date:
            sql.append("AND trade_date <= :end_date")
            params["end_date"] = _normalize_query_date(end_date or self.config.end_date)
        query = text("\n".join(sql))
        return pd.read_sql_query(query, self.get_engine(), params=params)

    def load_named_source(
        self,
        source_name: str,
        start_date: str | None = None,
        end_date: str | None = None,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        spec = self.source_specs[source_name]
        selected_columns = list(columns or spec.key_columns)
        if spec.date_column not in selected_columns:
            selected_columns.append(spec.date_column)
        quoted = [f"`{c}`" if not c.startswith("`") else c for c in selected_columns]
        sql = [
            f"SELECT {', '.join(quoted)}",
            f"FROM {spec.table_name}",
            f"WHERE {spec.date_column} >= :start_date",
        ]
        params = {"start_date": _normalize_query_date(start_date or self.config.start_date)}
        if end_date or self.config.end_date:
            sql.append(f"AND {spec.date_column} <= :end_date")
            params["end_date"] = _normalize_query_date(end_date or self.config.end_date)
        query = text("\n".join(sql))
        return pd.read_sql_query(query, self.get_engine(), params=params)

    def align_event_frame(self, frame: pd.DataFrame, source_name: str) -> pd.DataFrame:
        spec = self.source_specs[source_name]
        aligned = frame.copy()
        source_date = spec.effective_date_column or spec.date_column
        if source_date not in aligned.columns:
            return aligned
        aligned["trade_date"] = pd.to_datetime(aligned[source_date], errors="coerce")
        if spec.available_lag > 0:
            aligned["trade_date"] = aligned["trade_date"] + pd.to_timedelta(spec.available_lag, unit="D")
        aligned["trade_date"] = aligned["trade_date"].dt.strftime("%Y-%m-%d")
        return aligned

    def build_sparse_event_features(
        self,
        frame: pd.DataFrame,
        source_name: str,
        value_columns: Sequence[str],
        windows: Sequence[int] = (1, 3, 5, 10, 20, 60),
    ) -> pd.DataFrame:
        aligned = self.align_event_frame(frame, source_name)
        return generate_event_features(aligned, event_cols=value_columns, windows=windows)

    def load_dataset(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        source_requests: Mapping[str, Sequence[str]] | None = None,
    ) -> dict[str, pd.DataFrame]:
        requests = source_requests or {"panel": ("ts_code", "trade_date", "open", "close")}
        dataset: dict[str, pd.DataFrame] = {}
        for source_name, columns in requests.items():
            dataset[source_name] = self.load_named_source(
                source_name,
                start_date=start_date,
                end_date=end_date,
                columns=columns,
            )
        return dataset

    def prepare_panel(
        self,
        panel: pd.DataFrame,
        lag_by_column: Mapping[str, int] | None = None,
        open_col: str = "open",
        close_col: str = "close",
    ) -> pd.DataFrame:
        prepared = _sort_panel(panel)
        if lag_by_column:
            prepared = apply_available_lag(prepared, lag_by_column)
        return build_forward_overnight_returns(prepared, open_col=open_col, close_col=close_col)
