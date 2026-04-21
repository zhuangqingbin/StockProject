from __future__ import annotations

import argparse
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df


STRATEGY_NAME = "top_list_matrix"
STRATEGY_DESCRIPTION = "龙虎榜策略矩阵"
SOURCE_TABLES = "stock_stk_factor_pro, stock_top_inst, stock_top_list"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass(frozen=True)
class SignalRuleDef:
    strategy_family: str
    signal_code: str
    description: str
    predicate: str


REASON_GROUP_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("up_deviation", ("涨幅偏离值",)),
    ("down_deviation", ("跌幅偏离值",)),
    ("high_turnover", ("换手率达到",)),
    ("consecutive_move", ("连续三个交易日", "连续三个有价格涨跌幅限制", "连续三个交易日内")),
    ("high_amplitude", ("振幅值达到",)),
)


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


def normalize_reason_flags(reason_series: pd.Series) -> pd.DataFrame:
    filled = reason_series.fillna("")
    flags: dict[str, pd.Series] = {}
    for group_name, patterns in REASON_GROUP_PATTERNS:
        flags[f"reason_{group_name}"] = filled.str.contains("|".join(patterns), regex=True).astype(int)
    return pd.DataFrame(flags, index=reason_series.index)


def _column_or_nan(frame: pd.DataFrame, column: str) -> pd.Series:
    if column in frame.columns:
        return pd.to_numeric(frame[column], errors="coerce")
    return pd.Series(np.nan, index=frame.index, name=column)


def _series_predicate(column: str) -> str:
    return f"{column} > 0"


def _numeric_predicate(column: str, comparator: str, threshold: float) -> str:
    op_map = {
        "ge": ">=",
        "gt": ">",
        "le": "<=",
        "lt": "<",
        "eq": "==",
    }
    if comparator not in op_map:
        raise ValueError(f"Unsupported comparator: {comparator}")
    threshold_literal = str(int(threshold)) if float(threshold).is_integer() else f"{threshold:g}"
    return f"{column} {op_map[comparator]} {threshold_literal}"


def _combine_predicates(*predicates: str) -> str:
    return " & ".join(f"({predicate})" for predicate in predicates if predicate)


def _threshold_token(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}".replace("-", "neg_").replace(".", "p")


def _millions_token(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value / 1_000_000)}m"
    return f"{value / 1_000_000:g}m".replace("-", "neg_").replace(".", "p")


def _seed_code(*parts: str) -> str:
    return "__".join(parts)


def load_base_frame(start_date: str, end_date: str | None) -> pd.DataFrame:
    end_expr = f"AND trade_date <= '{end_date}'" if end_date else ""
    sql = f"""
    SELECT
      ts_code,
      trade_date,
      open_qfq,
      high_qfq,
      low_qfq,
      close_qfq,
      pct_chg,
      amount,
      vol,
      volume_ratio,
      turnover_rate_f,
      boll_lower_qfq,
      rsi_qfq_6,
      ma_qfq_5,
      ma_qfq_20,
      ma_qfq_60
    FROM stock_stk_factor_pro
    WHERE trade_date >= '{start_date}'
      {end_expr}
    ORDER BY trade_date, ts_code
    """
    return query_df(sql)


def load_top_inst_frame(start_date: str, end_date: str | None) -> pd.DataFrame:
    end_expr = f"AND trade_date <= '{end_date}'" if end_date else ""
    sql = f"""
    SELECT
      ts_code,
      trade_date,
      buy,
      buy_rate,
      sell,
      sell_rate,
      net_buy,
      reason
    FROM stock_top_inst
    WHERE trade_date >= '{start_date}'
      {end_expr}
    """
    return query_df(sql)


def load_top_list_frame(start_date: str, end_date: str | None) -> pd.DataFrame:
    end_expr = f"AND trade_date <= '{end_date}'" if end_date else ""
    sql = f"""
    SELECT
      ts_code,
      trade_date,
      net_amount,
      net_rate,
      amount_rate,
      l_buy,
      l_sell,
      l_amount,
      reason
    FROM stock_top_list
    WHERE trade_date >= '{start_date}'
      {end_expr}
    """
    return query_df(sql)


