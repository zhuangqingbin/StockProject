from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df


STRATEGY_NAME = "supply_shock_matrix"
STRATEGY_DESCRIPTION = "供给冲击 / 吸收修复矩阵"
SOURCE_TABLES = "stock_stk_factor_pro, stock_share_float, stock_stk_holdertrade"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass(frozen=True)
class SignalRuleDef:
    family: str
    code: str
    description: str
    predicate: Callable[[pd.DataFrame], pd.Series]


def _format_date_range(start_date: str, end_date: str | None) -> str:
    return f"{start_date} -> {end_date or 'latest'}"


def _print_execution_context(
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
) -> None:
    print(f"strategy = {STRATEGY_NAME}", flush=True)
    print(f"description = {STRATEGY_DESCRIPTION}", flush=True)
    print(f"source_tables = {SOURCE_TABLES}", flush=True)
    print(f"requested_date_range = {_format_date_range(start_date, end_date)}", flush=True)
    print(f"output_dir = {output_dir}", flush=True)
    print(f"min_sample = {min_sample}", flush=True)
    print(f"top_n = {top_n}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=STRATEGY_DESCRIPTION)
    parser.add_argument("--start-date", default="20180101", help="起始日期，格式 YYYYMMDD")
    parser.add_argument("--end-date", default=None, help="结束日期，格式 YYYYMMDD")
    parser.add_argument("--min-sample", type=int, default=30, help="最小样本数阈值")
    parser.add_argument("--top-n", type=int, default=20, help="终端显示条数")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="结果输出目录")
    return parser


def _load_end_date(end_date: str | None) -> str | None:
    if end_date is None:
        return None
    return (datetime.strptime(end_date, "%Y%m%d") + timedelta(days=10)).strftime("%Y%m%d")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=numerator.index, dtype="float64")
    valid = denominator.notna() & (denominator != 0)
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _frame_effective_start_date(*frames: pd.DataFrame) -> str | None:
    values: list[pd.Series] = []
    for frame in frames:
        if not frame.empty and "trade_date" in frame.columns:
            series = frame["trade_date"].dropna().astype(str)
            if not series.empty:
                values.append(series)
    if not values:
        return None
    return str(pd.concat(values, ignore_index=True).min())


def _frame_effective_end_date(*frames: pd.DataFrame) -> str | None:
    values: list[pd.Series] = []
    for frame in frames:
        if not frame.empty and "trade_date" in frame.columns:
            series = frame["trade_date"].dropna().astype(str)
            if not series.empty:
                values.append(series)
    if not values:
        return None
    return str(pd.concat(values, ignore_index=True).max())


def _column_or_nan(frame: pd.DataFrame, column: str) -> pd.Series:
    if column in frame.columns:
        return frame[column]
    return pd.Series(np.nan, index=frame.index, name=column)


