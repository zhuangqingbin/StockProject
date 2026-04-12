from __future__ import annotations

import html
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _table_html(frame: pd.DataFrame, float_format: str = "{:.6f}") -> str:
    if frame.empty:
        return "<p>No data available.</p>"
    formatted = frame.copy()
    for column in formatted.columns:
        if pd.api.types.is_numeric_dtype(formatted[column]):
            formatted[column] = formatted[column].map(
                lambda value: "" if pd.isna(value) else float_format.format(float(value))
            )
    return formatted.to_html(index=False, escape=False)


def _render_html_document(title: str, sections: list[str]) -> str:
    body = "\n".join(sections)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px auto; max-width: 1120px; color: #1f2937; }}
    h1, h2 {{ color: #111827; }}
    .muted {{ color: #6b7280; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 24px 0; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; background: #fafafa; }}
    img {{ max-width: 100%; border: 1px solid #e5e7eb; border-radius: 10px; background: white; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
    .asset-list a {{ display: inline-block; margin-right: 12px; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


class ResearchReportBuilder:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_factor_report(
        self,
        factor_name: str,
        ic_result: dict[str, object],
        layered_result: dict[str, object],
        correlation_result: dict[str, object],
    ) -> dict[str, str]:
        summary_path = self.output_dir / f"{factor_name}_summary.csv"
        detail_html_path = self.output_dir / f"{factor_name}_detail.html"
        ic_series_path = self.output_dir / f"{factor_name}_ic_series.csv"
        group_returns_path = self.output_dir / f"{factor_name}_group_returns.csv"
        ic_plot_path = self.output_dir / f"{factor_name}_ic.png"
        layered_plot_path = self.output_dir / f"{factor_name}_layered.png"
        correlation_plot_path = self.output_dir / f"{factor_name}_correlation.png"

        summary = pd.DataFrame(
            [
                {
                    "factor_name": factor_name,
                    "mean_ic": ic_result.get("mean_ic", 0.0),
                    "rank_ic": ic_result.get("rank_ic", 0.0),
                    "ic_ir": ic_result.get("ic_ir", 0.0),
                    "positive_rate": ic_result.get("positive_rate", 0.0),
                    "p_value": ic_result.get("p_value", 1.0),
                    "coverage": ic_result.get("coverage", 0.0),
                    "trade_date_coverage": ic_result.get("trade_date_coverage", 0.0),
                    "active_trade_date_coverage": ic_result.get("active_trade_date_coverage", 0.0),
                    "rolling_1y_valid_ratio": ic_result.get("rolling_1y_valid_ratio", 0.0),
                    "passes_rolling_stability": ic_result.get("passes_rolling_stability", False),
                    "long_short_mean": layered_result.get("long_short_returns", pd.Series(dtype=float)).mean(),
                    "monotonicity": layered_result.get("monotonicity", 0.0),
                }
            ]
        )
        summary.to_csv(summary_path, index=False)

        ic_series = ic_result.get("ic_series", pd.DataFrame())
        if isinstance(ic_series, pd.DataFrame):
            ic_series.to_csv(ic_series_path, index=False)
        plt.figure(figsize=(8, 4))
        if not ic_series.empty:
            plt.plot(ic_series["trade_date"], ic_series["ic"], label="IC")
            plt.plot(ic_series["trade_date"], ic_series["rank_ic"], label="Rank IC")
            plt.xticks(rotation=45)
            plt.legend()
        plt.title(f"{factor_name} IC")
        plt.tight_layout()
        plt.savefig(ic_plot_path)
        plt.close()

        plt.figure(figsize=(8, 4))
        group_returns = layered_result.get("group_returns", pd.DataFrame())
        if isinstance(group_returns, pd.DataFrame):
            group_returns.to_csv(group_returns_path)
        if not group_returns.empty:
            for column in group_returns.columns:
                plt.plot(group_returns.index.astype(str), group_returns[column], label=f"G{column}")
            plt.legend()
            plt.xticks(rotation=45)
        plt.title(f"{factor_name} Layered Returns")
        plt.tight_layout()
        plt.savefig(layered_plot_path)
        plt.close()

        plt.figure(figsize=(6, 5))
        corr = correlation_result.get("correlation_matrix", pd.DataFrame())
        if not corr.empty:
            sns.heatmap(corr, annot=True, cmap="coolwarm", center=0.0)
        plt.title(f"{factor_name} Correlation")
        plt.tight_layout()
        plt.savefig(correlation_plot_path)
        plt.close()

        detail_html_path.write_text(
            _render_html_document(
                f"{factor_name} Factor Report",
                [
                    f"<h1>{html.escape(factor_name)} factor report</h1>",
                    "<p class='muted'>IC diagnostics, layered return behavior, and correlation snapshot for a single factor.</p>",
                    "<h2>Summary</h2>",
                    _table_html(summary),
                    "<div class='asset-list'>"
                    f"<a href='{summary_path.name}'>summary csv</a>"
                    f"<a href='{ic_series_path.name}'>ic series csv</a>"
                    f"<a href='{group_returns_path.name}'>group returns csv</a>"
                    "</div>",
                    "<div class='grid'>"
                    f"<div class='card'><h2>IC series</h2><img src='{ic_plot_path.name}' alt='IC plot'></div>"
                    f"<div class='card'><h2>Layered returns</h2><img src='{layered_plot_path.name}' alt='Layered returns plot'></div>"
                    f"<div class='card'><h2>Correlation</h2><img src='{correlation_plot_path.name}' alt='Correlation heatmap'></div>"
                    "</div>",
                    "<h2>IC sample</h2>",
                    _table_html(ic_series.head(20), float_format="{:.4f}"),
                    "<h2>Group return sample</h2>",
                    _table_html(group_returns.reset_index().head(20), float_format="{:.4f}"),
                ],
            ),
            encoding="utf-8",
        )

        return {
            "summary_csv": str(summary_path),
            "detail_html": str(detail_html_path),
            "ic_series_csv": str(ic_series_path),
            "group_returns_csv": str(group_returns_path),
            "ic_plot": str(ic_plot_path),
            "layered_plot": str(layered_plot_path),
            "correlation_heatmap": str(correlation_plot_path),
        }

    def build_correlation_report(
        self,
        correlation_result: dict[str, object],
        report_name: str = "factor_correlation",
    ) -> dict[str, str]:
        matrix = correlation_result.get("correlation_matrix", pd.DataFrame())
        matrix_path = self.output_dir / f"{report_name}_matrix.csv"
        heatmap_path = self.output_dir / f"{report_name}_heatmap.png"
        matrix.to_csv(matrix_path)

        plt.figure(figsize=(10, 8))
        if not matrix.empty:
            sns.heatmap(matrix, cmap="coolwarm", center=0.0)
        plt.title(report_name.replace("_", " ").title())
        plt.tight_layout()
        plt.savefig(heatmap_path)
        plt.close()

        return {
            "matrix_csv": str(matrix_path),
            "heatmap_png": str(heatmap_path),
        }

    def build_ranking_report(
        self,
        ranking: pd.DataFrame,
        report_name: str = "factor_ranking",
        title: str | None = None,
    ) -> dict[str, str]:
        ranking_path = self.output_dir / f"{report_name}.csv"
        html_path = self.output_dir / f"{report_name}.html"
        ranking.to_csv(ranking_path, index=False)
        top_columns = [column for column in ["factor_name", "mean_ic", "rank_ic", "ic_ir", "positive_rate", "coverage", "passes_research_gate"] if column in ranking.columns]
        html_path.write_text(
            _render_html_document(
                title or report_name.replace("_", " ").title(),
                [
                    f"<h1>{html.escape(title or report_name.replace('_', ' ').title())}</h1>",
                    f"<p class='muted'>Rows: {len(ranking)}</p>",
                    f"<p><a href='{ranking_path.name}'>download csv</a></p>",
                    _table_html(ranking.loc[:, top_columns].head(50) if top_columns else ranking.head(50)),
                ],
            ),
            encoding="utf-8",
        )
        return {
            "ranking_csv": str(ranking_path),
            "overview_html": str(html_path),
        }

    def build_strategy_comparison_report(
        self,
        comparison: pd.DataFrame,
        report_name: str = "strategy_comparison",
    ) -> dict[str, str]:
        csv_path = self.output_dir / f"{report_name}.csv"
        html_path = self.output_dir / f"{report_name}.html"
        plot_path = self.output_dir / f"{report_name}_sharpe.png"
        comparison.to_csv(csv_path, index=False)

        plt.figure(figsize=(10, 6))
        if not comparison.empty and {"strategy_name", "sharpe_ratio"}.issubset(comparison.columns):
            top = comparison.sort_values("sharpe_ratio", ascending=False).head(10)
            sns.barplot(data=top, y="strategy_name", x="sharpe_ratio", orient="h")
            plt.xlabel("Sharpe Ratio")
            plt.ylabel("Strategy")
        plt.title(report_name.replace("_", " ").title())
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        html_path.write_text(
            _render_html_document(
                report_name.replace("_", " ").title(),
                [
                    f"<h1>{html.escape(report_name.replace('_', ' ').title())}</h1>",
                    "<p class='muted'>Strategy-level comparison exported from composite factor backtests.</p>",
                    f"<p><a href='{csv_path.name}'>download csv</a></p>",
                    f"<div class='card'><h2>Sharpe leaderboard</h2><img src='{plot_path.name}' alt='Strategy comparison plot'></div>",
                    "<h2>Top strategies</h2>",
                    _table_html(comparison.head(20)),
                ],
            ),
            encoding="utf-8",
        )
        return {
            "comparison_csv": str(csv_path),
            "overview_html": str(html_path),
            "sharpe_plot": str(plot_path),
        }
