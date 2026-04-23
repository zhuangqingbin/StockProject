from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from tqdm import tqdm

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df

STRATEGY_NAME = "flow_chip_northbound_matrix"
STRATEGY_DESCRIPTION = "资金流 + 筹码 + 北向策略矩阵"
SOURCE_TABLES = "stock_stk_factor_pro, stock_money_flow, stock_cyq_perf, stock_hk_hold"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass(frozen=True)
class SignalRuleDef:
    family: str
    code: str
    description: str
    predicate: Callable[[pd.DataFrame], pd.Series]


def _format_date_range(start_date: str, end_date: str | None) -> str:
    return f"{start_date} -> {end_date or 'latest'}"


def _load_end_date(end_date: str | None) -> str | None:
    if end_date is None:
        return None
    return (datetime.strptime(end_date, "%Y%m%d") + timedelta(days=10)).strftime("%Y%m%d")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = pd.Series(float("nan"), index=numerator.index, dtype="float64")
    valid = denominator.notna() & (denominator != 0)
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result


def _series_mean(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.mean()) if not valid.empty else float("nan")


def _series_median(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.median()) if not valid.empty else float("nan")


def _series_variance(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.var()) if len(valid) >= 2 else float("nan")


def _series_win_rate(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.gt(0).mean()) if not valid.empty else float("nan")


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _format_threshold_value(value: float | int) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}".replace("-", "neg").replace(".", "p")


def _format_threshold_text(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:g}"


def _threshold_predicate(field: str, comparator: str, threshold: float | int) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(frame: pd.DataFrame) -> pd.Series:
        if field not in frame.columns:
            return pd.Series(False, index=frame.index, dtype=bool)
        series = frame[field]
        if comparator == "gt":
            return series.gt(threshold) & series.notna()
        if comparator == "ge":
            return series.ge(threshold) & series.notna()
        if comparator == "lt":
            return series.lt(threshold) & series.notna()
        if comparator == "le":
            return series.le(threshold) & series.notna()
        raise ValueError(f"Unsupported comparator: {comparator}")

    return predicate


def _bottom_zone_predicate(frame: pd.DataFrame) -> pd.Series:
    if "is_bottom_zone" not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    return frame["is_bottom_zone"].fillna(False).astype(bool)


def _combine_predicates(*predicates: Callable[[pd.DataFrame], pd.Series]) -> Callable[[pd.DataFrame], pd.Series]:
    def predicate(frame: pd.DataFrame) -> pd.Series:
        if not predicates:
            return pd.Series(True, index=frame.index, dtype=bool)
        combined = predicates[0](frame).fillna(False).astype(bool)
        for item in predicates[1:]:
            combined = combined & item(frame).fillna(False).astype(bool)
        return combined

    return predicate


def _project_existing_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame[[column for column in columns if column in frame.columns]].copy()


def _build_atomic_rules(
    family: str,
    specs: list[tuple[str, str, list[float | int]]],
) -> list[SignalRuleDef]:
    rules: list[SignalRuleDef] = []
    for field, comparator, thresholds in specs:
        for threshold in thresholds:
            code = f"{family}__{field}_{comparator}_{_format_threshold_value(threshold)}"
            description = f"{field} {comparator} {_format_threshold_text(threshold)}"
            rules.append(
                SignalRuleDef(
                    family=family,
                    code=code,
                    description=description,
                    predicate=_threshold_predicate(field, comparator, threshold),
                )
            )
    return rules


