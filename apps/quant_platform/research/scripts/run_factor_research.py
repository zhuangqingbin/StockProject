from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from apps.quant_platform.research.analyzer import ResearchReportBuilder, analyze_factor_correlation, analyze_factor_ic, analyze_layered_returns
from apps.quant_platform.research.analyzer.ic_analysis import apply_fdr_correction
from apps.quant_platform.research.pipeline import FullResearchPipeline, FullResearchPipelineConfig, save_factor_catalog
from apps.quant_platform.research.publishing import publish_research_snapshot

IC_REPORTS_OUTPUT_DIR = Path("apps/quant_platform/research/output/ic_reports")
FULL_RESEARCH_OUTPUT_DIR = Path("apps/quant_platform/research/output/full_research")


def _annotate_split_consistency(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary

    annotated = summary.copy()
    train_mean_ic = annotated.get("train_mean_ic", pd.Series(0.0, index=annotated.index)).fillna(0.0)
    validation_mean_ic = annotated.get("validation_mean_ic", pd.Series(0.0, index=annotated.index)).fillna(0.0)
    train_ic_ir = annotated.get("train_ic_ir", pd.Series(0.0, index=annotated.index)).fillna(0.0).abs()
    validation_ic_ir = annotated.get("validation_ic_ir", pd.Series(0.0, index=annotated.index)).fillna(0.0).abs()
    train_coverage = annotated.get("train_coverage", pd.Series(0.0, index=annotated.index)).fillna(0.0)
    validation_coverage = annotated.get("validation_coverage", pd.Series(0.0, index=annotated.index)).fillna(0.0)
    train_rolling_ratio = annotated.get(
        "train_rolling_1y_valid_ratio",
        pd.Series(0.0, index=annotated.index),
    ).fillna(0.0)
    validation_rolling_ratio = annotated.get(
        "validation_rolling_1y_valid_ratio",
        pd.Series(0.0, index=annotated.index),
    ).fillna(0.0)

    same_direction = (
        train_mean_ic.ne(0.0)
        & validation_mean_ic.ne(0.0)
        & ((train_mean_ic * validation_mean_ic) > 0.0)
    )
    annotated["train_validation_same_direction"] = same_direction
    annotated["train_validation_consistent"] = same_direction & train_ic_ir.ge(0.3) & validation_ic_ir.ge(0.3)
    annotated["train_rolling_stable"] = train_rolling_ratio.ge(0.7)
    annotated["validation_rolling_stable"] = validation_rolling_ratio.ge(0.7)
    annotated["passes_research_gate"] = (
        annotated["train_validation_consistent"]
        & annotated["train_rolling_stable"]
        & annotated["validation_rolling_stable"]
        & train_coverage.ge(0.3)
        & validation_coverage.ge(0.3)
    )
    return annotated


def run_factor_research(
    panel: pd.DataFrame,
    factor_cols: list[str],
    target_col: str = "overnight_return",
    output_dir: str | Path = "apps/quant_platform/research/output/ic_reports",
) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    ranking_records: list[dict[str, float | str]] = []
    builder = ResearchReportBuilder(output_path)

    for factor in factor_cols:
        ic_result = analyze_factor_ic(panel, factor_col=factor, target_col=target_col)
        layered_result = analyze_layered_returns(panel, factor_col=factor, target_col=target_col)
        ranking_records.append(
            {
                "factor_name": factor,
                "mean_ic": ic_result["mean_ic"],
                "rank_ic": ic_result["rank_ic"],
                "ic_ir": ic_result["ic_ir"],
                "positive_rate": ic_result["positive_rate"],
                "t_stat": ic_result["t_stat"],
                "p_value": ic_result["p_value"],
                "coverage": ic_result["coverage"],
                "trade_date_coverage": ic_result["trade_date_coverage"],
                "eligible_trade_date_coverage": ic_result["eligible_trade_date_coverage"],
                "active_stock_coverage": ic_result["active_stock_coverage"],
                "active_trade_date_coverage": ic_result["active_trade_date_coverage"],
                "avg_active_stocks_per_day": ic_result["avg_active_stocks_per_day"],
                "active_trade_date_count": ic_result["active_trade_date_count"],
                "daily_missing_ratio_mean": ic_result["daily_missing_ratio_mean"],
                "daily_missing_ratio_max": ic_result["daily_missing_ratio_max"],
                "rolling_1y_window_count": ic_result["rolling_1y_window_count"],
                "rolling_1y_valid_ratio": ic_result["rolling_1y_valid_ratio"],
                "passes_rolling_stability": ic_result["passes_rolling_stability"],
                "long_short_mean": float(layered_result["long_short_returns"].mean()) if not layered_result["long_short_returns"].empty else 0.0,
                "monotonicity": float(layered_result.get("monotonicity", 0.0)),
            }
        )
        builder.build_factor_report(
            factor_name=factor,
            ic_result=ic_result,
            layered_result=layered_result,
            correlation_result=analyze_factor_correlation(panel, factor_cols=[factor]),
        )

    ranking = pd.DataFrame(ranking_records)
    if ranking.empty:
        ranking = pd.DataFrame(
            columns=[
                "factor_name",
                "mean_ic",
                "rank_ic",
                "ic_ir",
                "positive_rate",
                "t_stat",
                "p_value",
                "coverage",
                "trade_date_coverage",
                "eligible_trade_date_coverage",
                "active_stock_coverage",
                "active_trade_date_coverage",
                "avg_active_stocks_per_day",
                "active_trade_date_count",
                "daily_missing_ratio_mean",
                "daily_missing_ratio_max",
                "rolling_1y_window_count",
                "rolling_1y_valid_ratio",
                "passes_rolling_stability",
                "long_short_mean",
                "monotonicity",
                "fdr_p_value",
            ]
        )
    else:
        ranking = ranking.sort_values("ic_ir", ascending=False).reset_index(drop=True)
        ranking = apply_fdr_correction(ranking)
    ranking_assets = builder.build_ranking_report(ranking, report_name="factor_ranking", title="Factor Ranking")
    ranking_path = Path(ranking_assets["ranking_csv"])
    correlation = analyze_factor_correlation(panel, factor_cols=factor_cols, factor_scores=ranking.set_index("factor_name")["ic_ir"].to_dict())
    correlation_assets = builder.build_correlation_report(correlation)
    return {
        "ranking": ranking,
        "correlation": correlation,
        "ranking_path": str(ranking_path),
        "ranking_overview_html": ranking_assets["overview_html"],
        "correlation_plot": correlation_assets["heatmap_png"],
        "correlation_matrix_csv": correlation_assets["matrix_csv"],
    }


def run_full_factor_research(
    start_date: str,
    end_date: str | None = None,
    output_dir: str | Path = "apps/quant_platform/research/output/full_research",
    target_col: str = "overnight_return",
    time_series_windows: tuple[int, ...] = (5, 10, 20, 60),
    event_windows: tuple[int, ...] = (3, 5, 10, 20),
    include_chip_distribution: bool = True,
) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    pipeline = FullResearchPipeline(
        config=FullResearchPipelineConfig(
            time_series_windows=time_series_windows,
            event_windows=event_windows,
            include_chip_distribution=include_chip_distribution,
        )
    )
    build_result = pipeline.build_from_dataset(
        pipeline.load_dataset_from_database(start_date=start_date, end_date=end_date)
    )

    panel_path = output_path / "full_factor_panel.csv"
    build_result.panel.to_csv(panel_path, index=False)
    catalog_path = save_factor_catalog(build_result.factor_catalog, output_path / "factor_catalog.json")

    split_results: dict[str, str] = {}
    merged_rankings: list[pd.DataFrame] = []
    for split_name, split_panel in build_result.sample_panels.items():
        usable = split_panel.dropna(subset=[target_col])
        if usable.empty:
            continue
        split_output_dir = output_path / split_name
        split_result = run_factor_research(
            usable,
            factor_cols=build_result.factor_columns,
            target_col=target_col,
            output_dir=split_output_dir,
        )
        split_results[split_name] = split_result["ranking_path"]
        ranking = split_result["ranking"].copy().rename(
            columns={column: f"{split_name}_{column}" for column in split_result["ranking"].columns if column != "factor_name"}
        )
        merged_rankings.append(ranking)

    split_summary_path = output_path / "split_factor_summary.csv"
    summary = pd.DataFrame(columns=["factor_name"])
    if merged_rankings:
        summary = merged_rankings[0]
        for frame in merged_rankings[1:]:
            summary = summary.merge(frame, on="factor_name", how="outer")
    summary = _annotate_split_consistency(summary)
    summary.to_csv(split_summary_path, index=False)

    qualified_mask = summary["passes_research_gate"].fillna(False) if "passes_research_gate" in summary.columns else pd.Series(False, index=summary.index)
    qualified_summary = summary.loc[qualified_mask].copy()
    qualified_summary_path = output_path / "qualified_factor_summary.csv"
    qualified_summary.to_csv(qualified_summary_path, index=False)
    builder = ResearchReportBuilder(output_path)
    split_summary_assets = builder.build_ranking_report(
        summary,
        report_name="split_factor_summary",
        title="Train Validation Test Factor Summary",
    )
    qualified_summary_assets = builder.build_ranking_report(
        qualified_summary,
        report_name="qualified_factor_summary",
        title="Qualified Factor Summary",
    )

    return {
        "panel_path": str(panel_path),
        "catalog_path": catalog_path,
        "split_results": split_results,
        "split_summary_path": str(split_summary_path),
        "qualified_summary_path": str(qualified_summary_path),
        "split_summary_html": split_summary_assets["overview_html"],
        "qualified_summary_html": qualified_summary_assets["overview_html"],
    }


def _resolve_output_dir(*, from_db: bool, output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir)
    return FULL_RESEARCH_OUTPUT_DIR if from_db else IC_REPORTS_OUTPUT_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-factor research ranking.")
    parser.add_argument("--factor", action="append", dest="factors")
    parser.add_argument("--panel-csv")
    parser.add_argument("--from-db", action="store_true")
    parser.add_argument("--start-date", default="2018-01-01")
    parser.add_argument("--end-date")
    parser.add_argument("--time-series-window", action="append", dest="time_series_windows", type=int)
    parser.add_argument("--event-window", action="append", dest="event_windows", type=int)
    parser.add_argument(
        "--skip-chip-distribution",
        action="store_true",
        help="Skip stock_cyq_chips to avoid the heaviest chip-distribution query during publish runs.",
    )
    parser.add_argument("--target-col", default="overnight_return")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    output_dir = _resolve_output_dir(from_db=args.from_db, output_dir=args.output_dir)

    if args.from_db:
        result = run_full_factor_research(
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=output_dir,
            target_col=args.target_col,
            time_series_windows=tuple(args.time_series_windows or [5, 10, 20, 60]),
            event_windows=tuple(args.event_windows or [3, 5, 10, 20]),
            include_chip_distribution=not args.skip_chip_distribution,
        )
        result["snapshot"] = publish_research_snapshot(
            output_root=output_dir.parent,
            full_research_dir=output_dir,
        )
        print(json.dumps(result, ensure_ascii=False))
        return

    if not args.panel_csv or not args.factors:
        parser.error("--panel-csv and at least one --factor are required unless --from-db is used")

    panel = pd.read_csv(args.panel_csv)
    result = run_factor_research(panel, factor_cols=args.factors, target_col=args.target_col, output_dir=output_dir)
    print(json.dumps({"ranking_path": result["ranking_path"], "correlation_plot": result["correlation_plot"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
