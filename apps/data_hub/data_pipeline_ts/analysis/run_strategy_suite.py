from __future__ import annotations

import argparse
import importlib
import time
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


def _strategy_output_dir(suite_output_dir: Path, strategy_name: str) -> Path:
    return suite_output_dir / strategy_name


def run_single_strategy(
    *,
    spec: StrategySpec,
    strategy_module: Any,
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    suite_output_dir: Path,
) -> dict[str, Any]:
    strategy_output_dir = _strategy_output_dir(suite_output_dir, spec.strategy_name)
    strategy_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"==> running strategy = {spec.strategy_name}", flush=True)
    started_at = time.perf_counter()
    try:
        result = strategy_module.run_analysis(
            start_date=start_date,
            end_date=end_date,
            min_sample=min_sample,
            top_n=top_n,
            output_dir=strategy_output_dir,
            show_progress=True,
        )
        result = result or {}
        compact_df = result.get("compact_df", pd.DataFrame())
        output_paths = result.get("output_paths", {})
        elapsed_seconds = round(time.perf_counter() - started_at, 3)
        rows = int(len(compact_df))
        print(
            f"==> done strategy = {spec.strategy_name} | status = success | rows = {rows} | elapsed = {elapsed_seconds}s",
            flush=True,
        )
        return {
            "strategy_name": spec.strategy_name,
            "strategy_description": spec.strategy_description,
            "status": "success",
            "rows": rows,
            "summary_csv": str(output_paths.get("summary_csv", "")),
            "summary_md": str(output_paths.get("summary_md", "")),
            "elapsed_seconds": elapsed_seconds,
            "error_message": "",
            "compact_df": compact_df,
        }
    except Exception as exc:
        elapsed_seconds = round(time.perf_counter() - started_at, 3)
        error_message = f"{type(exc).__name__}: {exc}"
        print(
            f"==> failed strategy = {spec.strategy_name} | error = {error_message}",
            flush=True,
        )
        return {
            "strategy_name": spec.strategy_name,
            "strategy_description": spec.strategy_description,
            "status": "failed",
            "rows": 0,
            "summary_csv": "",
            "summary_md": "",
            "elapsed_seconds": elapsed_seconds,
            "error_message": error_message,
            "compact_df": pd.DataFrame(),
        }


def build_suite_summary_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "strategy_name",
        "strategy_description",
        "status",
        "rows",
        "summary_csv",
        "summary_md",
        "elapsed_seconds",
        "error_message",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).reindex(columns=columns)


def write_suite_summary(summary_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "suite_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    return summary_path


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