def aggregate_top_inst_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "ts_code",
        "trade_date",
        "inst_buy",
        "inst_sell",
        "inst_net_buy",
        "inst_buy_rate",
        "inst_sell_rate",
        "reason_up_deviation",
        "reason_down_deviation",
        "reason_high_turnover",
        "reason_consecutive_move",
        "reason_high_amplitude",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        frame.groupby(["ts_code", "trade_date"], as_index=False)
        .agg(
            inst_buy=("buy", "sum"),
            inst_sell=("sell", "sum"),
            inst_net_buy=("net_buy", "sum"),
            inst_buy_rate=("buy_rate", "sum"),
            inst_sell_rate=("sell_rate", "sum"),
        )
    )
    flags = normalize_reason_flags(frame["reason"])
    grouped_flags = pd.concat([frame[["ts_code", "trade_date"]], flags], axis=1)
    grouped_flags = grouped_flags.groupby(["ts_code", "trade_date"], as_index=False).max()
    return grouped.merge(grouped_flags, on=["ts_code", "trade_date"], how="left").reindex(columns=columns)


def aggregate_top_list_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "ts_code",
        "trade_date",
        "top_list_net_amount",
        "top_list_net_rate",
        "top_list_amount_rate",
        "top_list_buy",
        "top_list_sell",
        "top_list_amount",
        "top_list_event_count",
        "reason_up_deviation",
        "reason_down_deviation",
        "reason_high_turnover",
        "reason_consecutive_move",
        "reason_high_amplitude",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)

    deduped = (
        frame.sort_values(["ts_code", "trade_date", "reason"])
        .drop_duplicates(["ts_code", "trade_date", "reason"], keep="first")
        .copy()
    )
    grouped = (
        deduped.groupby(["ts_code", "trade_date"], as_index=False)
        .agg(
            top_list_net_amount=("net_amount", "first"),
            top_list_net_rate=("net_rate", "mean"),
            top_list_amount_rate=("amount_rate", "mean"),
            top_list_buy=("l_buy", "first"),
            top_list_sell=("l_sell", "first"),
            top_list_amount=("l_amount", "first"),
            top_list_event_count=("reason", "count"),
        )
    )
    flags = normalize_reason_flags(deduped["reason"])
    grouped_flags = pd.concat([deduped[["ts_code", "trade_date"]], flags], axis=1)
    grouped_flags = grouped_flags.groupby(["ts_code", "trade_date"], as_index=False).max()
    return grouped.merge(grouped_flags, on=["ts_code", "trade_date"], how="left").reindex(columns=columns)


