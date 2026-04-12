from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RESEARCH_ROOT = Path(__file__).resolve().parents[2] / "research"
OUTPUT_ROOT = RESEARCH_ROOT / "output"
ASSET_BASE_URL = "/research-assets"

COMMANDS = [
    {
        "name": "research-publish",
        "description": "发布前端研究快照，生成因子推荐股票和钻取 JSON",
        "command": "bash apps/quant_platform/scripts/run.sh research-publish --from-db --start-date 2018-01-01",
    },
    {
        "name": "research-notebook",
        "description": "启动 Jupyter Lab，浏览研究模板 notebook",
        "command": "bash apps/quant_platform/scripts/run.sh research-notebook",
    },
    {
        "name": "research-single",
        "description": "对单个因子执行 IC 与分层回测",
        "command": "bash apps/quant_platform/scripts/run.sh research-single --factor pct_chg",
    },
    {
        "name": "research-factor",
        "description": "生成多因子排行榜、相关性和研究报告",
        "command": "bash apps/quant_platform/scripts/run.sh research-factor --panel-csv /path/to/panel.csv --factor pct_chg --factor net_mf_rate",
    },
    {
        "name": "research-backtest",
        "description": "对组合因子执行策略回测",
        "command": "bash apps/quant_platform/scripts/run.sh research-backtest --panel-csv /path/to/panel.csv --factor alpha_1 --factor alpha_2",
    },
]

SAMPLE_SPLITS = [
    {"name": "训练集", "start_date": "2018-01-01", "end_date": "2023-12-31", "purpose": "因子挖掘、IC 分析、参数调优"},
    {"name": "验证集", "start_date": "2024-01-01", "end_date": "2025-06-30", "purpose": "因子筛选、组合方法选择"},
    {"name": "测试集", "start_date": "2025-07-01", "end_date": "至今", "purpose": "样本外最终评估，仅用于最终报告"},
]


