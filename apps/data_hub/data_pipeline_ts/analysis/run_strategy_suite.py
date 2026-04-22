from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.strategy_registry import STRATEGY_REGISTRY, StrategySpec

SUITE_NAME = "strategy_suite"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "strategy_suite"


def _format_date_range(start_date: str, end_date: str | None) -> str:
    return f"{start_date} -> {end_date or 'latest'}"


def _parse_strategy_names(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    names = [item.strip() for item in raw.split(",") if item.strip()]
    return names or None


def _print_suite_context(
    start_date: str,
    end_date: str | None,
    strategy_names: list[str] | None,
    output_dir: Path,
) -> None:
    names_text = ",".join(strategy_names) if strategy_names else "all"
    print(f"suite = {SUITE_NAME}", flush=True)
    print(f"requested_date_range = {_format_date_range(start_date, end_date)}", flush=True)
    print(f"strategies = {names_text}", flush=True)
    print(f"output_dir = {output_dir}", flush=True)


def resolve_strategy_specs(strategy_names: list[str] | None) -> list[StrategySpec]:
    if strategy_names is None:
        return [STRATEGY_REGISTRY[name] for name in STRATEGY_REGISTRY]
    unknown = [name for name in strategy_names if name not in STRATEGY_REGISTRY]
    if unknown:
        joined = ",".join(unknown)
        raise ValueError(f"Unknown strategies: {joined}")
    return [STRATEGY_REGISTRY[name] for name in strategy_names]


def load_strategy_module(spec: StrategySpec):
    module = importlib.import_module(spec.module_path)
    required = ["STRATEGY_NAME", "STRATEGY_DESCRIPTION", "run_analysis"]
    missing = [item for item in required if not hasattr(module, item)]
    if missing:
        joined = ",".join(missing)
        raise AttributeError(f"{spec.strategy_name} missing required attributes: {joined}")
    return module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multiple strategy matrix scripts")
    parser.add_argument("--start-date", default="20180101")
    parser.add_argument("--end-date")
    parser.add_argument("--strategies")
    parser.add_argument("--min-sample", type=int, default=30)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def run_suite(
    *,
    start_date: str,
    end_date: str | None,
    strategy_names: list[str] | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "suite_summary_df": pd.DataFrame(),
        "output_paths": {
            "suite_summary_csv": output_dir / "suite_summary.csv",
            "suite_compact_ranking_csv": output_dir / "suite_compact_ranking.csv",
            "suite_compact_by_strategy_csv": output_dir / "suite_compact_by_strategy.csv",
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    strategy_names = _parse_strategy_names(args.strategies)
    output_dir = Path(args.output_dir)
    _print_suite_context(args.start_date, args.end_date, strategy_names, output_dir)
    result = run_suite(
        start_date=args.start_date,
        end_date=args.end_date,
        strategy_names=strategy_names,
        min_sample=args.min_sample,
        top_n=args.top_n,
        output_dir=output_dir,
    )
    print(f"==> suite_summary_csv = {result['output_paths']['suite_summary_csv']}", flush=True)
    print(f"==> suite_compact_ranking_csv = {result['output_paths']['suite_compact_ranking_csv']}", flush=True)
    print(f"==> suite_compact_by_strategy_csv = {result['output_paths']['suite_compact_by_strategy_csv']}", flush=True)
    print(f"==> strategy_count = {len(result['suite_summary_df'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
