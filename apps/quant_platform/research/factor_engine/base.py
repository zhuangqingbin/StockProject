from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


KEY_COLUMNS = ["ts_code", "trade_date"]


@dataclass(frozen=True)
class FactorPipelineConfig:
    winsorize_n_mad: float = 3.0
    zscore: bool = True
    fill_missing: bool = True


def sort_panel(panel: pd.DataFrame, group_key: str = "ts_code", date_col: str = "trade_date") -> pd.DataFrame:
    if panel.empty:
        return panel.copy()
    return panel.sort_values([group_key, date_col]).reset_index(drop=True)


def merge_on_panel_keys(
    panel: pd.DataFrame,
    feature_frame: pd.DataFrame | None,
    value_columns: Sequence[str] | None = None,
    key_columns: Sequence[str] = KEY_COLUMNS,
) -> pd.DataFrame:
    if feature_frame is None or feature_frame.empty:
        return panel.copy()
    columns = list(key_columns)
    if value_columns is None:
        value_columns = [column for column in feature_frame.columns if column not in key_columns]
    columns.extend([column for column in value_columns if column in feature_frame.columns])
    deduped = feature_frame.loc[:, columns].drop_duplicates(list(key_columns))
    existing_overlap = [column for column in value_columns if column in panel.columns]
    base_panel = panel.drop(columns=existing_overlap, errors="ignore")
    return base_panel.merge(deduped, on=list(key_columns), how="left")


def winsorize_mad_by_date(
    panel: pd.DataFrame,
    factor_cols: Sequence[str],
    date_col: str = "trade_date",
    n_mad: float = 3.0,
) -> pd.DataFrame:
    clipped = panel.copy()
    date_groups = clipped.groupby(date_col, dropna=False)

    for column in factor_cols:
        median = date_groups[column].transform("median")
        abs_dev = (clipped[column] - median).abs()
        mad = abs_dev.groupby(clipped[date_col], dropna=False).transform("median")
        std = date_groups[column].transform("std").fillna(0.0)
        scale = mad.mask(mad.isna() | mad.eq(0), std)
        lower = median - (n_mad * scale)
        upper = median + (n_mad * scale)
        clipped[column] = clipped[column].clip(lower=lower, upper=upper)

    return clipped


def zscore_by_date(
    panel: pd.DataFrame,
    factor_cols: Sequence[str],
    date_col: str = "trade_date",
) -> pd.DataFrame:
    normalized = panel.copy()
    grouped = normalized.groupby(date_col, dropna=False)

    for column in factor_cols:
        mean = grouped[column].transform("mean")
        std = grouped[column].transform(lambda values: values.std(ddof=0))
        normalized[column] = ((normalized[column] - mean) / std).mask(std.isna() | std.eq(0), 0.0)

    return normalized


def fill_factor_missing_values(
    panel: pd.DataFrame,
    factor_cols: Sequence[str],
    date_col: str = "trade_date",
    industry_col: str = "industry",
) -> pd.DataFrame:
    filled = panel.copy()

    for column in factor_cols:
        if industry_col in filled.columns:
            industry_median = filled.groupby([date_col, industry_col], dropna=False)[column].transform("median")
        else:
            industry_median = pd.Series(index=filled.index, dtype=float)
        market_median = filled.groupby(date_col, dropna=False)[column].transform("median")
        filled[column] = filled[column].fillna(industry_median).fillna(market_median)

    return filled


def run_standard_factor_pipeline(
    panel: pd.DataFrame,
    factor_cols: Sequence[str],
    config: FactorPipelineConfig | None = None,
    date_col: str = "trade_date",
    industry_col: str = "industry",
) -> pd.DataFrame:
    cfg = config or FactorPipelineConfig()
    available_cols = [
        column
        for column in factor_cols
        if column in panel.columns and pd.api.types.is_numeric_dtype(panel[column])
    ]
    standardized = panel.copy()

    if not available_cols:
        return standardized

    standardized = winsorize_mad_by_date(
        standardized,
        available_cols,
        date_col=date_col,
        n_mad=cfg.winsorize_n_mad,
    )
    if cfg.fill_missing:
        standardized = fill_factor_missing_values(
            standardized,
            available_cols,
            date_col=date_col,
            industry_col=industry_col,
        )
    if cfg.zscore:
        standardized = zscore_by_date(standardized, available_cols, date_col=date_col)
    return standardized


def _group_transform(
    panel: pd.DataFrame,
    column: str,
    group_key: str,
    transform,
) -> pd.Series:
    return panel.groupby(group_key, sort=False)[column].transform(transform)


def _rolling_percentile(values: pd.Series) -> float:
    ranked = values.rank(pct=True)
    return float(ranked.iloc[-1]) if len(ranked) else np.nan


