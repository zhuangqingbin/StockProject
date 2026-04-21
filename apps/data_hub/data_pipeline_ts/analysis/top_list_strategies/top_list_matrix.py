from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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
    predicate: Callable[[pd.DataFrame], pd.Series]


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

    grouped = (
        frame.groupby(["ts_code", "trade_date"], as_index=False)
        .agg(
            top_list_net_amount=("net_amount", "sum"),
            top_list_net_rate=("net_rate", "mean"),
            top_list_amount_rate=("amount_rate", "mean"),
            top_list_buy=("l_buy", "sum"),
            top_list_sell=("l_sell", "sum"),
            top_list_amount=("l_amount", "sum"),
            top_list_event_count=("reason", "count"),
        )
    )
    flags = normalize_reason_flags(frame["reason"])
    grouped_flags = pd.concat([frame[["ts_code", "trade_date"]], flags], axis=1)
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

    numeric_cols = merged.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        merged[numeric_cols] = merged[numeric_cols].fillna(0.0)
    return merged.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).reset_index(drop=True).copy()
    grouped = result.groupby("ts_code", group_keys=False)

    result["ret_1d"] = grouped["close_qfq"].shift(-1) / result["close_qfq"] - 1.0
    result["ret_3d"] = grouped["close_qfq"].shift(-3) / result["close_qfq"] - 1.0
    result["top_list_any"] = (result["top_list_event_count"] > 0).astype(int)
    result["top_list_count_3d"] = grouped["top_list_any"].transform(lambda s: s.rolling(3, min_periods=1).sum())
    result["top_list_count_5d"] = grouped["top_list_any"].transform(lambda s: s.rolling(5, min_periods=1).sum())
    prev_any = grouped["top_list_any"].shift(1).fillna(0)
    result["top_list_streak_2d"] = ((result["top_list_any"] == 1) & (prev_any == 1)).astype(int)

    for column in ("reason_up_deviation", "reason_down_deviation", "reason_consecutive_move"):
        if column not in result.columns:
            result[column] = 0
    result["consecutive_reason_flag"] = result[
        ["reason_up_deviation", "reason_down_deviation", "reason_consecutive_move"]
    ].max(axis=1)
    return result


def run_analysis(
    *,
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
    show_progress: bool = False,
) -> dict[str, Any]:
    return {
        "compact_df": pd.DataFrame(),
        "output_paths": {
            "summary_csv": output_dir / "placeholder.csv",
            "summary_md": output_dir / "placeholder.md",
        },
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