def _build_composite_rules(
    family: str,
    group_a: list[SignalRuleDef],
    group_b: list[SignalRuleDef],
    *,
    extra_group: list[SignalRuleDef] | None = None,
) -> list[SignalRuleDef]:
    rules: list[SignalRuleDef] = []
    if extra_group is None:
        for left, right in product(group_a, group_b):
            code = f"{family}__{left.code}__{right.code}"
            description = f"{left.description} and {right.description}"
            rules.append(
                SignalRuleDef(
                    family=family,
                    code=code,
                    description=description,
                    predicate=_combine_predicates(left.predicate, right.predicate),
                )
            )
        return rules

    for left, middle, right in product(group_a, group_b, extra_group):
        code = f"{family}__{left.code}__{middle.code}__{right.code}"
        description = f"{left.description} and {middle.description} and {right.description}"
        rules.append(
            SignalRuleDef(
                family=family,
                code=code,
                description=description,
                predicate=_combine_predicates(left.predicate, middle.predicate, right.predicate),
            )
        )
    return rules


def build_signal_rule_defs() -> list[SignalRuleDef]:
    plain_main_flow = _build_atomic_rules(
        "plain_main_flow",
        [
            ("main_net_ratio", "gt", [0.02, 0.04, 0.06, 0.08]),
            ("elg_net_ratio", "gt", [0.01, 0.02, 0.04, 0.06]),
            ("mf_net_ratio", "gt", [0.01, 0.02, 0.04, 0.06]),
            ("main_net_change_3d", "gt", [0.0, 0.2, 0.5, 1.0]),
        ],
    )
    plain_chip_repair = _build_atomic_rules(
        "plain_chip_repair",
        [
            ("winner_rate", "lt", [35, 30, 25, 20]),
            ("winner_rate_change_3d", "ge", [1, 2, 3, 4]),
            ("chip_spread", "le", [0.22, 0.18, 0.15, 0.12]),
            ("close_vs_weight_avg", "ge", [1.00, 1.02, 1.05, 1.08]),
        ],
    )
    plain_northbound_support = _build_atomic_rules(
        "plain_northbound_support",
        [
            ("hk_ratio", "ge", [0.1, 0.3, 0.5, 1.0]),
            ("hk_ratio_change_3d", "ge", [0.0, 0.1, 0.2, 0.3]),
            ("hk_vol_change_3d", "ge", [0, 5, 10, 20]),
        ],
    )

    bottom_main_flow = [
        SignalRuleDef(
            family="bottom_main_flow",
            code=f"bottom_main_flow__{rule.code}",
            description=f"is_bottom_zone and {rule.description}",
            predicate=_combine_predicates(_bottom_zone_predicate, rule.predicate),
        )
        for rule in plain_main_flow
    ]
    bottom_chip_repair = [
        SignalRuleDef(
            family="bottom_chip_repair",
            code=f"bottom_chip_repair__{rule.code}",
            description=f"is_bottom_zone and {rule.description}",
            predicate=_combine_predicates(_bottom_zone_predicate, rule.predicate),
        )
        for rule in plain_chip_repair
    ]
    bottom_northbound_support = [
        SignalRuleDef(
            family="bottom_northbound_support",
            code=f"bottom_northbound_support__{rule.code}",
            description=f"is_bottom_zone and {rule.description}",
            predicate=_combine_predicates(_bottom_zone_predicate, rule.predicate),
        )
        for rule in plain_northbound_support
    ]

    plain_resonance = _build_composite_rules(
        "plain_resonance",
        plain_main_flow[:12],
        plain_chip_repair[:6],
    )
    bottom_resonance = _build_composite_rules(
        "bottom_resonance",
        bottom_main_flow[:6],
        bottom_chip_repair[:6],
        extra_group=bottom_northbound_support[:2],
    )

    return [
        *plain_main_flow,
        *bottom_main_flow,
        *plain_chip_repair,
        *bottom_chip_repair,
        *plain_northbound_support,
        *bottom_northbound_support,
        *plain_resonance,
        *bottom_resonance,
    ]