def load_analysis_frame(start_date: str, end_date: str | None) -> pd.DataFrame:
    base_df = load_base_frame(start_date, end_date)
    top_inst_df = aggregate_top_inst_frame(load_top_inst_frame(start_date, end_date))
    top_list_df = aggregate_top_list_frame(load_top_list_frame(start_date, end_date))

    merged = base_df.merge(top_inst_df, on=["ts_code", "trade_date"], how="left", suffixes=("", "_inst"))
    merged = merged.merge(top_list_df, on=["ts_code", "trade_date"], how="left", suffixes=("", "_list"))

    for group_name, _ in REASON_GROUP_PATTERNS:
        column = f"reason_{group_name}"
        list_column = f"{column}_list"
        if list_column in merged.columns:
            if column in merged.columns:
                merged[column] = pd.concat(
                    [
                        pd.to_numeric(merged[column], errors="coerce"),
                        pd.to_numeric(merged[list_column], errors="coerce"),
                    ],
                    axis=1,
                ).max(axis=1)
            else:
                merged[column] = pd.to_numeric(merged[list_column], errors="coerce")
            merged = merged.drop(columns=[list_column])
        if column in merged.columns:
            merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0)

    fill_zero_columns = [column for column in merged.columns if column.startswith(("inst_", "top_list_", "reason_"))]
    for column in fill_zero_columns:
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0.0)
    return merged.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).reset_index(drop=True).copy()
    grouped = result.groupby("ts_code", group_keys=False)

    close_qfq = _column_or_nan(result, "close_qfq")
    if "close_qfq" in result.columns:
        result["ret_1d"] = grouped["close_qfq"].shift(-1) / close_qfq - 1.0
        result["ret_3d"] = grouped["close_qfq"].shift(-3) / close_qfq - 1.0
        rolling_low_120 = grouped["close_qfq"].transform(lambda s: s.rolling(120, min_periods=20).min())
        rolling_high_120 = grouped["close_qfq"].transform(lambda s: s.rolling(120, min_periods=20).max())
        spread = (rolling_high_120 - rolling_low_120).replace(0, np.nan)
        result["pos120"] = ((close_qfq - rolling_low_120) / spread).clip(0, 1)
        result["close_to_low_120"] = close_qfq / rolling_low_120
    else:
        result["ret_1d"] = np.nan
        result["ret_3d"] = np.nan
        result["pos120"] = np.nan
        result["close_to_low_120"] = np.nan

    if "top_list_event_count" in result.columns:
        result["top_list_any"] = pd.to_numeric(result["top_list_event_count"], errors="coerce").fillna(0).gt(0).astype(int)
    else:
        result["top_list_any"] = 0
    result["top_list_count_3d"] = grouped["top_list_any"].transform(lambda s: s.rolling(3, min_periods=1).sum())
    result["top_list_count_5d"] = grouped["top_list_any"].transform(lambda s: s.rolling(5, min_periods=1).sum())
    prev_any = grouped["top_list_any"].shift(1).fillna(0)
    result["top_list_streak_2d"] = ((result["top_list_any"] == 1) & (prev_any == 1)).astype(int)
    result["inst_net_buy_ratio"] = (
        _column_or_nan(result, "inst_net_buy") / _column_or_nan(result, "amount").replace(0, np.nan)
        if "inst_net_buy" in result.columns and "amount" in result.columns
        else np.nan
    )
    result["inst_sell_ratio"] = (
        _column_or_nan(result, "inst_sell") / _column_or_nan(result, "amount").replace(0, np.nan)
        if "inst_sell" in result.columns and "amount" in result.columns
        else np.nan
    )

    for column in ("reason_up_deviation", "reason_down_deviation", "reason_consecutive_move"):
        if column not in result.columns:
            result[column] = 0
    result["consecutive_reason_flag"] = result[
        ["reason_up_deviation", "reason_down_deviation", "reason_consecutive_move"]
    ].max(axis=1)
    if "ma_qfq_5" in result.columns:
        result["ma_reclaim_state"] = (
            (close_qfq >= _column_or_nan(result, "ma_qfq_5"))
            & (grouped["close_qfq"].shift(1) < grouped["ma_qfq_5"].shift(1))
        ).fillna(False).astype(int)
    else:
        result["ma_reclaim_state"] = 0
    if "ma_qfq_20" in result.columns and "ma_qfq_60" in result.columns:
        result["strong_trend_state"] = (
            (close_qfq >= _column_or_nan(result, "ma_qfq_20"))
            & (_column_or_nan(result, "ma_qfq_20") >= _column_or_nan(result, "ma_qfq_60"))
        ).fillna(False).astype(int)
        result["weak_trend_state"] = (
            (close_qfq < _column_or_nan(result, "ma_qfq_20"))
            & (_column_or_nan(result, "ma_qfq_20") < _column_or_nan(result, "ma_qfq_60"))
        ).fillna(False).astype(int)
        result["pullback_state"] = (
            (result["strong_trend_state"] == 1)
            & (_column_or_nan(result, "pct_chg") > -3.0)
            & (close_qfq <= _column_or_nan(result, "ma_qfq_20") * 1.03)
        ).fillna(False).astype(int)
    else:
        result["strong_trend_state"] = 0
        result["weak_trend_state"] = 0
        result["pullback_state"] = 0
    result["volume_expand_state"] = (_column_or_nan(result, "volume_ratio") >= 1.5).fillna(False).astype(int)
    result["high_turnover_state"] = (_column_or_nan(result, "turnover_rate_f") >= 5.0).fillna(False).astype(int)
    result["oversold_state"] = (
        (close_qfq <= _column_or_nan(result, "boll_lower_qfq") * 1.03)
        & (_column_or_nan(result, "rsi_qfq_6") < 35)
    ).fillna(False).astype(int)
    result["bottom_soft"] = (result["pos120"] <= 0.25).fillna(False).astype(int)
    result["bottom_near_low"] = (result["close_to_low_120"] <= 1.08).fillna(False).astype(int)
    result["bottom_oversold"] = result["oversold_state"].astype(int)
    result["bottom_strict"] = ((result["pos120"] <= 0.20) & (result["oversold_state"] == 1)).fillna(False).astype(int)
    if "ma_qfq_20" in result.columns and "ma_qfq_60" in result.columns:
        result["bottom_weak_ma"] = (
            (close_qfq < _column_or_nan(result, "ma_qfq_20"))
            & (close_qfq < _column_or_nan(result, "ma_qfq_60"))
            & (result["bottom_near_low"] == 1)
        ).fillna(False).astype(int)
    else:
        result["bottom_weak_ma"] = 0
    return result


