from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def assign_factor_groups(
    panel: pd.DataFrame,
    factor_col: str,
    n_groups: int,
    date_col: str = "trade_date",
) -> pd.DataFrame:
    grouped = panel.copy()
    rank_pct = grouped.groupby(date_col, sort=False)[factor_col].rank(method="first", pct=True)
    groups = np.ceil(rank_pct * n_groups).clip(1, n_groups)
    grouped["group"] = pd.Series(groups, index=grouped.index).where(rank_pct.notna()).astype("Int64")
    return grouped


def analyze_layered_returns(
    panel: pd.DataFrame,
    factor_col: str,
    target_col: str = "overnight_return",
    n_groups: int = 5,
    date_col: str = "trade_date",
) -> dict[str, object]:
    grouped_panel = assign_factor_groups(panel, factor_col=factor_col, n_groups=n_groups, date_col=date_col)
    group_returns = (
        grouped_panel.groupby([date_col, "group"], sort=True)[target_col]
        .mean()
        .unstack("group")
        .sort_index(axis=1)
    )
    if group_returns.empty:
        long_short = pd.Series(dtype=float)
        group_return_means: dict[int, float] = {}
        return {
            "grouped_panel": grouped_panel,
            "group_returns": group_returns,
            "long_short_returns": long_short,
            "group_return_means": group_return_means,
        }

    lowest_group = int(group_returns.columns.min())
    highest_group = int(group_returns.columns.max())
    long_short = (group_returns[highest_group] - group_returns[lowest_group]).round(10)
    cumulative_returns = (1 + group_returns.fillna(0.0)).cumprod()
    group_return_means = {int(group): round(float(values.mean()), 10) for group, values in group_returns.items()}
    monotonicity_values = []
    for _, row in group_returns.iterrows():
        clean = row.dropna()
        if len(clean) < 2:
            continue
        stat, _ = spearmanr(clean.index.to_list(), clean.to_list())
        if not np.isnan(stat):
            monotonicity_values.append(float(stat))
    return {
        "grouped_panel": grouped_panel,
        "group_returns": group_returns,
        "cumulative_returns": cumulative_returns,
        "long_short_returns": long_short,
        "group_return_means": group_return_means,
        "monotonicity": float(np.mean(monotonicity_values)) if monotonicity_values else 0.0,
    }