def summarize_signal_matrix(
    frame: pd.DataFrame,
    rule_defs: list[SignalRuleDef] | None = None,
    min_sample: int = 30,
    show_progress: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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
            if triggered.empty:
                if progress_bar is not None:
                    progress_bar.update(1)
                continue
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
    ]
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows).sort_values(
            ["win_rate_1d", "avg_ret_1d", "win_rate_3d", "avg_ret_3d", "sample_count", "signal_code"],
            ascending=[False, False, False, False, False, True],
            na_position="last",
        )
        summary_df["is_low_sample"] = summary_df["sample_count"] < min_sample
    else:
        summary_df = pd.DataFrame(columns=[*summary_columns, "is_low_sample"])

    trigger_df = pd.concat(trigger_frames, ignore_index=True) if trigger_frames else pd.DataFrame(columns=trigger_columns)
    return summary_df.reset_index(drop=True), trigger_df


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
            .dropna(subset=["signal_code", "ts_code"])
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
    return result[columns]


def build_signal_code_markdown(rule_defs: list[SignalRuleDef]) -> str:
    if not rule_defs:
        return "_No signal codes_"

    lines = [
        "## Signal Codes",
        "",
        "| strategy_family | signal_code | description |",
        "| --- | --- | --- |",
    ]
    for rule in sorted(rule_defs, key=lambda item: (item.family, item.code)):
        lines.append(f"| {rule.family} | `{rule.code}` | {rule.description} |")
    return "\n".join(lines)


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


def _print_stage(step: str, **details: object) -> None:
    if details:
        detail_parts = [f"{key} = {value}" for key, value in details.items()]
        print(f"==> {step} | {' | '.join(detail_parts)}", flush=True)
        return
    print(f"==> {step}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=STRATEGY_DESCRIPTION)
    parser.add_argument("--start-date", default="20180101", help="起始日期，格式 YYYYMMDD")
    parser.add_argument("--end-date", default=None, help="结束日期，格式 YYYYMMDD")
    parser.add_argument("--min-sample", type=int, default=30, help="最小样本数阈值")
    parser.add_argument("--top-n", type=int, default=20, help="保留的排名数量")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="结果输出目录")
    return parser


def load_base_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        pct_chg,
        open_qfq,
        high_qfq,
        low_qfq,
        close_qfq,
        boll_lower_qfq,
        rsi_qfq_6,
        rsi_qfq_12,
        ma_qfq_20,
        ma_qfq_60,
        vol,
        amount,
        turnover_rate,
        turnover_rate_f,
        volume_ratio,
        downdays
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

    frame = query_df(sql, params)
    if frame.empty:
        return _empty_frame(
            [
                "ts_code",
                "trade_date",
                "pct_chg",
                "open_qfq",
                "high_qfq",
                "low_qfq",
                "close_qfq",
                "boll_lower_qfq",
                "rsi_qfq_6",
                "rsi_qfq_12",
                "ma_qfq_20",
                "ma_qfq_60",
                "vol",
                "amount",
                "turnover_rate",
                "turnover_rate_f",
                "volume_ratio",
                "downdays",
            ]
        )
    return frame.reindex(
        columns=[
            "ts_code",
            "trade_date",
            "pct_chg",
            "open_qfq",
            "high_qfq",
            "low_qfq",
            "close_qfq",
            "boll_lower_qfq",
            "rsi_qfq_6",
            "rsi_qfq_12",
            "ma_qfq_20",
            "ma_qfq_60",
            "vol",
            "amount",
            "turnover_rate",
            "turnover_rate_f",
            "volume_ratio",
            "downdays",
        ]
    )


def load_money_flow_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        buy_sm_amount,
        sell_sm_amount,
        buy_md_amount,
        sell_md_amount,
        buy_lg_amount,
        sell_lg_amount,
        buy_elg_amount,
        sell_elg_amount,
        net_mf_amount
    FROM stock_money_flow
    WHERE trade_date >= :start_date
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"

    frame = query_df(sql, params)
    columns = [
        "ts_code",
        "trade_date",
        "buy_sm_amount",
        "sell_sm_amount",
        "buy_md_amount",
        "sell_md_amount",
        "buy_lg_amount",
        "sell_lg_amount",
        "buy_elg_amount",
        "sell_elg_amount",
        "net_mf_amount",
    ]
    if frame.empty:
        return _empty_frame(columns + ["main_net", "elg_net"])

    result = frame.reindex(columns=columns).copy()
    result["main_net"] = (
        result["buy_elg_amount"].fillna(0)
        + result["buy_lg_amount"].fillna(0)
        - result["sell_elg_amount"].fillna(0)
        - result["sell_lg_amount"].fillna(0)
    )
    result["elg_net"] = result["buy_elg_amount"].fillna(0) - result["sell_elg_amount"].fillna(0)
    return result


