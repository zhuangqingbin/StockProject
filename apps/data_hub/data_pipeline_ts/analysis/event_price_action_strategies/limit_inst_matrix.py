from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df


STRATEGY_NAME = "limit_inst_matrix"
STRATEGY_DESCRIPTION = "涨跌停 + 龙虎榜事件矩阵"
SOURCE_TABLES = "stock_stk_factor_pro, stock_limit_list_d, stock_top_inst"
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


def _frame_effective_end_date(*frames: pd.DataFrame) -> str | None:
    for frame in frames:
        if not frame.empty and "trade_date" in frame.columns:
            valid_dates = frame["trade_date"].dropna()
            if not valid_dates.empty:
                return str(valid_dates.max())
    return None


def _frame_effective_start_date(*frames: pd.DataFrame) -> str | None:
    for frame in frames:
        if not frame.empty and "trade_date" in frame.columns:
            valid_dates = frame["trade_date"].dropna()
            if not valid_dates.empty:
                return str(valid_dates.min())
    return None


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
        series = df[column]
        if comparator == "ge":
            return series.ge(threshold) & series.notna()
        if comparator == "gt":
            return series.gt(threshold) & series.notna()
        if comparator == "le":
            return series.le(threshold) & series.notna()
        if comparator == "lt":
            return series.lt(threshold) & series.notna()
        raise ValueError(comparator)

    return predicate


def _combine_predicates(
    *predicates: Callable[[pd.DataFrame], pd.Series],
) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(df: pd.DataFrame) -> pd.Series:
        combined = pd.Series(True, index=df.index, dtype=bool)
        for item in predicates:
            combined = combined & item(df).fillna(False).astype(bool)
        return combined

    return predicate


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


def load_limit_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        `limit` AS limit_type,
        open_times,
        fd_amount,
        limit_times
    FROM stock_limit_list_d
    WHERE trade_date >= :start_date
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"
    columns = ["ts_code", "trade_date", "limit_type", "open_times", "fd_amount", "limit_times"]
    frame = query_df(sql, params)
    return frame.reindex(columns=columns) if not frame.empty else _empty_frame(columns)


def load_top_inst_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        SUM(CASE WHEN side = '0' THEN buy ELSE 0 END) AS inst_buy,
        SUM(CASE WHEN side = '1' THEN sell ELSE 0 END) AS inst_sell,
        SUM(net_buy) AS inst_net_buy
    FROM stock_top_inst
    WHERE trade_date >= :start_date
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    GROUP BY ts_code, trade_date\n    ORDER BY ts_code, trade_date"
    columns = ["ts_code", "trade_date", "inst_buy", "inst_sell", "inst_net_buy"]
    frame = query_df(sql, params)
    return frame.reindex(columns=columns) if not frame.empty else _empty_frame(columns)


