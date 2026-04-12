from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExitRuleConfig:
    take_profit: float | None = 0.20
    stop_loss: float | None = -0.08
    max_holding_days: int | None = 10
    require_positive_factor: bool = False


class ExitRuleEngine:
    def __init__(self, config: ExitRuleConfig | None = None):
        self.config = config or ExitRuleConfig()

    def apply(
        self,
        target_weights: pd.DataFrame,
        factor_panel: pd.DataFrame | None = None,
        factor_col: str = "composite_factor",
        position_return_col: str = "position_return",
    ) -> pd.DataFrame:
        adjusted = target_weights.copy().sort_index()
        adjusted["exit_reason"] = ""

        if factor_panel is not None and not factor_panel.empty:
            factor_frame = factor_panel.loc[:, ["trade_date", "ts_code", factor_col, *([position_return_col] if position_return_col in factor_panel.columns else [])]]
            adjusted = adjusted.reset_index().merge(factor_frame, on=["trade_date", "ts_code"], how="left").set_index(
                ["trade_date", "ts_code"]
            )

        adjusted["holding_days"] = 0.0
        adjusted = adjusted.sort_index()

        for _, index in adjusted.groupby(level=1, sort=False).groups.items():
            group = adjusted.loc[index]
            active = False
            holding_days = 0
            for row_index, row in group.iterrows():
                target_weight = float(row["target_weight"])
                if target_weight <= 0:
                    adjusted.loc[row_index, "holding_days"] = 0.0
                    active = False
                    holding_days = 0
                    continue

                holding_days = holding_days + 1 if active else 1
                adjusted.loc[row_index, "holding_days"] = float(holding_days)

                position_return = 0.0
                if active and position_return_col in adjusted.columns:
                    raw_position_return = row.get(position_return_col, 0.0)
                    position_return = 0.0 if pd.isna(raw_position_return) else float(raw_position_return)
                factor_value = float(row.get(factor_col, np.nan)) if factor_col in adjusted.columns else np.nan
                exit_reason = ""

                if self.config.max_holding_days is not None and holding_days > self.config.max_holding_days:
                    exit_reason = "max_holding_days"
                elif self.config.require_positive_factor and factor_col in adjusted.columns and factor_value <= 0:
                    exit_reason = "non_positive_factor"
                elif self.config.take_profit is not None and active and position_return >= self.config.take_profit:
                    exit_reason = "take_profit"
                elif self.config.stop_loss is not None and active and position_return <= self.config.stop_loss:
                    exit_reason = "stop_loss"

                if exit_reason:
                    adjusted.loc[row_index, "target_weight"] = 0.0
                    adjusted.loc[row_index, "exit_reason"] = exit_reason
                    adjusted.loc[row_index, "holding_days"] = 0.0
                    active = False
                    holding_days = 0
                    continue

                active = True

        return adjusted