def _iso_timestamp(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _list_module_names(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("*.py") if path.stem != "__init__")


def _list_notebooks(directory: Path, base_dir: Path) -> list[dict[str, str]]:
    if not directory.exists():
        return []
    return [
        {
            "name": path.name,
            "stem": path.stem,
            "relative_path": path.relative_to(base_dir).as_posix(),
        }
        for path in sorted(directory.glob("*.ipynb"))
    ]


def _asset_url(path: Path, output_dir: Path, asset_base_url: str) -> str | None:
    if not path.exists():
        return None
    return f"{asset_base_url.rstrip('/')}/{path.relative_to(output_dir).as_posix()}"


def _json_records(frame: pd.DataFrame, limit: int | None = None) -> list[dict[str, object]]:
    view = frame if limit is None else frame.head(limit)
    return json.loads(view.to_json(orient="records", force_ascii=False))


def _load_latest_ranking(output_dir: Path) -> dict[str, object]:
    candidates = [
        (
            output_dir / "serving" / "latest" / "factors.json",
            "serving_snapshot",
            lambda path: _load_serving_ranking(path),
        ),
        (
            output_dir / "full_research" / "qualified_factor_summary.csv",
            "qualified_factor_summary",
            lambda path: _load_csv_ranking(path, output_dir),
        ),
        (
            output_dir / "full_research" / "split_factor_summary.csv",
            "split_factor_summary",
            lambda path: _load_csv_ranking(path, output_dir),
        ),
        (
            output_dir / "ic_reports" / "factor_ranking.csv",
            "factor_ranking",
            lambda path: _load_csv_ranking(path, output_dir),
        ),
    ]

    for path, source_name, loader in candidates:
        ranking = loader(path)
        if ranking["available"]:
            ranking["source"] = source_name
            return ranking
    return {"available": False, "row_count": 0, "rows": [], "updated_at": None, "source": None}


def _load_serving_ranking(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"available": False, "row_count": 0, "rows": [], "updated_at": None}

    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    if not rows:
        return {"available": False, "row_count": 0, "rows": [], "updated_at": _iso_timestamp(path)}

    return {
        "available": True,
        "row_count": int(payload.get("row_count", len(rows))),
        "rows": rows[:10],
        "updated_at": _iso_timestamp(path),
        "relative_path": path.relative_to(path.parents[2]).as_posix(),
        "overview_html": None,
        "latest_trade_date": payload.get("latest_trade_date"),
        "supports_picks": bool(payload.get("supports_picks", False)),
    }


def _load_csv_ranking(path: Path, output_dir: Path) -> dict[str, object]:
    if not path.exists():
        return {"available": False, "row_count": 0, "rows": [], "updated_at": None}

    ranking = pd.read_csv(path)
    if ranking.empty:
        return {"available": False, "row_count": 0, "rows": [], "updated_at": _iso_timestamp(path)}

    html_path = path.with_suffix(".html")
    return {
        "available": True,
        "row_count": int(len(ranking)),
        "rows": _json_records(ranking, limit=10),
        "updated_at": _iso_timestamp(path),
        "relative_path": path.relative_to(output_dir.parent).as_posix(),
        "overview_html": _asset_url(html_path, output_dir, asset_base_url="/research-assets"),
    }


def _load_factor_reports(ic_dir: Path, output_dir: Path, asset_base_url: str) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for summary_path in sorted(ic_dir.glob("*_summary.csv")):
        factor_name = summary_path.name[: -len("_summary.csv")]
        summary_frame = pd.read_csv(summary_path)
        summary = _json_records(summary_frame, limit=1)[0] if not summary_frame.empty else {}
        reports.append(
            {
                "factor_name": factor_name,
                "summary": summary,
                "updated_at": _iso_timestamp(summary_path),
                "assets": {
                    "detail_html": _asset_url(ic_dir / f"{factor_name}_detail.html", output_dir, asset_base_url),
                    "ic_plot": _asset_url(ic_dir / f"{factor_name}_ic.png", output_dir, asset_base_url),
                    "layered_plot": _asset_url(ic_dir / f"{factor_name}_layered.png", output_dir, asset_base_url),
                    "correlation_heatmap": _asset_url(ic_dir / f"{factor_name}_correlation.png", output_dir, asset_base_url),
                    "ic_series_csv": _asset_url(ic_dir / f"{factor_name}_ic_series.csv", output_dir, asset_base_url),
                    "group_returns_csv": _asset_url(ic_dir / f"{factor_name}_group_returns.csv", output_dir, asset_base_url),
                },
            }
        )
    return reports


def _load_strategy_runs(backtest_dir: Path, output_dir: Path, asset_base_url: str) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for json_path in sorted(backtest_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        runs.append(
            {
                "name": json_path.stem,
                "updated_at": _iso_timestamp(json_path),
                "relative_path": json_path.relative_to(output_dir.parent).as_posix(),
                "asset_url": _asset_url(json_path, output_dir, asset_base_url),
                "summary": json.loads(json_path.read_text(encoding="utf-8")),
            }
        )
    return runs


def _load_summary_artifact(output_dir: Path, name: str, asset_base_url: str) -> dict[str, object]:
    candidates = [
        (output_dir / "full_research" / f"{name}.csv", output_dir / "full_research" / f"{name}.html"),
        (output_dir / f"{name}.csv", output_dir / f"{name}.html"),
    ]

    selected_paths: tuple[Path, Path] | None = None
    for csv_path, html_path in candidates:
        if csv_path.exists():
            selected_paths = (csv_path, html_path)
            break

    if selected_paths is None:
        return {"available": False, "row_count": 0, "rows": [], "updated_at": None}

    csv_path, html_path = selected_paths
    frame = pd.read_csv(csv_path)
    return {
        "available": True,
        "row_count": int(len(frame)),
        "rows": _json_records(frame, limit=10),
        "updated_at": _iso_timestamp(csv_path),
        "asset_url": _asset_url(csv_path, output_dir, asset_base_url),
        "overview_html": _asset_url(html_path, output_dir, asset_base_url),
    }


def _load_strategy_comparison(output_dir: Path, asset_base_url: str) -> dict[str, object]:
    csv_path = output_dir / "strategy_comparison.csv"
    html_path = output_dir / "strategy_comparison.html"
    plot_path = output_dir / "strategy_comparison_sharpe.png"
    if not csv_path.exists():
        return {"available": False, "row_count": 0, "rows": [], "updated_at": None}
    comparison = pd.read_csv(csv_path)
    return {
        "available": True,
        "row_count": int(len(comparison)),
        "rows": _json_records(comparison, limit=10),
        "updated_at": _iso_timestamp(csv_path),
        "asset_url": _asset_url(csv_path, output_dir, asset_base_url),
        "overview_html": _asset_url(html_path, output_dir, asset_base_url),
        "sharpe_plot": _asset_url(plot_path, output_dir, asset_base_url),
    }


def get_research_overview(
    base_dir: Path | str | None = None,
    asset_base_url: str = ASSET_BASE_URL,
) -> dict[str, object]:
    research_root = Path(base_dir) if base_dir is not None else RESEARCH_ROOT
    output_dir = research_root / "output"
    ic_dir = output_dir / "ic_reports"
    backtest_dir = output_dir / "backtest_results"

    factor_modules = _list_module_names(research_root / "factor_engine")
    analyzer_modules = _list_module_names(research_root / "analyzer")
    strategy_modules = _list_module_names(research_root / "strategy")
    notebooks = _list_notebooks(research_root / "notebooks", research_root)
    latest_ranking = _load_latest_ranking(output_dir)
    factor_reports = _load_factor_reports(ic_dir, output_dir, asset_base_url)
    strategy_runs = _load_strategy_runs(backtest_dir, output_dir, asset_base_url)
    split_summary = _load_summary_artifact(output_dir, "split_factor_summary", asset_base_url)
    qualified_summary = _load_summary_artifact(output_dir, "qualified_factor_summary", asset_base_url)
    strategy_comparison = _load_strategy_comparison(output_dir, asset_base_url)
    status = "ready" if latest_ranking["available"] or factor_reports or strategy_runs else "empty"

    return {
        "goal": "基于 tushare_database 构建 A 股次日开盘收益预测因子，并将有效因子转成可回测组合策略。",
        "target_formula": "overnight_return = (T+1 open - T close) / T close",
        "catalog": {
            "factor_modules": factor_modules,
            "factor_module_count": len(factor_modules),
            "analyzer_modules": analyzer_modules,
            "analyzer_module_count": len(analyzer_modules),
            "strategy_modules": strategy_modules,
            "strategy_module_count": len(strategy_modules),
            "notebooks": notebooks,
            "notebook_count": len(notebooks),
        },
        "commands": COMMANDS,
        "sample_splits": SAMPLE_SPLITS,
        "outputs": {
            "status": status,
            "asset_base_url": asset_base_url,
            "latest_ranking": latest_ranking,
            "split_factor_summary": split_summary,
            "qualified_factor_summary": qualified_summary,
            "factor_reports": factor_reports,
            "strategy_runs": strategy_runs,
            "strategy_comparison": strategy_comparison,
            "artifact_counts": {
                "ic_reports": len(list(ic_dir.glob("*_summary.csv"))) if ic_dir.exists() else 0,
                "backtest_results": len(strategy_runs),
            },
        },
    }