def build_signal_rule_defs() -> list[SignalRuleDef]:
    follow_states = [
        ("strong_trend_state", "强趋势", _series_predicate("strong_trend_state")),
        ("volume_expand_state", "放量", _series_predicate("volume_expand_state")),
        ("top_list_streak_2d", "连续上榜", _series_predicate("top_list_streak_2d")),
    ]
    reversal_states = [
        ("oversold_state", "超跌", _series_predicate("oversold_state")),
        ("pullback_state", "回踩", _series_predicate("pullback_state")),
        ("weak_trend_state", "弱趋势", _series_predicate("weak_trend_state")),
    ]
    bottom_states = [
        ("ma_reclaim_state", "站回均线", _series_predicate("ma_reclaim_state")),
        ("strong_trend_state", "强趋势", _series_predicate("strong_trend_state")),
        ("volume_expand_state", "放量", _series_predicate("volume_expand_state")),
        ("high_turnover_state", "高换手", _series_predicate("high_turnover_state")),
    ]
    bottom_fields = [
        ("bottom_soft", "底部偏软"),
        ("bottom_near_low", "接近低位"),
        ("bottom_oversold", "底部超跌"),
        ("bottom_strict", "严格底部"),
        ("bottom_weak_ma", "弱均线底部"),
    ]

    follow_net_buy_thresholds = [5_000_000.0, 15_000_000.0, 30_000_000.0, 60_000_000.0]
    follow_rate_pairs = [(1.5, 8.0), (1.5, 15.0), (3.0, 8.0), (3.0, 15.0)]
    reversal_net_buy_thresholds = [-5_000_000.0, -15_000_000.0, -30_000_000.0, -60_000_000.0]
    reversal_rate_pairs = [(-1.5, 8.0), (-1.5, 15.0), (-3.0, 8.0), (-3.0, 15.0)]
    bottom_rate_thresholds = [0.5, 1.5]

    plain_follow_rules: list[SignalRuleDef] = []
    for threshold in follow_net_buy_thresholds:
        plain_follow_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_follow_through",
                signal_code=_seed_code("plain_inst_follow_through", f"inst_net_buy_ge_{_millions_token(threshold)}"),
                description=f"机构净买入不低于 {_millions_token(threshold)}",
                predicate=_numeric_predicate("inst_net_buy", "ge", threshold),
            )
        )
    for net_rate_threshold, amount_rate_threshold in follow_rate_pairs:
        plain_follow_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_follow_through",
                signal_code=_seed_code(
                    "plain_inst_follow_through",
                    f"reason_up_deviation__top_list_net_rate_ge_{_threshold_token(net_rate_threshold)}",
                    f"top_list_amount_rate_ge_{_threshold_token(amount_rate_threshold)}",
                ),
                description="涨幅异动上榜且榜单净买入与成交占比同步走强",
                predicate=_combine_predicates(
                    _series_predicate("reason_up_deviation"),
                    _numeric_predicate("top_list_net_rate", "ge", net_rate_threshold),
                    _numeric_predicate("top_list_amount_rate", "ge", amount_rate_threshold),
                ),
            )
        )
    for days in [2, 3]:
        plain_follow_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_follow_through",
                signal_code=_seed_code("plain_inst_follow_through", f"top_list_count_3d_ge_{days}"),
                description=f"近 3 日上榜次数不少于 {days}",
                predicate=_numeric_predicate("top_list_count_3d", "ge", days),
            )
        )

    plain_reversal_rules: list[SignalRuleDef] = []
    for threshold in reversal_net_buy_thresholds:
        plain_reversal_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_reversal_rebound",
                signal_code=_seed_code("plain_inst_reversal_rebound", f"inst_net_buy_le_{_millions_token(abs(threshold))}"),
                description=f"机构净卖出不低于 {_millions_token(abs(threshold))}",
                predicate=_numeric_predicate("inst_net_buy", "le", threshold),
            )
        )
    for net_rate_threshold, amount_rate_threshold in reversal_rate_pairs:
        plain_reversal_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_reversal_rebound",
                signal_code=_seed_code(
                    "plain_inst_reversal_rebound",
                    f"reason_down_deviation__top_list_net_rate_le_{_threshold_token(abs(net_rate_threshold))}",
                    f"top_list_amount_rate_ge_{_threshold_token(amount_rate_threshold)}",
                ),
                description="跌幅异动上榜且榜单净买入明显转负",
                predicate=_combine_predicates(
                    _series_predicate("reason_down_deviation"),
                    _numeric_predicate("top_list_net_rate", "le", net_rate_threshold),
                    _numeric_predicate("top_list_amount_rate", "ge", amount_rate_threshold),
                ),
            )
        )
    for days in [2, 3]:
        plain_reversal_rules.append(
            SignalRuleDef(
                strategy_family="plain_inst_reversal_rebound",
                signal_code=_seed_code("plain_inst_reversal_rebound", f"top_list_count_5d_ge_{days}"),
                description=f"近 5 日上榜次数不少于 {days}",
                predicate=_numeric_predicate("top_list_count_5d", "ge", days),
            )
        )

    plain_bottom_rules: list[SignalRuleDef] = []
    for field, description in bottom_fields:
        for threshold in bottom_rate_thresholds:
            plain_bottom_rules.append(
                SignalRuleDef(
                    strategy_family="plain_bottom_absorption",
                    signal_code=_seed_code(
                        "plain_bottom_absorption",
                        field,
                        f"top_list_net_rate_ge_{_threshold_token(threshold)}",
                    ),
                    description=f"{description} 且榜单净买入占比不低于 {threshold:g}",
                    predicate=_combine_predicates(
                        _series_predicate(field),
                        _numeric_predicate("top_list_net_rate", "ge", threshold),
                    ),
                )
            )
    plain_bottom_rules.extend(
        [
            SignalRuleDef(
                strategy_family="plain_bottom_absorption",
                signal_code=_seed_code("plain_bottom_absorption", "bottom_soft", "top_list_count_3d_ge_2"),
                description="底部偏软且近 3 日持续上榜",
                predicate=_combine_predicates(
                    _series_predicate("bottom_soft"),
                    _numeric_predicate("top_list_count_3d", "ge", 2),
                ),
            ),
            SignalRuleDef(
                strategy_family="plain_bottom_absorption",
                signal_code=_seed_code("plain_bottom_absorption", "bottom_strict", "top_list_count_3d_ge_3"),
                description="严格底部且近 3 日持续上榜",
                predicate=_combine_predicates(
                    _series_predicate("bottom_strict"),
                    _numeric_predicate("top_list_count_3d", "ge", 3),
                ),
            ),
        ]
    )

    def expand_state_rules(
        family: str,
        seeds: list[SignalRuleDef],
        state_defs: list[tuple[str, str, str]],
    ) -> list[SignalRuleDef]:
        expanded: list[SignalRuleDef] = []
        for seed in seeds:
            for state_code, state_description, state_predicate in state_defs:
                expanded.append(
                    SignalRuleDef(
                        strategy_family=family,
                        signal_code=_seed_code(family, seed.signal_code.split("__", 1)[1], state_code),
                        description=f"{seed.description}，{state_description}",
                        predicate=_combine_predicates(seed.predicate, state_predicate),
                    )
                )
        return expanded

    rules: list[SignalRuleDef] = [*plain_follow_rules, *plain_reversal_rules, *plain_bottom_rules]
    rules.extend(expand_state_rules("state_inst_follow_through", plain_follow_rules, follow_states))
    rules.extend(expand_state_rules("state_inst_reversal_rebound", plain_reversal_rules, reversal_states))
    rules.extend(expand_state_rules("state_bottom_absorption", plain_bottom_rules, bottom_states))

    deduped: dict[str, SignalRuleDef] = {}
    for rule in rules:
        deduped.setdefault(rule.signal_code, rule)
    return list(deduped.values())