def _positive_column_mask(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    mask = pd.Series(False, index=frame.index, dtype=bool)
    for column in columns:
        if column in frame.columns:
            mask = mask | frame[column].fillna(0).gt(0)
    return mask


def _series_predicate(column: str) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(df: pd.DataFrame) -> pd.Series:
        if column not in df.columns:
            return pd.Series(False, index=df.index, dtype=bool)
        return df[column].fillna(False).astype(bool)

    return predicate


def _numeric_predicate(column: str, comparator: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(df: pd.DataFrame) -> pd.Series:
        if column not in df.columns:
            return pd.Series(False, index=df.index, dtype=bool)

        series = pd.to_numeric(df[column], errors="coerce")
        if comparator == "ge":
            return series.ge(threshold).fillna(False)
        if comparator == "gt":
            return series.gt(threshold).fillna(False)
        if comparator == "le":
            return series.le(threshold).fillna(False)
        if comparator == "lt":
            return series.lt(threshold).fillna(False)
        if comparator == "eq":
            return series.eq(threshold).fillna(False)
        raise ValueError(f"Unsupported comparator: {comparator}")

    return predicate


def _combine_predicates(*predicates: Callable[[pd.DataFrame], pd.Series]) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(df: pd.DataFrame) -> pd.Series:
        combined = pd.Series(True, index=df.index, dtype=bool)
        for item in predicates:
            combined = combined & item(df).fillna(False).astype(bool)
        return combined

    return predicate


def _pct_chg_positive() -> Callable[[pd.DataFrame], pd.Series]:
    return _numeric_predicate("pct_chg", "gt", 0)


def _threshold_token(value: float) -> str:
    text = f"{value:g}"
    return text.replace(".", "p")


def _rule_code(*parts: str) -> str:
    return "__".join(parts)


def _comparison_suffix(column: str, comparator: str, threshold: float) -> str:
    return f"{column}_{comparator}_{_threshold_token(threshold)}"


def _share_anchor_columns(prefix: str) -> list[str]:
    return [
        f"{prefix}_event_count",
        f"{prefix}_total_float_share",
        f"{prefix}_total_float_ratio",
        f"{prefix}_max_float_ratio",
        f"{prefix}_ratio_ipo",
        f"{prefix}_ratio_orig",
        f"{prefix}_ratio_private_placement",
    ]


def _holder_anchor_columns(prefix: str) -> list[str]:
    columns = [
        f"{prefix}_event_count",
        f"{prefix}_total_change_vol",
        f"{prefix}_total_change_ratio",
        f"{prefix}_max_change_ratio",
    ]
    for direction in ("de", "in"):
        columns.extend(
            [
                f"{prefix}_{direction}_event_count",
                f"{prefix}_{direction}_total_change_vol",
                f"{prefix}_{direction}_total_change_ratio",
                f"{prefix}_{direction}_max_change_ratio",
            ]
        )
        for holder_alias in ("exec", "company", "person"):
            columns.extend(
                [
                    f"{prefix}_{direction}_{holder_alias}_total_change_ratio",
                    f"{prefix}_{direction}_{holder_alias}_max_change_ratio",
                ]
            )
    return columns


def load_base_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        open_qfq,
        high_qfq,
        low_qfq,
        close_qfq,
        pct_chg,
        vol,
        amount,
        turnover_rate_f,
        volume_ratio,
        boll_lower_qfq,
        rsi_qfq_6,
        rsi_qfq_12,
        ma_qfq_5,
        ma_qfq_20,
        ma_qfq_60,
        downdays,
        updays
    FROM stock_stk_factor_pro
    WHERE trade_date >= :start_date
      AND close_qfq IS NOT NULL
      AND vol > 0
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"
    columns = [
        "ts_code",
        "trade_date",
        "open_qfq",
        "high_qfq",
        "low_qfq",
        "close_qfq",
        "pct_chg",
        "vol",
        "amount",
        "turnover_rate_f",
        "volume_ratio",
        "boll_lower_qfq",
        "rsi_qfq_6",
        "rsi_qfq_12",
        "ma_qfq_5",
        "ma_qfq_20",
        "ma_qfq_60",
        "downdays",
        "updays",
    ]
    frame = query_df(sql, params)
    return frame.reindex(columns=columns) if not frame.empty else _empty_frame(columns)


def load_share_float_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        ann_date,
        float_date,
        float_share,
        float_ratio,
        holder_name,
        share_type
    FROM stock_share_float
    WHERE (
        ann_date >= :start_date
        OR float_date >= :start_date
    )
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql = """
    SELECT
        ts_code,
        ann_date,
        float_date,
        float_share,
        float_ratio,
        holder_name,
        share_type
    FROM stock_share_float
    WHERE (
        (ann_date >= :start_date AND ann_date <= :load_end_date)
        OR (float_date >= :start_date AND float_date <= :load_end_date)
    )
    """
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, ann_date, float_date"
    columns = ["ts_code", "ann_date", "float_date", "float_share", "float_ratio", "holder_name", "share_type"]
    frame = query_df(sql, params)
    if frame.empty:
        return _empty_frame(columns)

    result = frame.reindex(columns=columns).copy()
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        result.loc[~result["ann_date"].between(start_date, load_end_date), "ann_date"] = pd.NA
        result.loc[~result["float_date"].between(start_date, load_end_date), "float_date"] = pd.NA
    else:
        result.loc[result["ann_date"] < start_date, "ann_date"] = pd.NA
        result.loc[result["float_date"] < start_date, "float_date"] = pd.NA
    return result


def load_holdertrade_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        ann_date,
        holder_name,
        holder_type,
        in_de,
        change_vol,
        change_ratio,
        after_share,
        after_ratio,
        avg_price,
        total_share,
        begin_date,
        close_date
    FROM stock_stk_holdertrade
    WHERE (
        ann_date >= :start_date
        OR begin_date >= :start_date
        OR close_date >= :start_date
    )
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql = """
    SELECT
        ts_code,
        ann_date,
        holder_name,
        holder_type,
        in_de,
        change_vol,
        change_ratio,
        after_share,
        after_ratio,
        avg_price,
        total_share,
        begin_date,
        close_date
    FROM stock_stk_holdertrade
    WHERE (
        (ann_date >= :start_date AND ann_date <= :load_end_date)
        OR (begin_date >= :start_date AND begin_date <= :load_end_date)
        OR (close_date >= :start_date AND close_date <= :load_end_date)
    )
    """
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, ann_date, begin_date, close_date"
    columns = [
        "ts_code",
        "ann_date",
        "holder_name",
        "holder_type",
        "in_de",
        "change_vol",
        "change_ratio",
        "after_share",
        "after_ratio",
        "avg_price",
        "total_share",
        "begin_date",
        "close_date",
    ]
    frame = query_df(sql, params)
    if frame.empty:
        return _empty_frame(columns)

    result = frame.reindex(columns=columns).copy()
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        result.loc[~result["ann_date"].between(start_date, load_end_date), "ann_date"] = pd.NA
        result.loc[~result["begin_date"].between(start_date, load_end_date), "begin_date"] = pd.NA
        result.loc[~result["close_date"].between(start_date, load_end_date), "close_date"] = pd.NA
    else:
        result.loc[result["ann_date"] < start_date, "ann_date"] = pd.NA
        result.loc[result["begin_date"] < start_date, "begin_date"] = pd.NA
        result.loc[result["close_date"] < start_date, "close_date"] = pd.NA
    return result


def _aggregate_share_anchor(frame: pd.DataFrame, anchor_column: str, prefix: str) -> pd.DataFrame:
    columns = ["ts_code", "trade_date", *_share_anchor_columns(prefix)]
    if frame.empty or anchor_column not in frame.columns:
        return _empty_frame(columns)

    anchored = frame.loc[frame[anchor_column].notna()].copy()
    if anchored.empty:
        return _empty_frame(columns)

    anchored["trade_date"] = anchored[anchor_column].astype(str)
    result = (
        anchored.groupby(["ts_code", "trade_date"], sort=False)
        .agg(
            event_count=("ts_code", "size"),
            total_float_share=("float_share", "sum"),
            total_float_ratio=("float_ratio", "sum"),
            max_float_ratio=("float_ratio", "max"),
        )
        .reset_index()
    )

    alias_map = {
        "ratio_ipo": "首发股",
        "ratio_orig": "首发原始股",
        "ratio_private_placement": "定增股份",
    }
    for alias_suffix, share_type in alias_map.items():
        alias_frame = (
            anchored.loc[anchored["share_type"] == share_type]
            .groupby(["ts_code", "trade_date"], sort=False)["float_ratio"]
            .sum()
            .rename(alias_suffix)
            .reset_index()
        )
        result = result.merge(alias_frame, on=["ts_code", "trade_date"], how="left")

    result = result.rename(
        columns={name: f"{prefix}_{name}" for name in result.columns if name not in {"ts_code", "trade_date"}}
    )
    return result.reindex(columns=columns)


def _aggregate_holder_anchor(frame: pd.DataFrame, anchor_column: str, prefix: str) -> pd.DataFrame:
    columns = ["ts_code", "trade_date", *_holder_anchor_columns(prefix)]
    if frame.empty or anchor_column not in frame.columns:
        return _empty_frame(columns)

    anchored = frame.loc[frame[anchor_column].notna()].copy()
    if anchored.empty:
        return _empty_frame(columns)

    anchored["trade_date"] = anchored[anchor_column].astype(str)
    result = (
        anchored.groupby(["ts_code", "trade_date"], sort=False)
        .agg(
            event_count=("ts_code", "size"),
            total_change_vol=("change_vol", "sum"),
            total_change_ratio=("change_ratio", "sum"),
            max_change_ratio=("change_ratio", "max"),
        )
        .reset_index()
    )

    direction_map = {"DE": "de", "IN": "in"}
    type_map = {"G": "exec", "C": "company", "P": "person"}

    for direction_code, direction_label in direction_map.items():
        direction_frame = anchored.loc[anchored["in_de"] == direction_code].copy()
        if direction_frame.empty:
            direction_agg = _empty_frame(["ts_code", "trade_date"])
        else:
            direction_agg = (
                direction_frame.groupby(["ts_code", "trade_date"], sort=False)
                .agg(
                    event_count=("ts_code", "size"),
                    total_change_vol=("change_vol", "sum"),
                    total_change_ratio=("change_ratio", "sum"),
                    max_change_ratio=("change_ratio", "max"),
                )
                .reset_index()
            )
        direction_agg = direction_agg.rename(
            columns={name: f"{prefix}_{direction_label}_{name}" for name in direction_agg.columns if name not in {"ts_code", "trade_date"}}
        )
        result = result.merge(direction_agg, on=["ts_code", "trade_date"], how="left")

        for holder_type, holder_label in type_map.items():
            holder_frame = direction_frame.loc[direction_frame["holder_type"] == holder_type].copy()
            if holder_frame.empty:
                holder_agg = _empty_frame(["ts_code", "trade_date"])
            else:
                holder_agg = (
                    holder_frame.groupby(["ts_code", "trade_date"], sort=False)
                    .agg(
                        total_change_ratio=("change_ratio", "sum"),
                        max_change_ratio=("change_ratio", "max"),
                    )
                    .reset_index()
                )
            holder_agg = holder_agg.rename(
                columns={
                    name: f"{prefix}_{direction_label}_{holder_label}_{name}"
                    for name in holder_agg.columns
                    if name not in {"ts_code", "trade_date"}
                }
            )
            result = result.merge(holder_agg, on=["ts_code", "trade_date"], how="left")

    return result.reindex(columns=columns)


def aggregate_share_float_events(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["ts_code", "trade_date", *_share_anchor_columns("sf_ann"), *_share_anchor_columns("sf_float")]
    if frame.empty:
        return _empty_frame(columns)

    ann_frame = _aggregate_share_anchor(frame, "ann_date", "sf_ann")
    float_frame = _aggregate_share_anchor(frame, "float_date", "sf_float")
    result = ann_frame.merge(float_frame, on=["ts_code", "trade_date"], how="outer")
    return result.reindex(columns=columns)


def aggregate_holdertrade_events(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "ts_code",
        "trade_date",
        *_holder_anchor_columns("ht_ann"),
        *_holder_anchor_columns("ht_begin"),
        *_holder_anchor_columns("ht_close"),
    ]
    if frame.empty:
        return _empty_frame(columns)

    ann_frame = _aggregate_holder_anchor(frame, "ann_date", "ht_ann")
    begin_frame = _aggregate_holder_anchor(frame, "begin_date", "ht_begin")
    close_frame = _aggregate_holder_anchor(frame, "close_date", "ht_close")
    result = ann_frame.merge(begin_frame, on=["ts_code", "trade_date"], how="outer").merge(
        close_frame,
        on=["ts_code", "trade_date"],
        how="outer",
    )
    return result.reindex(columns=columns)


def merge_side_frames(
    base_df: pd.DataFrame,
    share_float_daily_df: pd.DataFrame,
    holdertrade_daily_df: pd.DataFrame,
) -> pd.DataFrame:
    result = base_df.copy()
    result = result.merge(share_float_daily_df, on=["ts_code", "trade_date"], how="left")
    result = result.merge(holdertrade_daily_df, on=["ts_code", "trade_date"], how="left")
    return result


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).copy()
    grouped = result.groupby("ts_code", sort=False)

    if "close_qfq" in result.columns:
        result["ret_1d"] = grouped["close_qfq"].shift(-1) / result["close_qfq"] - 1
        result["ret_3d"] = grouped["close_qfq"].shift(-3) / result["close_qfq"] - 1
    else:
        result["ret_1d"] = pd.Series(np.nan, index=result.index)
        result["ret_3d"] = pd.Series(np.nan, index=result.index)

    if "low_qfq" in result.columns:
        result["rolling_low_120"] = grouped["low_qfq"].transform(lambda s: s.rolling(120, min_periods=1).min())
    else:
        result["rolling_low_120"] = pd.Series(np.nan, index=result.index)

    if "high_qfq" in result.columns:
        result["rolling_high_120"] = grouped["high_qfq"].transform(lambda s: s.rolling(120, min_periods=1).max())
    else:
        result["rolling_high_120"] = pd.Series(np.nan, index=result.index)

    result["pos120"] = _safe_divide(
        result["close_qfq"] - result["rolling_low_120"],
        result["rolling_high_120"] - result["rolling_low_120"],
    ) if "close_qfq" in result.columns else pd.Series(np.nan, index=result.index)
    result["close_to_low_120"] = _safe_divide(result["close_qfq"], result["rolling_low_120"]) if "close_qfq" in result.columns else pd.Series(np.nan, index=result.index)

    close_qfq = _column_or_nan(result, "close_qfq")
    boll_lower_qfq = _column_or_nan(result, "boll_lower_qfq")
    rsi_qfq_6 = _column_or_nan(result, "rsi_qfq_6")
    volume_ratio = _column_or_nan(result, "volume_ratio")
    turnover_rate_f = _column_or_nan(result, "turnover_rate_f")
    ma_qfq_5 = _column_or_nan(result, "ma_qfq_5")
    ma_qfq_20 = _column_or_nan(result, "ma_qfq_20")
    ma_qfq_60 = _column_or_nan(result, "ma_qfq_60")

    result["is_bottom_zone"] = (
        (result["pos120"] <= 0.25)
        | (result["close_to_low_120"] <= 1.08)
        | ((close_qfq <= boll_lower_qfq * 1.03) & (rsi_qfq_6 < 35))
    ).fillna(False)

    result["oversold_state"] = ((close_qfq <= boll_lower_qfq * 1.03) & (rsi_qfq_6 < 35)).fillna(False)
    result["volume_expand_state"] = volume_ratio.ge(1.5).fillna(False)
    result["high_turnover_state"] = turnover_rate_f.ge(3.0).fillna(False)
    if "close_qfq" in result.columns and "ma_qfq_5" in result.columns:
        result["ma_reclaim_state"] = (close_qfq.ge(ma_qfq_5) & grouped["close_qfq"].shift(1).lt(grouped["ma_qfq_5"].shift(1))).fillna(False)
    else:
        result["ma_reclaim_state"] = pd.Series(False, index=result.index)
    result["weak_trend_state"] = (close_qfq.lt(ma_qfq_20) & close_qfq.lt(ma_qfq_60)).fillna(False)
    result["strong_trend_state"] = (close_qfq.ge(ma_qfq_20) & ma_qfq_20.ge(ma_qfq_60)).fillna(False)
    result["pullback_state"] = (result["strong_trend_state"] & close_qfq.le(ma_qfq_20 * 1.02)).fillna(False)

    supply_event_columns = [column for column in result.columns if column.startswith(("sf_", "ht_")) and column.endswith("_event_count")]
    result["has_supply_event"] = _positive_column_mask(result, supply_event_columns)
    result["has_share_float_event"] = _positive_column_mask(result, [column for column in supply_event_columns if column.startswith("sf_")])
    result["has_holdertrade_event"] = _positive_column_mask(result, [column for column in supply_event_columns if column.startswith("ht_")])
    result["has_de_event"] = _positive_column_mask(result, [column for column in result.columns if column.endswith("_de_event_count")])
    result["has_in_event"] = _positive_column_mask(result, [column for column in result.columns if column.endswith("_in_event_count")])
    return result


def build_signal_rule_defs() -> list[SignalRuleDef]:
    comparator_symbol = {"ge": ">=", "gt": ">", "le": "<=", "lt": "<", "eq": "="}
    share_float_labels = {
        "sf_ann_total_float_ratio": "公告浮筹总比",
        "sf_float_total_float_ratio": "流通浮筹总比",
        "sf_ann_max_float_ratio": "公告最大浮筹比",
        "sf_float_max_float_ratio": "流通最大浮筹比",
        "sf_ann_ratio_orig": "公告原始股比",
        "sf_float_ratio_orig": "流通原始股比",
        "sf_ann_ratio_private_placement": "公告定增比",
        "sf_float_ratio_private_placement": "流通定增比",
        "sf_ann_ratio_ipo": "公告首发比",
        "sf_float_ratio_ipo": "流通首发比",
    }
    holdertrade_labels = {
        "ht_ann_de_total_change_ratio": "公告减持总强度",
        "ht_begin_de_total_change_ratio": "起始减持总强度",
        "ht_close_de_total_change_ratio": "收盘减持总强度",
        "ht_ann_de_max_change_ratio": "公告减持峰值",
        "ht_begin_de_max_change_ratio": "起始减持峰值",
        "ht_close_de_max_change_ratio": "收盘减持峰值",
        "ht_ann_de_event_count": "公告减持事件数",
        "ht_begin_de_event_count": "起始减持事件数",
        "ht_close_de_event_count": "收盘减持事件数",
        "ht_ann_de_exec_total_change_ratio": "公告高管减持强度",
        "ht_begin_de_exec_total_change_ratio": "起始高管减持强度",
        "ht_close_de_exec_total_change_ratio": "收盘高管减持强度",
        "ht_ann_de_company_total_change_ratio": "公告公司减持强度",
        "ht_begin_de_company_total_change_ratio": "起始公司减持强度",
        "ht_close_de_company_total_change_ratio": "收盘公司减持强度",
    }
    supply_state_defs = [
        ("weak_trend_state", "弱趋势", _series_predicate("weak_trend_state")),
        ("high_turnover_state", "高换手", _series_predicate("high_turnover_state")),
        ("volume_expand_state", "放量", _series_predicate("volume_expand_state")),
        ("is_bottom_zone", "底部区", _series_predicate("is_bottom_zone")),
    ]
    absorption_state_defs = [
        ("is_bottom_zone", "底部区", _series_predicate("is_bottom_zone")),
        ("oversold_state", "超跌", _series_predicate("oversold_state")),
        ("ma_reclaim_state", "站回均线", _series_predicate("ma_reclaim_state")),
        ("pullback_state", "回踩", _series_predicate("pullback_state")),
        ("strong_trend_state", "强趋势", _series_predicate("strong_trend_state")),
    ]

    def make_numeric_seed(
        label_map: dict[str, str],
        column: str,
        comparator: str,
        threshold: float,
    ) -> tuple[str, str, Callable[[pd.DataFrame], pd.Series]]:
        seed_suffix = _comparison_suffix(column, comparator, threshold)
        description = f"{label_map[column]} {comparator_symbol[comparator]} {threshold:g}"
        return seed_suffix, description, _numeric_predicate(column, comparator, threshold)

    def make_bool_seed(
        seed_suffix: str,
        description: str,
        *predicates: Callable[[pd.DataFrame], pd.Series],
    ) -> tuple[str, str, Callable[[pd.DataFrame], pd.Series]]:
        return seed_suffix, description, _combine_predicates(*predicates)

    def expand_state_rules(
        family: str,
        seeds: list[tuple[str, str, Callable[[pd.DataFrame], pd.Series]]],
        state_defs: list[tuple[str, str, Callable[[pd.DataFrame], pd.Series]]],
    ) -> list[SignalRuleDef]:
        rules: list[SignalRuleDef] = []
        for seed_suffix, seed_description, seed_predicate in seeds:
            for state_code, state_description, state_predicate in state_defs:
                rules.append(
                    SignalRuleDef(
                        family=family,
                        code=_rule_code(family, seed_suffix, state_code),
                        description=f"{seed_description}，{state_description}",
                        predicate=_combine_predicates(seed_predicate, state_predicate),
                    )
                )
        return rules

    supply_pressure_seed_specs: list[tuple[dict[str, str], str, list[float], str]] = [
        (share_float_labels, "sf_ann_total_float_ratio", [1, 3, 5, 10], "ge"),
        (share_float_labels, "sf_float_total_float_ratio", [1, 3, 5, 10], "ge"),
        (share_float_labels, "sf_ann_max_float_ratio", [1, 3, 5], "ge"),
        (share_float_labels, "sf_float_max_float_ratio", [1, 3, 5], "ge"),
        (share_float_labels, "sf_ann_ratio_orig", [1, 3], "ge"),
        (share_float_labels, "sf_float_ratio_orig", [1, 3], "ge"),
        (share_float_labels, "sf_ann_ratio_private_placement", [1, 3], "ge"),
        (share_float_labels, "sf_float_ratio_private_placement", [1, 3], "ge"),
        (share_float_labels, "sf_ann_ratio_ipo", [3, 5], "ge"),
        (share_float_labels, "sf_float_ratio_ipo", [3, 5], "ge"),
        (holdertrade_labels, "ht_ann_de_total_change_ratio", [0.2, 0.5, 1, 2], "ge"),
        (holdertrade_labels, "ht_begin_de_total_change_ratio", [0.2, 0.5, 1, 2], "ge"),
        (holdertrade_labels, "ht_close_de_total_change_ratio", [0.2, 0.5, 1, 2], "ge"),
        (holdertrade_labels, "ht_ann_de_max_change_ratio", [0.2, 0.5, 1], "ge"),
        (holdertrade_labels, "ht_begin_de_max_change_ratio", [0.2, 0.5, 1], "ge"),
        (holdertrade_labels, "ht_close_de_max_change_ratio", [0.2, 0.5, 1], "ge"),
        (holdertrade_labels, "ht_ann_de_event_count", [1, 2, 3], "ge"),
        (holdertrade_labels, "ht_begin_de_event_count", [1, 2, 3], "ge"),
        (holdertrade_labels, "ht_close_de_event_count", [1, 2, 3], "ge"),
        (holdertrade_labels, "ht_ann_de_exec_total_change_ratio", [0.2, 0.5], "ge"),
        (holdertrade_labels, "ht_begin_de_exec_total_change_ratio", [0.2, 0.5], "ge"),
        (holdertrade_labels, "ht_close_de_exec_total_change_ratio", [0.2, 0.5], "ge"),
        (holdertrade_labels, "ht_ann_de_company_total_change_ratio", [0.2, 0.5], "ge"),
        (holdertrade_labels, "ht_begin_de_company_total_change_ratio", [0.2, 0.5], "ge"),
        (holdertrade_labels, "ht_close_de_company_total_change_ratio", [0.2, 0.5], "ge"),
    ]

    supply_pressure_seeds: list[tuple[str, str, Callable[[pd.DataFrame], pd.Series]]] = []
    for label_map, column, thresholds, comparator in supply_pressure_seed_specs:
        for threshold in thresholds:
            supply_pressure_seeds.append(make_numeric_seed(label_map, column, comparator, threshold))
    supply_pressure_seeds.append(
        make_bool_seed(
            "has_share_float_event__has_de_event",
            "浮筹事件叠加减持事件",
            _series_predicate("has_share_float_event"),
            _series_predicate("has_de_event"),
        )
    )

    absorption_repair_seeds: list[tuple[str, str, Callable[[pd.DataFrame], pd.Series]]] = [
        make_bool_seed(
            "has_supply_event__pct_chg_gt_0",
            "供给事件后转强",
            _series_predicate("has_supply_event"),
            _pct_chg_positive(),
        ),
        make_bool_seed(
            "has_de_event__pct_chg_gt_0",
            "减持事件后转强",
            _series_predicate("has_de_event"),
            _pct_chg_positive(),
        ),
        make_bool_seed(
            "has_de_event__has_in_event",
            "减持叠加承接",
            _series_predicate("has_de_event"),
            _series_predicate("has_in_event"),
        ),
        make_bool_seed(
            "has_share_float_event__has_in_event",
            "浮筹事件叠加承接",
            _series_predicate("has_share_float_event"),
            _series_predicate("has_in_event"),
        ),
    ]

    for threshold in [1, 3, 5]:
        absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(_comparison_suffix("sf_float_total_float_ratio", "ge", threshold), "pct_chg_gt_0"),
                    f"流通浮筹比 >= {threshold:g} 且转强",
                    _numeric_predicate("sf_float_total_float_ratio", "ge", threshold),
                    _pct_chg_positive(),
            )
        )
    for threshold in [1, 3]:
        absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(_comparison_suffix("sf_ann_total_float_ratio", "ge", threshold), "pct_chg_gt_0"),
                    f"公告浮筹比 >= {threshold:g} 且转强",
                    _numeric_predicate("sf_ann_total_float_ratio", "ge", threshold),
                    _pct_chg_positive(),
            )
        )
    for threshold in [0.5, 1, 2]:
        absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(_comparison_suffix("ht_close_de_total_change_ratio", "ge", threshold), "pct_chg_gt_0"),
                    f"收盘减持强度 >= {threshold:g} 且转强",
                    _numeric_predicate("ht_close_de_total_change_ratio", "ge", threshold),
                    _pct_chg_positive(),
            )
        )
    for threshold in [0.5, 1]:
        absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(_comparison_suffix("ht_ann_de_total_change_ratio", "ge", threshold), "has_in_event"),
                    f"公告减持强度 >= {threshold:g} 且承接",
                    _numeric_predicate("ht_ann_de_total_change_ratio", "ge", threshold),
                    _series_predicate("has_in_event"),
            )
        )
    for close_threshold in [0.5, 1]:
        for in_threshold in [0.1, 0.3]:
            absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(
                        _comparison_suffix("ht_close_de_total_change_ratio", "ge", close_threshold),
                        "ht_close_in_total_change_ratio",
                        _comparison_suffix("ht_close_in_total_change_ratio", "ge", in_threshold),
                    ),
                    f"收盘减持强度 >= {close_threshold:g} 且收盘承接 >= {in_threshold:g}",
                    _numeric_predicate("ht_close_de_total_change_ratio", "ge", close_threshold),
                    _numeric_predicate("ht_close_in_total_change_ratio", "ge", in_threshold),
                )
            )
    for float_threshold in [1, 3]:
        for in_threshold in [0.1, 0.3]:
            absorption_repair_seeds.append(
                make_bool_seed(
                    _rule_code(
                        _comparison_suffix("sf_float_total_float_ratio", "ge", float_threshold),
                        "ht_ann_in_total_change_ratio",
                        _comparison_suffix("ht_ann_in_total_change_ratio", "ge", in_threshold),
                    ),
                    f"流通浮筹比 >= {float_threshold:g} 且公告承接 >= {in_threshold:g}",
                    _numeric_predicate("sf_float_total_float_ratio", "ge", float_threshold),
                    _numeric_predicate("ht_ann_in_total_change_ratio", "ge", in_threshold),
                )
            )

    rules: list[SignalRuleDef] = []
    for seed_suffix, seed_description, seed_predicate in supply_pressure_seeds:
        rules.append(
            SignalRuleDef(
                family="plain_supply_pressure",
                code=_rule_code("plain_supply_pressure", seed_suffix),
                description=seed_description,
                predicate=seed_predicate,
            )
        )
    rules.extend(expand_state_rules("state_supply_pressure", supply_pressure_seeds, supply_state_defs))

    for seed_suffix, seed_description, seed_predicate in absorption_repair_seeds:
        rules.append(
            SignalRuleDef(
                family="plain_absorption_repair",
                code=_rule_code("plain_absorption_repair", seed_suffix),
                description=seed_description,
                predicate=seed_predicate,
            )
        )
    rules.extend(expand_state_rules("state_absorption_repair", absorption_repair_seeds, absorption_state_defs))
    return rules


