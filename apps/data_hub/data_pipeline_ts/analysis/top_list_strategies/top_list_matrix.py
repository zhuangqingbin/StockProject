from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


STRATEGY_NAME = "top_list_matrix"
STRATEGY_DESCRIPTION = "龙虎榜策略矩阵"
SOURCE_TABLES = "stock_stk_factor_pro, stock_top_inst, stock_top_list"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def _format_date_range(start_date: str, end_date: str | None) -> str:
    return f"{start_date} -> {end_date or 'latest'}"


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=STRATEGY_DESCRIPTION)
    parser.add_argument("--start-date", default="20180101", help="起始日期，格式 YYYYMMDD")
    parser.add_argument("--end-date", default=None, help="结束日期，格式 YYYYMMDD")
    parser.add_argument("--min-sample", type=int, default=30, help="最小样本数阈值")
    parser.add_argument("--top-n", type=int, default=20, help="终端显示条数")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="结果输出目录")
    return parser


def run_analysis(
    *,
    start_date: str,
    end_date: str | None,
    min_sample: int,
    top_n: int,
    output_dir: Path,
    show_progress: bool = False,
) -> dict[str, Any]:
    return {
        "compact_df": pd.DataFrame(),
        "output_paths": {
            "summary_csv": output_dir / "placeholder.csv",
            "summary_md": output_dir / "placeholder.md",
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    _print_execution_context(args.start_date, args.end_date, args.min_sample, args.top_n, output_dir)
    result = run_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        min_sample=args.min_sample,
        top_n=args.top_n,
        output_dir=output_dir,
        show_progress=True,
    )
    print(f"==> summary_csv = {result['output_paths']['summary_csv']}", flush=True)
    print(f"==> summary_md = {result['output_paths']['summary_md']}", flush=True)
    print(f"==> rows = {len(result['compact_df'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