def _series_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.mean())


def _series_variance(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.var())


def _series_win_rate(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float((numeric > 0).mean())


def summarize_signal_matrix(
    features_df: pd.DataFrame,
    rule_defs: list[SignalRuleDef] | None = None,
    *,
    min_sample: int,
    show_progress: bool = False,
) -> pd.DataFrame:
    rules = build_signal_rule_defs() if rule_defs is None else rule_defs
    latest_trade_date = str(features_df["trade_date"].max()) if not features_df.empty else ""
    rows: list[dict[str, object]] = []
    iterator = tqdm(rules, desc="Scanning strategies", disable=not show_progress)
    for rule in iterator:
        matched = features_df.query(rule.predicate, engine="python")
        if matched.empty:
            continue
        latest_hits = matched.loc[matched["trade_date"] == latest_trade_date, "ts_code"].drop_duplicates().tolist()
        rows.append(
            {
                "strategy_family": rule.strategy_family,
                "signal_code": rule.signal_code,
                "sample_count": int(len(matched)),
                "win_rate_1d": _series_win_rate(matched["ret_1d"]),
                "avg_ret_1d": _series_mean(matched["ret_1d"]),
                "var_ret_1d": _series_variance(matched["ret_1d"]),
                "win_rate_3d": _series_win_rate(matched["ret_3d"]),
                "avg_ret_3d": _series_mean(matched["ret_3d"]),
                "var_ret_3d": _series_variance(matched["ret_3d"]),
                "latest_trade_date": latest_trade_date,
                "latest_hit_stocks": ",".join(sorted(latest_hits)),
                "is_low_sample": int(len(matched) < min_sample),
            }
        )
    compact_df = pd.DataFrame(rows)
    if compact_df.empty:
        return pd.DataFrame(
            columns=[
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
                "is_low_sample",
            ]
        )
    return compact_df.sort_values(
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
    ).reset_index(drop=True)


def build_signal_code_markdown(rule_defs: list[SignalRuleDef]) -> str:
    lines = [
        "# Top List Matrix Signal Codes",
        "",
        "| family | signal_code | description |",
        "| --- | --- | --- |",
    ]
    for rule in sorted(rule_defs, key=lambda item: (item.strategy_family, item.signal_code)):
        lines.append(f"| {rule.strategy_family} | {rule.signal_code} | {rule.description} |")
    return "\n".join(lines)


def _build_output_stem(now: datetime | None = None) -> str:
    current = now or datetime.now()
    return current.strftime("%m%d_%H%M")


def write_outputs(
    compact_df: pd.DataFrame,
    markdown_text: str,
    *,
    output_dir: Path,
    now: datetime | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _build_output_stem(now)
    summary_csv = output_dir / f"{stem}.csv"
    summary_md = output_dir / f"{stem}.md"

    compact_df.to_csv(summary_csv, index=False)
    summary_md.write_text(markdown_text, encoding="utf-8")
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
    print("==> load_analysis_frame", flush=True)
    merged_df = load_analysis_frame(start_date, end_date)
    loaded_start = str(merged_df["trade_date"].min()) if not merged_df.empty else ""
    loaded_end = str(merged_df["trade_date"].max()) if not merged_df.empty else ""
    loaded_stocks = int(merged_df["ts_code"].nunique()) if not merged_df.empty else 0
    print(
        f"==> load_analysis_frame done | loaded_rows={len(merged_df)} | "
        f"loaded_stocks={loaded_stocks} | date_range={loaded_start} -> {loaded_end}",
        flush=True,
    )

    print("==> build_features", flush=True)
    featured_df = build_features(merged_df)
    analysis_df = featured_df.loc[featured_df["trade_date"] <= end_date].copy() if end_date else featured_df.copy()

    rule_defs = build_signal_rule_defs()
    print("==> Scanning strategies", flush=True)
    compact_df = summarize_signal_matrix(
        analysis_df,
        rule_defs,
        min_sample=min_sample,
        show_progress=show_progress,
    )

    print("==> build_signal_code_markdown", flush=True)
    markdown_text = build_signal_code_markdown(rule_defs)
    print("==> write_outputs", flush=True)
    output_paths = write_outputs(compact_df, markdown_text, output_dir=output_dir)
    return {
        "source_df": merged_df,
        "merged_df": merged_df,
        "featured_df": featured_df,
        "compact_df": compact_df,
        "output_paths": output_paths,
        "rule_defs": rule_defs,
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