def _series_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.mean())


def _series_variance(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.var(ddof=1))


def _series_win_rate(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.gt(0).mean())


def summarize_signal_matrix(
    frame: pd.DataFrame,
    rule_defs: list[SignalRuleDef] | None = None,
    min_sample: int = 30,
    show_progress: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rule_defs = build_signal_rule_defs() if rule_defs is None else rule_defs
    summary_rows: list[dict[str, Any]] = []
    trigger_frames: list[pd.DataFrame] = []

    iterable = rule_defs
    if show_progress:
        try:
            from tqdm import tqdm

            iterable = tqdm(rule_defs, desc="Scanning strategies")
        except ImportError:
            iterable = rule_defs

    for rule in iterable:
        mask = rule.predicate(frame).fillna(False).astype(bool)
        triggered = frame.loc[mask].copy()
        sample_count = int(mask.sum())
        summary_rows.append(
            {
                "strategy_family": rule.family,
                "signal_code": rule.code,
                "sample_count": sample_count,
                "win_rate_1d": _series_win_rate(triggered.get("ret_1d", pd.Series(dtype=float))),
                "avg_ret_1d": _series_mean(triggered.get("ret_1d", pd.Series(dtype=float))),
                "var_ret_1d": _series_variance(triggered.get("ret_1d", pd.Series(dtype=float))),
                "win_rate_3d": _series_win_rate(triggered.get("ret_3d", pd.Series(dtype=float))),
                "avg_ret_3d": _series_mean(triggered.get("ret_3d", pd.Series(dtype=float))),
                "var_ret_3d": _series_variance(triggered.get("ret_3d", pd.Series(dtype=float))),
                "is_low_sample": sample_count < min_sample,
            }
        )
        if triggered.empty:
            continue
        selected = triggered.reindex(
            columns=[
                "ts_code",
                "trade_date",
                "strategy_family",
                "signal_code",
                "close_qfq",
                "pct_chg",
                "volume_ratio",
                "turnover_rate_f",
                "ret_1d",
                "ret_3d",
            ]
        ).copy()
        selected["strategy_family"] = rule.family
        selected["signal_code"] = rule.code
        trigger_frames.append(selected)

    summary_columns = [
        "strategy_family",
        "signal_code",
        "sample_count",
        "win_rate_1d",
        "avg_ret_1d",
        "var_ret_1d",
        "win_rate_3d",
        "avg_ret_3d",
        "var_ret_3d",
        "is_low_sample",
    ]
    trigger_columns = [
        "ts_code",
        "trade_date",
        "strategy_family",
        "signal_code",
        "close_qfq",
        "pct_chg",
        "volume_ratio",
        "turnover_rate_f",
        "ret_1d",
        "ret_3d",
    ]
    summary_df = pd.DataFrame(summary_rows, columns=summary_columns)
    trigger_df = (
        pd.concat(trigger_frames, ignore_index=True)
        if trigger_frames
        else _empty_frame(trigger_columns)
    )
    return summary_df, trigger_df


def build_compact_summary(summary_df: pd.DataFrame, trigger_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "strategy_family",
        "signal_code",
        "sample_count",
        "win_rate_1d",
        "avg_ret_1d",
        "var_ret_1d",
        "win_rate_3d",
        "avg_ret_3d",
        "var_ret_3d",
        "latest_trade_date",
        "latest_hit_stocks",
    ]
    if summary_df.empty:
        return _empty_frame(columns)

    compact_df = summary_df.copy()
    if not trigger_df.empty:
        latest_rows = []
        for signal_code, group in trigger_df.groupby("signal_code", sort=False):
            latest_trade_date = str(group["trade_date"].max())
            latest_hit_stocks = ",".join(
                sorted(
                    group.loc[group["trade_date"] == latest_trade_date, "ts_code"]
                    .astype(str)
                    .unique()
                )
            )
            latest_rows.append(
                {
                    "signal_code": signal_code,
                    "latest_trade_date": latest_trade_date,
                    "latest_hit_stocks": latest_hit_stocks,
                }
            )
        latest_rows = pd.DataFrame(latest_rows)
        compact_df = compact_df.merge(latest_rows, on="signal_code", how="left")
    else:
        compact_df["latest_trade_date"] = ""
        compact_df["latest_hit_stocks"] = ""

    compact_df["latest_trade_date"] = compact_df["latest_trade_date"].fillna("")
    compact_df["latest_hit_stocks"] = compact_df["latest_hit_stocks"].fillna("")

    compact_df = compact_df.sort_values(
        [
            "win_rate_1d",
            "avg_ret_1d",
            "win_rate_3d",
            "avg_ret_3d",
            "sample_count",
            "signal_code",
        ],
        ascending=[False, False, False, False, False, True],
        kind="mergesort",
    )
    return compact_df.reindex(columns=columns)


def build_signal_code_markdown(rule_defs: list[SignalRuleDef]) -> str:
    lines = ["# Signal Codebook", "", "| family | signal_code | description |", "| --- | --- | --- |"]
    for rule in sorted(rule_defs, key=lambda item: (item.family, item.code)):
        lines.append(f"| {rule.family} | {rule.code} | {rule.description} |")
    return "\n".join(lines)


def _build_output_stem() -> str:
    return datetime.now().strftime("%m%d_%H%M")


def write_outputs(compact_df: pd.DataFrame, signal_code_markdown: str, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _build_output_stem()
    summary_csv = output_dir / f"{stem}.csv"
    summary_md = output_dir / f"{stem}.md"

    output_df = compact_df.copy()
    for column in ("latest_trade_date", "latest_hit_stocks"):
        if column in output_df.columns:
            output_df[column] = output_df[column].fillna("")

    output_df.to_csv(summary_csv, index=False)
    markdown_parts = [
        "# Supply Shock Matrix Summary",
        "",
        "## Compact Summary",
        "",
        output_df.to_markdown(index=False),
        "",
        "## Signal Codebook",
        "",
        signal_code_markdown,
        "",
    ]
    summary_md.write_text("\n".join(markdown_parts), encoding="utf-8")
    return {"summary_csv": summary_csv, "summary_md": summary_md}


def run_analysis(
    *,
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
    show_progress: bool = False,
) -> dict[str, Any]:
    print("==> load_base_frame", flush=True)
    base_df = load_base_frame(start_date=start_date, end_date=end_date)
    share_float_df = load_share_float_frame(start_date=start_date, end_date=end_date)
    holdertrade_df = load_holdertrade_frame(start_date=start_date, end_date=end_date)
    share_float_daily_df = aggregate_share_float_events(share_float_df)
    holdertrade_daily_df = aggregate_holdertrade_events(holdertrade_df)
    merged_df = merge_side_frames(base_df, share_float_daily_df, holdertrade_daily_df)
    effective_start_date = _frame_effective_start_date(base_df) or start_date
    effective_end_date = _frame_effective_end_date(base_df) or (end_date or effective_start_date)
    loaded_rows = len(base_df)
    loaded_stocks = int(base_df["ts_code"].nunique()) if "ts_code" in base_df.columns else 0
    print(
        f"==> load_base_frame done | loaded_rows={loaded_rows} | loaded_stocks={loaded_stocks} | date_range={effective_start_date} -> {effective_end_date}",
        flush=True,
    )

    print("==> build_features", flush=True)
    featured_df = build_features(merged_df)
    if end_date is not None and "trade_date" in featured_df.columns:
        analysis_df = featured_df.loc[featured_df["trade_date"].le(end_date)].copy()
    else:
        analysis_df = featured_df.copy()

    rule_defs = build_signal_rule_defs()
    print("==> Scanning strategies", flush=True)
    summary_df, trigger_df = summarize_signal_matrix(
        analysis_df,
        rule_defs=rule_defs,
        min_sample=min_sample,
        show_progress=show_progress,
    )

    print("==> build_compact_summary", flush=True)
    compact_df = build_compact_summary(summary_df, trigger_df)
    print("==> build_signal_code_markdown", flush=True)
    signal_code_markdown = build_signal_code_markdown(rule_defs)

    print("==> write_outputs", flush=True)
    output_paths = write_outputs(compact_df, signal_code_markdown, output_dir)
    return {
        "source_df": base_df,
        "base_df": base_df,
        "share_float_df": share_float_df,
        "holdertrade_df": holdertrade_df,
        "share_float_daily_df": share_float_daily_df,
        "holdertrade_daily_df": holdertrade_daily_df,
        "merged_df": merged_df,
        "featured_df": featured_df,
        "summary_df": summary_df,
        "trigger_df": trigger_df,
        "compact_df": compact_df,
        "output_paths": output_paths,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    _print_execution_context(args.start_date, args.end_date, args.min_sample, args.top_n, output_dir)
    result = run_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        min_sample=args.min_sample,
        top_n=args.top_n,
        output_dir=output_dir,
        show_progress=True,
    )
    print(f"==> summary_csv = {result['output_paths']['summary_csv']}", flush=True)
    print(f"==> summary_md = {result['output_paths']['summary_md']}", flush=True)
    print(f"==> rows = {len(result['compact_df'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