def merge_side_frames(
    base_df: pd.DataFrame,
    limit_df: pd.DataFrame,
    top_inst_df: pd.DataFrame,
) -> pd.DataFrame:
    result = base_df.copy()
    for side_df in (limit_df, top_inst_df):
        result = result.merge(side_df, on=["ts_code", "trade_date"], how="left")
    return result


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).copy()
    grouped = result.groupby("ts_code", sort=False)

    result["ret_1d"] = grouped["close_qfq"].shift(-1) / result["close_qfq"] - 1
    result["ret_3d"] = grouped["close_qfq"].shift(-3) / result["close_qfq"] - 1
    result["rolling_low_120"] = grouped["low_qfq"].transform(lambda s: s.rolling(120, min_periods=1).min())
    result["rolling_high_120"] = grouped["high_qfq"].transform(lambda s: s.rolling(120, min_periods=1).max())
    result["pos120"] = _safe_divide(
        result["close_qfq"] - result["rolling_low_120"],
        result["rolling_high_120"] - result["rolling_low_120"],
    )
    result["close_to_low_120"] = _safe_divide(result["close_qfq"], result["rolling_low_120"])
    result["is_bottom_zone"] = (
        (result["pos120"] <= 0.25)
        | (result["close_to_low_120"] <= 1.08)
        | ((result["close_qfq"] <= result["boll_lower_qfq"] * 1.03) & (result["rsi_qfq_6"] < 35))
    ).fillna(False)

    result["is_limit_up"] = result["limit_type"].eq("U").fillna(False)
    result["is_limit_down"] = result["limit_type"].eq("D").fillna(False)
    result["is_open_board"] = result["is_limit_up"] & result["open_times"].fillna(0).gt(0)
    result["is_one_word_board"] = result["is_limit_up"] & result["open_times"].fillna(0).eq(0)
    result["is_limit_up_first"] = result["is_limit_up"] & result["limit_times"].fillna(0).eq(1)
    result["is_limit_up_multi"] = result["is_limit_up"] & result["limit_times"].fillna(0).ge(2)

    result["inst_net_buy_ratio"] = _safe_divide(result["inst_net_buy"], result["amount"])
    result["inst_gross_turnover_ratio"] = _safe_divide(
        result["inst_buy"].fillna(0) + result["inst_sell"].fillna(0),
        result["amount"],
    )
    result["inst_abs_buy_sell_ratio"] = result["inst_gross_turnover_ratio"]

    result["oversold_state"] = (
        (result["close_qfq"] <= result["boll_lower_qfq"] * 1.03)
        & (result["rsi_qfq_6"] < 35)
    ).fillna(False)
    result["volume_expand_state"] = result["volume_ratio"].ge(1.5).fillna(False)
    result["high_turnover_state"] = result["turnover_rate_f"].ge(3.0).fillna(False)
    result["ma_reclaim_state"] = (
        result["close_qfq"].ge(result["ma_qfq_5"])
        & grouped["close_qfq"].shift(1).lt(grouped["ma_qfq_5"].shift(1))
    ).fillna(False)
    result["weak_trend_state"] = (
        result["close_qfq"].lt(result["ma_qfq_20"])
        & result["close_qfq"].lt(result["ma_qfq_60"])
    ).fillna(False)
    result["strong_trend_state"] = (
        result["close_qfq"].ge(result["ma_qfq_20"])
        & result["ma_qfq_20"].ge(result["ma_qfq_60"])
    ).fillna(False)
    result["pullback_state"] = (
        result["strong_trend_state"] & result["close_qfq"].le(result["ma_qfq_20"] * 1.02)
    ).fillna(False)
    return result


