from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from apps.quant_platform.research.factor_engine import CompositeFactorBuilder
from apps.quant_platform.research.strategy import FactorStrategy


def run_factor_strategy_backtest(
    panel: pd.DataFrame,
    factor_cols: list[str],
    target_col: str = "overnight_return",
) -> dict[str, object]:
    composite = CompositeFactorBuilder().build(panel, factor_cols=factor_cols, target_col=target_col, method="equal_weight")
    strategy = FactorStrategy()
    return strategy.run(composite, factor_col="composite_factor", return_col=target_col)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run composite-factor strategy backtest.")
    parser.add_argument("--panel-csv", required=True)
    parser.add_argument("--factor", action="append", dest="factors", required=True)
    parser.add_argument("--target-col", default="overnight_return")
    parser.add_argument("--output-json", default="apps/quant_platform/research/output/backtest_results/strategy_summary.json")
    args = parser.parse_args()

    panel = pd.read_csv(args.panel_csv)
    result = run_factor_strategy_backtest(panel, factor_cols=args.factors, target_col=args.target_col)
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result["summary"], handle, ensure_ascii=False, indent=2)
    print(json.dumps({"output_json": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
