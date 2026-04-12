from __future__ import annotations

import math

import pandas as pd
from scipy.stats import ttest_1samp

DEFAULT_MAX_MISSING_RATIO_PER_DATE = 0.3
DEFAULT_ROLLING_WINDOW_DAYS = 252
DEFAULT_ROLLING_STABILITY_THRESHOLD = 0.7
DEFAULT_MIN_ABS_IC = 0.02
DEFAULT_MIN_ABS_IC_IR = 0.3


def _spearman_correlation(left: pd.Series, right: pd.Series) -> float:
    return float(left.rank(method="average").corr(right.rank(method="average"), method="pearson"))


def _stable_ic_ir(mean_ic: float, ic_std: float, cap: float = 10.0) -> float:
    if math.isnan(mean_ic):
        return 0.0
    if ic_std <= 1e-12:
        return 0.0 if abs(mean_ic) <= 1e-12 else math.copysign(cap, mean_ic)
    value = mean_ic / ic_std
    return float(max(min(value, cap), -cap))


def compute_ic_series(
    panel: pd.DataFrame,
    factor_col: str,
    target_col: str,
    date_col: str = "trade_date",
    max_missing_ratio_per_date: float | None = DEFAULT_MAX_MISSING_RATIO_PER_DATE,
) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for trade_date, group in panel.groupby(date_col, sort=True):
        factor_coverage = float(group[factor_col].notna().mean()) if len(group) else 0.0
        factor_missing_ratio = 1.0 - factor_coverage
        if max_missing_ratio_per_date is not None and factor_missing_ratio > max_missing_ratio_per_date:
            continue
        valid = group.loc[:, [factor_col, target_col]].dropna()
        if len(valid) < 2:
            continue
        records.append(
            {
                "trade_date": trade_date,
                "ic": float(valid[factor_col].corr(valid[target_col], method="pearson")),
                "rank_ic": _spearman_correlation(valid[factor_col], valid[target_col]),
                "factor_coverage": factor_coverage,
                "factor_missing_ratio": factor_missing_ratio,
                "valid_coverage": float(len(valid) / len(group)),
            }
        )
    return pd.DataFrame(records)


def summarize_factor_coverage(
    panel: pd.DataFrame,
    factor_col: str,
    date_col: str = "trade_date",
) -> dict[str, float | int]:
    if panel.empty or factor_col not in panel.columns or date_col not in panel.columns:
        return {
            "coverage": 0.0,
            "trade_date_coverage": 0.0,
            "eligible_trade_date_coverage": 0.0,
            "active_stock_coverage": 0.0,
            "active_trade_date_coverage": 0.0,
            "avg_active_stocks_per_day": 0.0,
            "active_trade_date_count": 0,
            "daily_missing_ratio_mean": 1.0,
            "daily_missing_ratio_max": 1.0,
        }

    factor_present = panel[factor_col].notna()
    active_mask = panel[factor_col].fillna(0.0).ne(0.0)
    total_trade_dates = int(panel[date_col].nunique())
    trade_date_coverage = factor_present.groupby(panel[date_col]).any() if total_trade_dates else pd.Series(dtype=bool)
    active_trade_dates = active_mask.groupby(panel[date_col]).any() if total_trade_dates else pd.Series(dtype=bool)
    active_stocks_per_day = active_mask.groupby(panel[date_col]).sum() if total_trade_dates else pd.Series(dtype=float)
    daily_missing_ratio = 1.0 - factor_present.groupby(panel[date_col]).mean() if total_trade_dates else pd.Series(dtype=float)

    return {
        "coverage": float(factor_present.mean()),
        "trade_date_coverage": float(trade_date_coverage.mean()) if not trade_date_coverage.empty else 0.0,
        "eligible_trade_date_coverage": 0.0,
        "active_stock_coverage": float(active_mask.mean()),
        "active_trade_date_coverage": float(active_trade_dates.mean()) if not active_trade_dates.empty else 0.0,
        "avg_active_stocks_per_day": float(active_stocks_per_day.mean()) if not active_stocks_per_day.empty else 0.0,
        "active_trade_date_count": int(active_trade_dates.sum()) if not active_trade_dates.empty else 0,
        "daily_missing_ratio_mean": float(daily_missing_ratio.mean()) if not daily_missing_ratio.empty else 1.0,
        "daily_missing_ratio_max": float(daily_missing_ratio.max()) if not daily_missing_ratio.empty else 1.0,
    }