def build_signal_rule_defs() -> list[SignalRuleDef]:
    momentum_events = [
        SignalRuleDef(
            "plain_momentum_event",
            "plain_momentum_event__limit_up_first",
            "首板涨停",
            _series_predicate("is_limit_up_first"),
        ),
        SignalRuleDef(
            "plain_momentum_event",
            "plain_momentum_event__limit_up_multi",
            "连板涨停",
            _series_predicate("is_limit_up_multi"),
        ),
        SignalRuleDef(
            "plain_momentum_event",
            "plain_momentum_event__limit_up_one_word",
            "一字板",
            _series_predicate("is_one_word_board"),
        ),
        SignalRuleDef(
            "plain_momentum_event",
            "plain_momentum_event__limit_up_open_board",
            "涨停开板",
            _series_predicate("is_open_board"),
        ),
    ]

    reversal_events = [
        SignalRuleDef(
            "plain_reversal_event",
            "plain_reversal_event__limit_down",
            "跌停",
            _series_predicate("is_limit_down"),
        ),
    ]
    for open_times in [1, 2, 3]:
        reversal_events.append(
            SignalRuleDef(
                "plain_reversal_event",
                f"plain_reversal_event__open_board_ge_{open_times}",
                f"涨停开板次数 >= {open_times}",
                _combine_predicates(
                    _series_predicate("is_limit_up"),
                    _series_predicate("is_open_board"),
                    _numeric_predicate("open_times", "ge", open_times),
                ),
            )
        )
    for fd_amount in [2e7, 5e7, 1e8]:
        reversal_events.append(
            SignalRuleDef(
                "plain_reversal_event",
                f"plain_reversal_event__fd_amount_ge_{int(fd_amount)}",
                f"开板涨停封单金额 >= {int(fd_amount)}",
                _combine_predicates(
                    _series_predicate("is_limit_up"),
                    _series_predicate("is_open_board"),
                    _numeric_predicate("fd_amount", "ge", fd_amount),
                ),
            )
        )

    inst_events: list[SignalRuleDef] = []
    for threshold in [0, 2e7, 5e7, 1e8]:
        inst_events.append(
            SignalRuleDef(
                "plain_inst_event",
                f"plain_inst_event__inst_net_buy_ge_{int(threshold)}",
                f"机构净买入 >= {int(threshold)}",
                _numeric_predicate("inst_net_buy", "ge", threshold),
            )
        )
    for threshold in [-2e7, -5e7, -1e8]:
        inst_events.append(
            SignalRuleDef(
                "plain_inst_event",
                f"plain_inst_event__inst_net_buy_le_{int(threshold)}",
                f"机构净买入 <= {int(threshold)}",
                _numeric_predicate("inst_net_buy", "le", threshold),
            )
        )

    family_map = {
        "plain_momentum_event": "state_momentum_event",
        "plain_reversal_event": "state_reversal_event",
        "plain_inst_event": "state_inst_event",
    }
    state_templates = {
        "state_momentum_event": [
            ("bottom_zone", _series_predicate("is_bottom_zone"), "底部区"),
            ("volume_expand", _series_predicate("volume_expand_state"), "放量"),
            ("high_turnover", _series_predicate("high_turnover_state"), "高换手"),
            ("ma_reclaim", _series_predicate("ma_reclaim_state"), "站回5日线"),
            ("strong_trend", _series_predicate("strong_trend_state"), "强趋势"),
        ],
        "state_reversal_event": [
            ("bottom_zone", _series_predicate("is_bottom_zone"), "底部区"),
            ("oversold", _series_predicate("oversold_state"), "超跌"),
            ("volume_expand", _series_predicate("volume_expand_state"), "放量"),
            ("high_turnover", _series_predicate("high_turnover_state"), "高换手"),
            ("weak_trend", _series_predicate("weak_trend_state"), "弱趋势"),
            ("pullback_state", _series_predicate("pullback_state"), "回踩状态"),
        ],
        "state_inst_event": [
            ("bottom_zone", _series_predicate("is_bottom_zone"), "底部区"),
            ("oversold", _series_predicate("oversold_state"), "超跌"),
            ("volume_expand", _series_predicate("volume_expand_state"), "放量"),
            ("high_turnover", _series_predicate("high_turnover_state"), "高换手"),
            ("ma_reclaim", _series_predicate("ma_reclaim_state"), "站回5日线"),
            ("strong_trend", _series_predicate("strong_trend_state"), "强趋势"),
            ("weak_trend", _series_predicate("weak_trend_state"), "弱趋势"),
        ],
    }

    state_rules: list[SignalRuleDef] = []
    for base_rule in [*momentum_events, *reversal_events, *inst_events]:
        target_family = family_map[base_rule.family]
        for state_code, state_predicate, state_desc in state_templates[target_family]:
            state_rules.append(
                SignalRuleDef(
                    family=target_family,
                    code=f"{target_family}__{base_rule.code.split('__', 1)[1]}__{state_code}",
                    description=f"{base_rule.description} and {state_desc}",
                    predicate=_combine_predicates(base_rule.predicate, state_predicate),
                )
            )

    return [*momentum_events, *reversal_events, *inst_events, *state_rules]


def _series_mean(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.mean()) if not valid.empty else float("nan")


def _series_variance(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.var()) if len(valid) >= 2 else float("nan")


def _series_win_rate(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.gt(0).mean()) if not valid.empty else float("nan")


def _project_existing_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame[[column for column in columns if column in frame.columns]].copy()


