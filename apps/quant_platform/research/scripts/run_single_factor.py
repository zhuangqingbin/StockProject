from __future__ import annotations

import argparse
import json

import pandas as pd

from apps.quant_platform.research.analyzer import analyze_factor_ic, analyze_layered_returns
from apps.quant_platform.research.data_loader import ResearchDataLoader

BASE_PANEL_COLUMNS = ("ts_code", "trade_date", "open", "close")


def run_single_factor_analysis(
    panel: pd.DataFrame,
    factor_col: str,
    target_col: str = "overnight_return",
) -> dict[str, object]:
    return {
        "factor": factor_col,
        "ic": analyze_factor_ic(panel, factor_col=factor_col, target_col=target_col),
        "layered": analyze_layered_returns(panel, factor_col=factor_col, target_col=target_col),
    }


def _single_factor_columns(factor_col: str) -> list[str]:
    return list(dict.fromkeys([*BASE_PANEL_COLUMNS, factor_col]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run single-factor IC and layered analysis.")
    parser.add_argument("--factor", required=True)
    parser.add_argument("--start-date", default="2018-01-01")
    parser.add_argument("--end-date")
    args = parser.parse_args()

    loader = ResearchDataLoader()
    panel = loader.prepare_panel(
        loader.load_panel(
            start_date=args.start_date,
            end_date=args.end_date,
            columns=_single_factor_columns(args.factor),
        )
    )
    result = run_single_factor_analysis(panel, factor_col=args.factor)
    print(json.dumps({"factor": result["factor"], "ic": result["ic"]["mean_ic"]}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
