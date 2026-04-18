from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df


OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass(frozen=True)
class RuleDef:
    family: str
    code: str
    description: str
    predicate: Callable[[pd.DataFrame], pd.Series]


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=numerator.index, dtype="float64")
    valid = denominator.notna() & (denominator != 0)
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result


def _series_mean(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.mean()) if not valid.empty else float("nan")


def _series_median(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.median()) if not valid.empty else float("nan")


def _series_win_rate(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.gt(0).mean()) if not valid.empty else float("nan")


def _select_existing_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame[[column for column in columns if column in frame.columns]].copy()


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["ts_code", "trade_date"]).copy()
    grouped = result.groupby("ts_code", sort=False)

    result["ret_1d"] = grouped["close_qfq"].shift(-1) / result["close_qfq"] - 1
    result["ret_3d"] = grouped["close_qfq"].shift(-3) / result["close_qfq"] - 1
    result["rolling_low_120"] = grouped["low_qfq"].transform(lambda s: s.rolling(120, min_periods=1).min())
    result["rolling_high_120"] = grouped["high_qfq"].transform(lambda s: s.rolling(120, min_periods=1).max())

    range_width = result["rolling_high_120"] - result["rolling_low_120"]
    result["pos120"] = _safe_divide(result["close_qfq"] - result["rolling_low_120"], range_width)
    result["close_to_low_120"] = _safe_divide(result["close_qfq"], result["rolling_low_120"])

    result["vol_ma_3_prev"] = grouped["vol"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    result["vol_ma_5_prev"] = grouped["vol"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    result["volume_ratio_ma_3_prev"] = grouped["volume_ratio"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    result["prev_volume_ratio"] = grouped["volume_ratio"].shift(1)
    result["turnover_rate_f_ma_3_prev"] = grouped["turnover_rate_f"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    result["amount_ma_5_prev"] = grouped["amount"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())

    result["vol_spike_5"] = _safe_divide(result["vol"], result["vol_ma_5_prev"])
    result["amount_spike_5"] = _safe_divide(result["amount"], result["amount_ma_5_prev"])
    result["volume_expand_ratio_3"] = _safe_divide(result["volume_ratio"], result["volume_ratio_ma_3_prev"])
    result["turnover_jump_3"] = _safe_divide(result["turnover_rate_f"], result["turnover_rate_f_ma_3_prev"])
    return result


def build_bottom_rule_defs() -> list[RuleDef]:
    rules: list[RuleDef] = []

    for threshold in [0.10, 0.15, 0.20, 0.25, 0.30]:
        rules.append(
            RuleDef(
                family="pos120",
                code=f"B_pos120_le_{int(threshold * 100):02d}",
                description=f"pos120 <= {threshold:.2f}",
                predicate=lambda df, threshold=threshold: df["pos120"] <= threshold,
            )
        )

    for threshold in [1.03, 1.05, 1.08, 1.10]:
        suffix = str(threshold).split(".")[1]
        rules.append(
            RuleDef(
                family="near_120_low",
                code=f"B_near120_low_{suffix}",
                description=f"close_to_low_120 <= {threshold:.2f}",
                predicate=lambda df, threshold=threshold: df["close_to_low_120"] <= threshold,
            )
        )

    for code, price_mult, rsi_threshold in [
        ("B_boll_rsi_strict", 1.00, 30),
        ("B_boll_rsi_medium", 1.03, 35),
        ("B_boll_rsi_loose", 1.05, 40),
    ]:
        rules.append(
            RuleDef(
                family="boll_rsi_oversold",
                code=code,
                description=f"close_qfq <= boll_lower_qfq * {price_mult:.2f} and rsi_qfq_6 < {rsi_threshold}",
                predicate=lambda df, price_mult=price_mult, rsi_threshold=rsi_threshold: (
                    (df["close_qfq"] <= df["boll_lower_qfq"] * price_mult) & (df["rsi_qfq_6"] < rsi_threshold)
                ),
            )
        )

    for code, predicate in [
        ("B_below_ma_both", lambda df: (df["close_qfq"] < df["ma_qfq_20"]) & (df["close_qfq"] < df["ma_qfq_60"])),
        ("B_below_ma_trend_weak", lambda df: (df["close_qfq"] < df["ma_qfq_20"]) & (df["ma_qfq_20"] < df["ma_qfq_60"])),
        ("B_below_ma60_rsi45", lambda df: (df["close_qfq"] < df["ma_qfq_60"]) & (df["rsi_qfq_12"] < 45)),
    ]:
        rules.append(
            RuleDef(
                family="below_ma_zone",
                code=code,
                description=code,
                predicate=predicate,
            )
        )

    for downdays, rsi_threshold in [(3, 40), (4, 35), (5, 30)]:
        rules.append(
            RuleDef(
                family="exhaustion",
                code=f"B_exhaustion_d{downdays}_r{rsi_threshold}",
                description=f"downdays >= {downdays} and rsi_qfq_6 < {rsi_threshold}",
                predicate=lambda df, downdays=downdays, rsi_threshold=rsi_threshold: (
                    (df["downdays"] >= downdays) & (df["rsi_qfq_6"] < rsi_threshold)
                ),
            )
        )

    return rules


def build_volume_rule_defs() -> list[RuleDef]:
    rules: list[RuleDef] = []

    for threshold in [1.20, 1.50, 1.80, 2.00]:
        rules.append(
            RuleDef(
                family="volume_ratio",
                code=f"V_vr_gt_{int(threshold * 10):02d}",
                description=f"volume_ratio > {threshold:.2f}",
                predicate=lambda df, threshold=threshold: df["volume_ratio"] > threshold,
            )
        )

    for code, now_threshold, prev_threshold in [
        ("V_shrink_expand_strict", 1.20, 0.80),
        ("V_shrink_expand_medium", 1.50, 1.00),
        ("V_shrink_expand_loose", 1.80, 1.20),
    ]:
        rules.append(
            RuleDef(
                family="shrink_to_expand",
                code=code,
                description=f"volume_ratio > {now_threshold:.2f} and volume_ratio_ma_3_prev <= {prev_threshold:.2f}",
                predicate=lambda df, now_threshold=now_threshold, prev_threshold=prev_threshold: (
                    (df["volume_ratio"] > now_threshold) & (df["volume_ratio_ma_3_prev"] <= prev_threshold)
                ),
            )
        )

    for threshold in [1.30, 1.50, 1.80]:
        rules.append(
            RuleDef(
                family="vol_spike_5",
                code=f"V_vol_spike5_{int(threshold * 10):02d}",
                description=f"vol_spike_5 >= {threshold:.2f}",
                predicate=lambda df, threshold=threshold: df["vol_spike_5"] >= threshold,
            )
        )

    for min_turnover, jump_threshold in [(1.5, 1.30), (2.0, 1.50), (3.0, 2.00)]:
        rules.append(
            RuleDef(
                family="turnover_jump",
                code=f"V_turnover_jump_{int(min_turnover * 10):02d}_{int(jump_threshold * 10):02d}",
                description=f"turnover_rate_f > {min_turnover:.1f} and turnover_jump_3 >= {jump_threshold:.2f}",
                predicate=lambda df, min_turnover=min_turnover, jump_threshold=jump_threshold: (
                    (df["turnover_rate_f"] > min_turnover) & (df["turnover_jump_3"] >= jump_threshold)
                ),
            )
        )

    for threshold in [1.30, 1.50, 2.00]:
        rules.append(
            RuleDef(
                family="amount_spike_5",
                code=f"V_amount_spike5_{int(threshold * 10):02d}",
                description=f"amount_spike_5 >= {threshold:.2f}",
                predicate=lambda df, threshold=threshold: df["amount_spike_5"] >= threshold,
            )
        )

    for code, current_threshold, prev_threshold in [
        ("V_consecutive_expand_loose", 1.20, 1.00),
        ("V_consecutive_expand_strict", 1.50, 1.20),
    ]:
        rules.append(
            RuleDef(
                family="consecutive_expand",
                code=code,
                description=f"volume_ratio > {current_threshold:.2f} and prev_volume_ratio > {prev_threshold:.2f}",
                predicate=lambda df, current_threshold=current_threshold, prev_threshold=prev_threshold: (
                    (df["volume_ratio"] > current_threshold) & (df["prev_volume_ratio"] > prev_threshold)
                ),
            )
        )

    return rules


def build_family_summary(summary_df: pd.DataFrame, family_col: str) -> pd.DataFrame:
    if summary_df.empty:
        return pd.DataFrame(columns=[family_col, "best_signal_code", "best_avg_ret_3d", "best_win_rate_3d"])

    rows: list[dict[str, object]] = []
    grouped = summary_df.sort_values(["avg_ret_3d", "win_rate_3d"], ascending=[False, False]).groupby(
        family_col,
        sort=True,
        dropna=False,
    )
    for family_value, family_frame in grouped:
        best_row = family_frame.iloc[0]
        rows.append(
            {
                family_col: family_value,
                "best_signal_code": best_row["signal_code"],
                "best_avg_ret_3d": best_row["avg_ret_3d"],
                "best_win_rate_3d": best_row["win_rate_3d"],
            }
        )
    return pd.DataFrame(rows)


def build_strategy_ranking(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return pd.DataFrame(
            columns=[
                "strategy_rank_1d",
                "strategy_rank_3d",
                "bottom_family",
                "bottom_code",
                "volume_family",
                "volume_code",
                "signal_code",
                "sample_count",
                "avg_ret_1d",
                "median_ret_1d",
                "win_rate_1d",
                "avg_ret_3d",
                "median_ret_3d",
                "win_rate_3d",
                "is_low_sample",
            ]
        )

    ranking_df = summary_df.sort_values(
        ["avg_ret_1d", "win_rate_1d", "avg_ret_3d", "win_rate_3d", "sample_count"],
        ascending=[False, False, False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    ranking_df["strategy_rank_1d"] = ranking_df.index + 1

    ranking_3d = summary_df.sort_values(
        ["avg_ret_3d", "win_rate_3d", "avg_ret_1d", "win_rate_1d", "sample_count"],
        ascending=[False, False, False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    ranking_3d["strategy_rank_3d"] = ranking_3d.index + 1

    ranking_df = ranking_df.merge(
        ranking_3d[["signal_code", "strategy_rank_3d"]],
        on="signal_code",
        how="left",
    )
    leading_cols = [
        "strategy_rank_1d",
        "strategy_rank_3d",
        "bottom_family",
        "bottom_code",
        "volume_family",
        "volume_code",
        "signal_code",
        "sample_count",
        "avg_ret_1d",
        "median_ret_1d",
        "win_rate_1d",
        "avg_ret_3d",
        "median_ret_3d",
        "win_rate_3d",
        "is_low_sample",
    ]
    return ranking_df[leading_cols]


def build_latest_hits(trigger_df: pd.DataFrame, strategy_ranking_df: pd.DataFrame) -> pd.DataFrame:
    if trigger_df.empty or strategy_ranking_df.empty:
        return pd.DataFrame(
            columns=[
                "ts_code",
                "trade_date",
                "bottom_family",
                "bottom_code",
                "volume_family",
                "volume_code",
                "signal_code",
                "close_qfq",
                "pct_chg",
                "volume_ratio",
                "turnover_rate_f",
                "strategy_rank_1d",
                "strategy_rank_3d",
                "strategy_avg_ret_1d",
                "strategy_win_rate_1d",
                "strategy_avg_ret_3d",
                "strategy_win_rate_3d",
                "strategy_sample_count",
            ]
        )

    latest_date = trigger_df["trade_date"].max()
    latest_hits = trigger_df[trigger_df["trade_date"] == latest_date].copy()
    latest_hits = latest_hits.merge(
        strategy_ranking_df[
            [
                "signal_code",
                "strategy_rank_1d",
                "strategy_rank_3d",
                "sample_count",
                "avg_ret_1d",
                "win_rate_1d",
                "avg_ret_3d",
                "win_rate_3d",
            ]
        ].rename(
            columns={
                "sample_count": "strategy_sample_count",
                "avg_ret_1d": "strategy_avg_ret_1d",
                "win_rate_1d": "strategy_win_rate_1d",
                "avg_ret_3d": "strategy_avg_ret_3d",
                "win_rate_3d": "strategy_win_rate_3d",
            }
        ),
        on="signal_code",
        how="left",
    )
    latest_hits = latest_hits.sort_values(
        ["strategy_avg_ret_1d", "strategy_win_rate_1d", "strategy_avg_ret_3d", "strategy_win_rate_3d", "signal_code", "ts_code"],
        ascending=[False, False, False, False, True, True],
        na_position="last",
    ).reset_index(drop=True)
    leading_cols = [
        "ts_code",
        "trade_date",
        "bottom_family",
        "bottom_code",
        "volume_family",
        "volume_code",
        "signal_code",
        "close_qfq",
        "pct_chg",
        "volume_ratio",
        "turnover_rate_f",
        "strategy_rank_1d",
        "strategy_rank_3d",
        "strategy_avg_ret_1d",
        "strategy_win_rate_1d",
        "strategy_avg_ret_3d",
        "strategy_win_rate_3d",
        "strategy_sample_count",
    ]
    return latest_hits[leading_cols]


def summarize_signal_matrix(
    frame: pd.DataFrame,
    min_sample: int = 30,
    bottom_rules: list[RuleDef] | None = None,
    volume_rules: list[RuleDef] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bottom_rules = bottom_rules or build_bottom_rule_defs()
    volume_rules = volume_rules or build_volume_rule_defs()

    summary_rows: list[dict[str, object]] = []
    trigger_frames: list[pd.DataFrame] = []

    for bottom_rule in bottom_rules:
        bottom_mask = bottom_rule.predicate(frame).fillna(False)
        for volume_rule in volume_rules:
            volume_mask = volume_rule.predicate(frame).fillna(False)
            signal_mask = bottom_mask & volume_mask
            triggered = frame.loc[signal_mask].copy()
            if triggered.empty:
                continue
            if triggered["ret_1d"].notna().sum() == 0 and triggered["ret_3d"].notna().sum() == 0:
                continue

            signal_code = f"{bottom_rule.code}__{volume_rule.code}"
            triggered["bottom_family"] = bottom_rule.family
            triggered["bottom_code"] = bottom_rule.code
            triggered["volume_family"] = volume_rule.family
            triggered["volume_code"] = volume_rule.code
            triggered["signal_code"] = signal_code
            trigger_frames.append(
                _select_existing_columns(
                    triggered,
                    [
                        "ts_code",
                        "trade_date",
                        "bottom_family",
                        "bottom_code",
                        "volume_family",
                        "volume_code",
                        "signal_code",
                        "close_qfq",
                        "pct_chg",
                        "volume_ratio",
                        "turnover_rate_f",
                        "ret_1d",
                        "ret_3d",
                    ],
                )
            )
            summary_rows.append(
                {
                    "bottom_family": bottom_rule.family,
                    "bottom_code": bottom_rule.code,
                    "volume_family": volume_rule.family,
                    "volume_code": volume_rule.code,
                    "signal_code": signal_code,
                    "sample_count": int(len(triggered)),
                    "avg_ret_1d": _series_mean(triggered["ret_1d"]),
                    "median_ret_1d": _series_median(triggered["ret_1d"]),
                    "win_rate_1d": _series_win_rate(triggered["ret_1d"]),
                    "avg_ret_3d": _series_mean(triggered["ret_3d"]),
                    "median_ret_3d": _series_median(triggered["ret_3d"]),
                    "win_rate_3d": _series_win_rate(triggered["ret_3d"]),
                }
            )

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows).sort_values(
            ["avg_ret_3d", "win_rate_3d", "sample_count"],
            ascending=[False, False, False],
            na_position="last",
        )
        summary_df["is_low_sample"] = summary_df["sample_count"] < min_sample
    else:
        summary_df = pd.DataFrame(
            columns=[
                "bottom_family",
                "bottom_code",
                "volume_family",
                "volume_code",
                "signal_code",
                "sample_count",
                "avg_ret_1d",
                "median_ret_1d",
                "win_rate_1d",
                "avg_ret_3d",
                "median_ret_3d",
                "win_rate_3d",
                "is_low_sample",
            ]
        )

    trigger_df = pd.concat(trigger_frames, ignore_index=True) if trigger_frames else pd.DataFrame()
    bottom_family_df = build_family_summary(summary_df, "bottom_family")
    volume_family_df = build_family_summary(summary_df, "volume_family")
    return summary_df, trigger_df, bottom_family_df, volume_family_df


def _dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows_"

    columns = frame.columns.tolist()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in frame.iterrows():
        values = ["" if pd.isna(value) else str(value) for value in row.tolist()]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def _build_output_stem() -> str:
    return datetime.now().strftime("%m%d_%H%M")


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
        turnover_rate,
        turnover_rate_f,
        volume_ratio,
        boll_lower_qfq,
        boll_mid_qfq,
        boll_upper_qfq,
        rsi_qfq_6,
        rsi_qfq_12,
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
    if end_date:
        load_end_date = (datetime.strptime(end_date, "%Y%m%d") + timedelta(days=10)).strftime("%Y%m%d")
        sql += "\n      AND trade_date <= :load_end_date"
        params["load_end_date"] = load_end_date
    sql += "\n    ORDER BY ts_code, trade_date"
    return query_df(sql, params)


def write_outputs(
    summary_df: pd.DataFrame,
    trigger_df: pd.DataFrame,
    bottom_family_df: pd.DataFrame,
    volume_family_df: pd.DataFrame,
    strategy_ranking_df: pd.DataFrame,
    latest_hits_df: pd.DataFrame,
    output_dir: Path,
    top_n: int,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_stem = _build_output_stem()
    summary_csv = output_dir / f"{output_stem}.csv"
    summary_md = output_dir / f"{output_stem}.md"
    bottom_family_csv = output_dir / f"{output_stem}_bottom_family.csv"
    volume_family_csv = output_dir / f"{output_stem}_volume_family.csv"
    trigger_csv = output_dir / f"{output_stem}_triggers.csv"
    strategy_ranking_csv = output_dir / f"{output_stem}_strategy_ranking.csv"
    latest_hits_csv = output_dir / f"{output_stem}_latest_hits.csv"

    summary_df.to_csv(summary_csv, index=False)
    trigger_df.to_csv(trigger_csv, index=False)
    bottom_family_df.to_csv(bottom_family_csv, index=False)
    volume_family_df.to_csv(volume_family_csv, index=False)
    strategy_ranking_df.to_csv(strategy_ranking_csv, index=False)
    latest_hits_df.to_csv(latest_hits_csv, index=False)

    top_view = strategy_ranking_df.head(top_n)
    summary_md.write_text(_dataframe_to_markdown(top_view), encoding="utf-8")
    return {
        "summary_csv": summary_csv,
        "summary_md": summary_md,
        "bottom_family_csv": bottom_family_csv,
        "volume_family_csv": volume_family_csv,
        "trigger_csv": trigger_csv,
        "strategy_ranking_csv": strategy_ranking_csv,
        "latest_hits_csv": latest_hits_csv,
    }


def run_analysis(
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
) -> dict[str, object]:
    source_df = load_base_frame(start_date=start_date, end_date=end_date)
    featured_df = build_features(source_df)
    analysis_df = featured_df[featured_df["trade_date"] <= end_date].copy() if end_date else featured_df
    summary_df, trigger_df, bottom_family_df, volume_family_df = summarize_signal_matrix(
        analysis_df,
        min_sample=min_sample,
    )
    strategy_ranking_df = build_strategy_ranking(summary_df)
    latest_hits_df = build_latest_hits(trigger_df, strategy_ranking_df)
    output_paths = write_outputs(
        summary_df=summary_df,
        trigger_df=trigger_df,
        bottom_family_df=bottom_family_df,
        volume_family_df=volume_family_df,
        strategy_ranking_df=strategy_ranking_df,
        latest_hits_df=latest_hits_df,
        output_dir=output_dir,
        top_n=top_n,
    )
    return {
        "source_df": source_df,
        "featured_df": featured_df,
        "summary_df": summary_df,
        "trigger_df": trigger_df,
        "bottom_family_df": bottom_family_df,
        "volume_family_df": volume_family_df,
        "strategy_ranking_df": strategy_ranking_df,
        "latest_hits_df": latest_hits_df,
        "output_paths": output_paths,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bottom volume matrix analyzer")
    parser.add_argument("--start-date", default="20180101")
    parser.add_argument("--end-date")
    parser.add_argument("--min-sample", type=int, default=30)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        min_sample=args.min_sample,
        top_n=args.top_n,
        output_dir=args.output_dir,
    )
    strategy_ranking_df = result["strategy_ranking_df"]
    print(strategy_ranking_df.head(args.top_n).to_string(index=False))
    print(f"summary_csv={result['output_paths']['summary_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