def summarize_signal_matrix(
    frame: pd.DataFrame,
    rule_defs: list[SignalRuleDef] | None = None,
    min_sample: int = 30,
    show_progress: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    from tqdm import tqdm

    rule_defs = rule_defs or build_signal_rule_defs()
    summary_rows: list[dict[str, object]] = []
    trigger_frames: list[pd.DataFrame] = []
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
    progress_bar = tqdm(total=len(rule_defs), desc="Scanning strategies", unit="combo") if show_progress else None
    try:
        for rule in rule_defs:
            signal_mask = rule.predicate(frame).fillna(False).astype(bool)
            triggered = frame.loc[signal_mask].copy()
            if not triggered.empty:
                triggered["strategy_family"] = rule.family
                triggered["signal_code"] = rule.code
                trigger_frames.append(_project_existing_columns(triggered, trigger_columns))
                summary_rows.append(
                    {
                        "strategy_family": rule.family,
                        "signal_code": rule.code,
                        "sample_count": int(len(triggered)),
                        "win_rate_1d": _series_win_rate(triggered["ret_1d"]),
                        "avg_ret_1d": _series_mean(triggered["ret_1d"]),
                        "var_ret_1d": _series_variance(triggered["ret_1d"]),
                        "win_rate_3d": _series_win_rate(triggered["ret_3d"]),
                        "avg_ret_3d": _series_mean(triggered["ret_3d"]),
                        "var_ret_3d": _series_variance(triggered["ret_3d"]),
                    }
                )
            if progress_bar is not None:
                progress_bar.update(1)
    finally:
        if progress_bar is not None:
            progress_bar.close()

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
    summary_df = pd.DataFrame(summary_rows)
    if summary_df.empty:
        summary_df = pd.DataFrame(columns=summary_columns)
    else:
        summary_df["is_low_sample"] = summary_df["sample_count"] < min_sample
        summary_df = summary_df[summary_columns]

    trigger_df = pd.concat(trigger_frames, ignore_index=True) if trigger_frames else pd.DataFrame(columns=trigger_columns)
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
        return pd.DataFrame(columns=columns)

    result = summary_df.copy()
    if trigger_df.empty:
        latest_trade_date = ""
        latest_hit_map: dict[str, str] = {}
    else:
        latest_trade_date = str(trigger_df["trade_date"].max())
        latest_hits = (
            trigger_df.loc[trigger_df["trade_date"] == latest_trade_date, ["signal_code", "ts_code"]]
            .drop_duplicates()
            .sort_values(["signal_code", "ts_code"])
        )
        latest_hit_map = (
            latest_hits.groupby("signal_code", sort=False)["ts_code"]
            .apply(lambda series: ",".join(series.astype(str)))
            .to_dict()
        )

    result["latest_trade_date"] = latest_trade_date
    result["latest_hit_stocks"] = result["signal_code"].map(latest_hit_map).fillna("")
    result = result.sort_values(
        ["win_rate_1d", "avg_ret_1d", "win_rate_3d", "avg_ret_3d", "sample_count", "signal_code"],
        ascending=[False, False, False, False, False, True],
        na_position="last",
    ).reset_index(drop=True)
    return result[columns]


def build_signal_code_markdown(rule_defs: list[SignalRuleDef]) -> str:
    lines = ["## Signal Codes", ""]
    for rule in sorted(rule_defs, key=lambda item: (item.family, item.code)):
        lines.append(f"- `{rule.code}` | family=`{rule.family}` | {rule.description}")
    return "\n".join(lines).rstrip()


def _build_output_stem() -> str:
    return datetime.now().strftime("%m%d_%H%M")


def write_outputs(compact_df: pd.DataFrame, signal_code_markdown: str, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_stem = _build_output_stem()
    summary_csv = output_dir / f"{output_stem}.csv"
    summary_md = output_dir / f"{output_stem}.md"
    compact_df.to_csv(summary_csv, index=False)
    summary_md.write_text(signal_code_markdown, encoding="utf-8")
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
    limit_df = load_limit_frame(start_date=start_date, end_date=end_date)
    top_inst_df = load_top_inst_frame(start_date=start_date, end_date=end_date)
    merged_df = merge_side_frames(base_df, limit_df, top_inst_df)
    effective_start_date = _frame_effective_start_date(merged_df, base_df) or start_date
    effective_end_date = _frame_effective_end_date(merged_df, base_df)
    loaded_stocks = int(base_df["ts_code"].nunique()) if "ts_code" in base_df.columns else 0
    date_range = _format_date_range(effective_start_date, effective_end_date)
    print(
        f"==> load_base_frame done | loaded_rows={len(base_df)} | loaded_stocks={loaded_stocks} | date_range={date_range}",
        flush=True,
    )

    print("==> build_features", flush=True)
    featured_df = build_features(merged_df)
    analysis_df = featured_df.loc[featured_df["trade_date"] <= end_date].copy() if end_date else featured_df.copy()

    rule_defs = build_signal_rule_defs()
    print("==> Scanning strategies", flush=True)
    summary_df, trigger_df = summarize_signal_matrix(
        analysis_df,
        rule_defs=rule_defs,
        min_sample=min_sample,
        show_progress=show_progress,
    )

    compact_df = build_compact_summary(summary_df, trigger_df)
    signal_code_markdown = build_signal_code_markdown(rule_defs)

    print("==> write_outputs", flush=True)
    output_paths = write_outputs(
        compact_df=compact_df,
        signal_code_markdown=signal_code_markdown,
        output_dir=output_dir,
    )
    return {
        "source_df": base_df,
        "base_df": base_df,
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