def _trend_t_stat(values: pd.Series) -> float:
    array = values.to_numpy(dtype=float)
    if len(array) < 2 or np.allclose(array.std(ddof=0), 0):
        return 0.0
    x = np.arange(len(array), dtype=float)
    slope = np.polyfit(x, array, 1)[0]
    std = float(array.std(ddof=0))
    return 0.0 if std == 0 else float(slope / std)


def generate_time_series_features(
    panel: pd.DataFrame,
    factor_cols: Sequence[str],
    windows: Sequence[int],
    group_key: str = "ts_code",
    date_col: str = "trade_date",
) -> pd.DataFrame:
    transformed = sort_panel(panel, group_key=group_key, date_col=date_col)

    for column in factor_cols:
        if column not in transformed.columns:
            continue
        grouped = transformed.groupby(group_key, sort=False)[column]
        for window in windows:
            if window <= 0:
                continue
            momentum_col = f"{column}_momentum_{window}"
            transformed[momentum_col] = grouped.transform(lambda values: values - values.shift(window))
            transformed[f"{column}_acceleration_{window}"] = transformed.groupby(group_key, sort=False)[
                momentum_col
            ].transform(lambda values: values - values.shift(1))
            transformed[f"{column}_quantile_{window}"] = grouped.transform(
                lambda values: values.rolling(window, min_periods=window).apply(_rolling_percentile, raw=False)
            )
            transformed[f"{column}_volatility_{window}"] = grouped.transform(
                lambda values: values.rolling(window, min_periods=window).std(ddof=1)
            )
            transformed[f"{column}_skewness_{window}"] = grouped.transform(
                lambda values: values.rolling(window, min_periods=window).skew()
            )
            rolling_mean = grouped.transform(lambda values: values.rolling(window, min_periods=window).mean())
            rolling_std = grouped.transform(lambda values: values.rolling(window, min_periods=window).std(ddof=1))
            transformed[f"{column}_mr_distance_{window}"] = (
                (transformed[column] - rolling_mean) / rolling_std.replace(0, np.nan)
            )
            transformed[f"{column}_trend_t_stat_{window}"] = grouped.transform(
                lambda values: values.rolling(window, min_periods=window).apply(_trend_t_stat, raw=False)
            )

    return transformed


def _event_age(values: pd.Series) -> pd.Series:
    ages: list[float] = []
    last_seen: int | None = None
    for index, value in enumerate(values.fillna(0).to_list()):
        if value != 0:
            last_seen = index
            ages.append(0.0)
            continue
        if last_seen is None:
            ages.append(np.nan)
            continue
        ages.append(float(index - last_seen))
    return pd.Series(ages, index=values.index, dtype=float)


def _state_duration(values: pd.Series) -> pd.Series:
    durations: list[float] = []
    current = 0
    for value in values.fillna(0).to_list():
        if value != 0:
            current += 1
        else:
            current = 0
        durations.append(float(current))
    return pd.Series(durations, index=values.index, dtype=float)


def generate_event_features(
    panel: pd.DataFrame,
    event_cols: Sequence[str],
    windows: Sequence[int],
    group_key: str = "ts_code",
    date_col: str = "trade_date",
    half_life: float = 3.0,
) -> pd.DataFrame:
    transformed = sort_panel(panel, group_key=group_key, date_col=date_col)

    for column in event_cols:
        if column not in transformed.columns:
            continue
        grouped = transformed.groupby(group_key, sort=False)[column]
        age_col = f"{column}_event_age"
        transformed[age_col] = grouped.transform(_event_age)
        transformed[f"{column}_state_duration"] = grouped.transform(_state_duration)
        decay = np.exp(-transformed[age_col] / half_life)
        transformed[f"{column}_event_decay"] = transformed[column].fillna(0.0) * decay.fillna(0.0)

        event_flag = transformed[column].fillna(0.0).ne(0).astype(float)
        for window in windows:
            if window <= 0:
                continue
            transformed[f"{column}_event_count_{window}"] = event_flag.groupby(
                transformed[group_key], sort=False
            ).transform(lambda values: values.rolling(window, min_periods=1).sum())
            transformed[f"{column}_event_decay_{window}"] = transformed[f"{column}_event_decay"].groupby(
                transformed[group_key], sort=False
            ).transform(lambda values: values.rolling(window, min_periods=1).sum())
            transformed[f"{column}_revision_strength_{window}"] = (
                transformed[column].fillna(0.0)
                .groupby(transformed[group_key], sort=False)
                .transform(lambda values: values.rolling(window, min_periods=1).sum())
            )

    return transformed