def load_cyq_perf_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        winner_rate,
        cost_5pct,
        cost_95pct,
        weight_avg
    FROM stock_cyq_perf
    WHERE trade_date >= :start_date
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"

    frame = query_df(sql, params)
    columns = ["ts_code", "trade_date", "winner_rate", "cost_5pct", "cost_95pct", "weight_avg"]
    if frame.empty:
        return _empty_frame(columns + ["chip_spread"])

    result = frame.reindex(columns=columns).copy()
    result["chip_spread"] = _safe_divide(result["cost_95pct"] - result["cost_5pct"], result["weight_avg"])
    return result


def load_hk_hold_frame(start_date: str, end_date: str | None = None) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code,
        trade_date,
        vol AS hk_vol,
        ratio AS hk_ratio
    FROM stock_hk_hold
    WHERE trade_date >= :start_date
      AND ratio IS NOT NULL
      AND ratio > 0
    """
    params: dict[str, object] = {"start_date": start_date}
    load_end_date = _load_end_date(end_date)
    if load_end_date is not None:
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"

    frame = query_df(sql, params)
    columns = ["ts_code", "trade_date", "hk_vol", "hk_ratio"]
    if frame.empty:
        return _empty_frame(columns)
    return frame.reindex(columns=columns)


def merge_side_frames(
    base_frame: pd.DataFrame,
    money_flow_frame: pd.DataFrame,
    cyq_perf_frame: pd.DataFrame,
    hk_hold_frame: pd.DataFrame,
) -> pd.DataFrame:
    result = base_frame.copy()
    for side_frame in (money_flow_frame, cyq_perf_frame, hk_hold_frame):
        if not side_frame.empty:
            result = result.merge(side_frame, on=["ts_code", "trade_date"], how="left")
    return result


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).copy()
    grouped = result.groupby("ts_code", sort=False)
    rolling_low = grouped["low_qfq"].transform(lambda series: series.rolling(120, min_periods=1).min())
    rolling_high = grouped["high_qfq"].transform(lambda series: series.rolling(120, min_periods=1).max())

    result["rolling_low_120"] = rolling_low
    result["rolling_high_120"] = rolling_high
    result["pos120"] = _safe_divide(result["close_qfq"] - rolling_low, rolling_high - rolling_low)
    result["close_to_low_120"] = _safe_divide(result["close_qfq"], rolling_low)

    if {"buy_lg_amount", "sell_lg_amount", "buy_elg_amount", "sell_elg_amount"}.issubset(result.columns):
        big_amount = (
            result["buy_lg_amount"].fillna(0)
            + result["sell_lg_amount"].fillna(0)
            + result["buy_elg_amount"].fillna(0)
            + result["sell_elg_amount"].fillna(0)
        )
        result["main_net_ratio"] = _safe_divide(result["main_net"], big_amount)
        result["elg_net_ratio"] = _safe_divide(result["elg_net"], big_amount)
    if "net_mf_amount" in result.columns and "amount" in result.columns:
        result["mf_net_ratio"] = _safe_divide(result["net_mf_amount"], result["amount"])

    if "main_net" in result.columns:
        result["main_net_change_2d"] = grouped["main_net"].diff(2)
        result["main_net_change_3d"] = grouped["main_net"].diff(3)
    if "elg_net" in result.columns:
        result["elg_net_change_2d"] = grouped["elg_net"].diff(2)
    if {"cost_95pct", "cost_5pct", "weight_avg"}.issubset(result.columns):
        result["chip_spread"] = _safe_divide(result["cost_95pct"] - result["cost_5pct"], result["weight_avg"])
        result["chip_spread_change_3d"] = grouped["chip_spread"].diff(3)
    if "winner_rate" in result.columns:
        result["winner_rate_change_3d"] = grouped["winner_rate"].diff(3)
    if {"close_qfq", "weight_avg"}.issubset(result.columns):
        result["close_vs_weight_avg"] = _safe_divide(result["close_qfq"], result["weight_avg"])
    if "hk_ratio" in result.columns:
        result["hk_ratio_change_3d"] = grouped["hk_ratio"].diff(3)
    if "hk_vol" in result.columns:
        result["hk_vol_change_3d"] = grouped["hk_vol"].diff(3)

    if {"close_qfq", "boll_lower_qfq", "rsi_qfq_6"}.issubset(result.columns):
        result["is_bottom_zone"] = (
            (result["pos120"] <= 0.25)
            | (result["close_to_low_120"] <= 1.08)
            | ((result["close_qfq"] <= result["boll_lower_qfq"] * 1.03) & (result["rsi_qfq_6"] < 35))
        ).fillna(False)

    if "close_qfq" in result.columns:
        result["ret_1d"] = grouped["close_qfq"].shift(-1) / result["close_qfq"] - 1
        result["ret_3d"] = grouped["close_qfq"].shift(-3) / result["close_qfq"] - 1

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
    _print_stage("load_base_frame")
    base_frame = load_base_frame(start_date=start_date, end_date=end_date)
    _print_stage("load_money_flow_frame")
    money_flow_frame = load_money_flow_frame(start_date=start_date, end_date=end_date)
    _print_stage("load_cyq_perf_frame")
    cyq_perf_frame = load_cyq_perf_frame(start_date=start_date, end_date=end_date)
    _print_stage("load_hk_hold_frame")
    hk_hold_frame = load_hk_hold_frame(start_date=start_date, end_date=end_date)
    effective_end_date = str(base_frame["trade_date"].max()) if not base_frame.empty else (end_date or "n/a")
    _print_stage(
        "load_base_frame done",
        loaded_rows=len(base_frame),
        loaded_stocks=base_frame["ts_code"].nunique() if "ts_code" in base_frame.columns else 0,
        date_range=_format_date_range(start_date, effective_end_date),
    )
    _print_stage("merge_side_frames")
    merged_frame = merge_side_frames(base_frame, money_flow_frame, cyq_perf_frame, hk_hold_frame)
    _print_stage("build_features")
    featured_df = build_features(merged_frame)
    analysis_df = featured_df[featured_df["trade_date"] <= end_date].copy() if end_date else featured_df
    _print_stage("summarize_signal_matrix")
    rule_defs = build_signal_rule_defs()
    summary_df, trigger_df = summarize_signal_matrix(
        analysis_df,
        rule_defs=rule_defs,
        min_sample=min_sample,
        show_progress=show_progress,
    )
    _print_stage("build_compact_summary")
    compact_df = build_compact_summary(summary_df, trigger_df)
    _print_stage("build_signal_code_markdown")
    signal_code_markdown = build_signal_code_markdown(rule_defs)
    _print_stage("write_outputs")
    output_paths = write_outputs(compact_df, signal_code_markdown, output_dir)
    return {
        "base_df": base_frame,
        "merged_df": merged_frame,
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
    _print_stage("run_analysis")
    result = run_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        min_sample=args.min_sample,
        top_n=args.top_n,
        output_dir=output_dir,
        show_progress=True,
    )

    output_paths = result.get("output_paths", {})
    summary_csv = output_paths.get("summary_csv")
    summary_md = output_paths.get("summary_md")
    if summary_csv is not None:
        print(f"==> summary_csv = {summary_csv}", flush=True)
    if summary_md is not None:
        print(f"==> summary_md = {summary_md}", flush=True)
    print(f"==> rows = {len(result['compact_df'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
