from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TopPercentSignalGenerator:
    top_pct: float = 0.10
    hold_pct: float = 0.30
    max_holdings: int = 20
    weighting: str = "equal"

    def _weights_for_selection(self, selected: pd.DataFrame, factor_col: str) -> pd.Series:
        if selected.empty:
            return pd.Series(dtype=float)
        if self.weighting == "factor_weighted":
            shifted = selected[factor_col] - selected[factor_col].min() + 1e-6
            total = shifted.sum()
            if total > 0:
                return shifted / total
        return pd.Series(1 / len(selected), index=selected.index, dtype=float)

    def generate(self, factor_panel: pd.DataFrame, factor_col: str) -> pd.DataFrame:
        records: list[dict[str, object]] = []
        previous_holdings: set[str] = set()

        for trade_date, group in factor_panel.groupby("trade_date", sort=True):
            ranked = group.sort_values(factor_col, ascending=False).reset_index(drop=True)
            ranked["rank_pct"] = ranked[factor_col].rank(method="first", ascending=False, pct=True)

            buy_candidates = ranked.loc[ranked["rank_pct"] <= self.top_pct].copy()
            keep_candidates = ranked.loc[
                ranked["ts_code"].isin(previous_holdings) & (ranked["rank_pct"] <= self.hold_pct)
            ].copy()
            selected = (
                pd.concat([buy_candidates, keep_candidates], ignore_index=True)
                .drop_duplicates("ts_code")
                .sort_values(factor_col, ascending=False)
                .head(self.max_holdings)
            )
            selected_codes = set(selected["ts_code"].tolist())
            weights = self._weights_for_selection(selected, factor_col)

            for _, row in ranked.iterrows():
                target_weight = float(weights.loc[row.name]) if row.name in weights.index else 0.0
                records.append(
                    {
                        "trade_date": trade_date,
                        "ts_code": row["ts_code"],
                        "target_weight": target_weight,
                        "rank_pct": float(row["rank_pct"]),
                        "selected": float(row["ts_code"] in selected_codes),
                    }
                )

            previous_holdings = selected_codes

        frame = pd.DataFrame(records).set_index(["trade_date", "ts_code"]).sort_index()
        return frame