def evaluate_rolling_ic_stability(
    ic_series: pd.DataFrame,
    window_days: int = DEFAULT_ROLLING_WINDOW_DAYS,
    min_abs_ic: float = DEFAULT_MIN_ABS_IC,
    min_abs_ic_ir: float = DEFAULT_MIN_ABS_IC_IR,
) -> dict[str, float | int | bool]:
    if ic_series.empty or len(ic_series) < window_days:
        return {
            "rolling_1y_window_count": 0,
            "rolling_1y_valid_ratio": 0.0,
            "passes_rolling_stability": False,
        }

    effective_windows = 0
    for end in range(window_days, len(ic_series) + 1):
        window = ic_series["ic"].iloc[end - window_days : end]
        mean_ic = float(window.mean())
        ic_ir = _stable_ic_ir(mean_ic, float(window.std(ddof=0)))
        if abs(mean_ic) >= min_abs_ic and abs(ic_ir) >= min_abs_ic_ir:
            effective_windows += 1

    window_count = len(ic_series) - window_days + 1
    valid_ratio = effective_windows / window_count if window_count else 0.0
    return {
        "rolling_1y_window_count": window_count,
        "rolling_1y_valid_ratio": float(valid_ratio),
        "passes_rolling_stability": bool(valid_ratio >= DEFAULT_ROLLING_STABILITY_THRESHOLD),
    }


def compute_ic_decay(
    panel: pd.DataFrame,
    factor_col: str,
    target_col: str,
    lags: range = range(1, 11),
    group_key: str = "ts_code",
) -> pd.DataFrame:
    if group_key not in panel.columns:
        return pd.DataFrame(columns=["lag", "mean_ic", "rank_ic"])
    records: list[dict[str, float | int]] = []
    for lag in lags:
        shifted = panel.copy()
        shifted[f"{target_col}_lag_{lag}"] = shifted.groupby(group_key, sort=False)[target_col].shift(-(lag - 1))
        result = analyze_factor_ic(
            shifted,
            factor_col=factor_col,
            target_col=f"{target_col}_lag_{lag}",
            include_decay=False,
        )
        records.append({"lag": lag, "mean_ic": result["mean_ic"], "rank_ic": result["rank_ic"]})
    return pd.DataFrame(records)


def apply_fdr_correction(summary: pd.DataFrame, pvalue_col: str = "p_value") -> pd.DataFrame:
    corrected = summary.copy()
    if corrected.empty or pvalue_col not in corrected.columns:
        return corrected
    ranked = corrected[pvalue_col].rank(method="first")
    corrected["fdr_p_value"] = corrected[pvalue_col] * len(corrected) / ranked
    corrected["fdr_p_value"] = corrected["fdr_p_value"].clip(upper=1.0)
    return corrected


def analyze_factor_ic(
    panel: pd.DataFrame,
    factor_col: str,
    target_col: str = "overnight_return",
    date_col: str = "trade_date",
    include_decay: bool = True,
    max_missing_ratio_per_date: float | None = DEFAULT_MAX_MISSING_RATIO_PER_DATE,
) -> dict[str, object]:
    coverage_summary = summarize_factor_coverage(panel, factor_col=factor_col, date_col=date_col)
    ic_series = compute_ic_series(
        panel,
        factor_col=factor_col,
        target_col=target_col,
        date_col=date_col,
        max_missing_ratio_per_date=max_missing_ratio_per_date,
    )
    total_trade_dates = int(panel[date_col].nunique()) if date_col in panel.columns else 0
    coverage_summary["eligible_trade_date_coverage"] = float(len(ic_series) / total_trade_dates) if total_trade_dates else 0.0
    rolling_stability = evaluate_rolling_ic_stability(ic_series)
    if ic_series.empty:
        return {
            "ic_series": ic_series,
            "mean_ic": 0.0,
            "rank_ic": 0.0,
            "ic_ir": 0.0,
            "positive_rate": 0.0,
            "t_stat": 0.0,
            "p_value": 1.0,
            "ic_decay": pd.DataFrame(columns=["lag", "mean_ic", "rank_ic"]),
            **coverage_summary,
            **rolling_stability,
        }

    mean_ic = float(ic_series["ic"].mean())
    mean_rank_ic = float(ic_series["rank_ic"].mean())
    ic_std = float(ic_series["ic"].std(ddof=0))
    positive_rate = float((ic_series["ic"] > 0).mean())
    ic_ir = _stable_ic_ir(mean_ic, ic_std)
    if len(ic_series) > 1:
        t_stat, p_value = ttest_1samp(ic_series["ic"], popmean=0.0, nan_policy="omit")
        t_stat = 0.0 if math.isnan(t_stat) else float(t_stat)
        p_value = 1.0 if math.isnan(p_value) else float(p_value)
    else:
        t_stat, p_value = 0.0, 1.0
    return {
        "ic_series": ic_series,
        "mean_ic": mean_ic,
        "rank_ic": mean_rank_ic,
        "ic_ir": ic_ir,
        "positive_rate": positive_rate,
        "t_stat": t_stat,
        "p_value": p_value,
        "ic_decay": compute_ic_decay(panel, factor_col=factor_col, target_col=target_col)
        if include_decay
        else pd.DataFrame(columns=["lag", "mean_ic", "rank_ic"]),
        **coverage_summary,
        **rolling_stability,
    }
