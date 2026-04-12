import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.quant_platform.app.api import research as research_api
from apps.quant_platform.app.services.research_service import get_research_overview


def test_get_research_overview_collects_catalog_and_outputs(tmp_path):
    research_root = tmp_path / "research"
    (research_root / "factor_engine").mkdir(parents=True)
    (research_root / "analyzer").mkdir()
    (research_root / "strategy").mkdir()
    (research_root / "notebooks").mkdir()
    (research_root / "scripts").mkdir()
    ic_dir = research_root / "output" / "ic_reports"
    backtest_dir = research_root / "output" / "backtest_results"
    ic_dir.mkdir(parents=True)
    backtest_dir.mkdir(parents=True)

    for path in [
        research_root / "factor_engine" / "technical.py",
        research_root / "factor_engine" / "money_flow.py",
        research_root / "analyzer" / "ic_analysis.py",
        research_root / "strategy" / "portfolio_backtest.py",
        research_root / "notebooks" / "02_single_factor_analysis.ipynb",
        research_root / "scripts" / "run_factor_research.py",
    ]:
        path.write_text("# fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "mean_ic": 0.032, "rank_ic": 0.041, "ic_ir": 0.83, "positive_rate": 0.61},
            {"factor_name": "flow_momentum", "mean_ic": 0.021, "rank_ic": 0.029, "ic_ir": 0.55, "positive_rate": 0.57},
        ]
    ).to_csv(ic_dir / "factor_ranking.csv", index=False)
    (ic_dir / "factor_ranking.html").write_text("<html></html>", encoding="utf-8")
    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "mean_ic": 0.032, "rank_ic": 0.041, "ic_ir": 0.83, "positive_rate": 0.61},
        ]
    ).to_csv(ic_dir / "alpha_quality_summary.csv", index=False)
    (ic_dir / "alpha_quality_detail.html").write_text("<html></html>", encoding="utf-8")
    (ic_dir / "alpha_quality_ic_series.csv").write_text("trade_date,ic\n2026-01-01,0.03\n", encoding="utf-8")
    (ic_dir / "alpha_quality_group_returns.csv").write_text("trade_date,1,5\n2026-01-01,0.01,0.03\n", encoding="utf-8")
    for suffix in ["ic", "layered", "correlation"]:
        (ic_dir / f"alpha_quality_{suffix}.png").write_bytes(b"png")

    (backtest_dir / "strategy_summary.json").write_text(
        json.dumps({"final_nav": 1.18, "annual_return": 0.26, "sharpe_ratio": 1.41}),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "train_ic_ir": 0.8, "validation_ic_ir": 0.5, "passes_research_gate": True},
        ]
    ).to_csv(research_root / "output" / "qualified_factor_summary.csv", index=False)
    (research_root / "output" / "qualified_factor_summary.html").write_text("<html></html>", encoding="utf-8")
    pd.DataFrame(
        [
            {"strategy_name": "ml_top10pct", "sharpe_ratio": 1.4, "annual_return": 0.3},
        ]
    ).to_csv(research_root / "output" / "strategy_comparison.csv", index=False)
    (research_root / "output" / "strategy_comparison.html").write_text("<html></html>", encoding="utf-8")
    (research_root / "output" / "strategy_comparison_sharpe.png").write_bytes(b"png")

    overview = get_research_overview(base_dir=research_root, asset_base_url="/research-assets")

    assert overview["catalog"]["factor_module_count"] == 2
    assert overview["catalog"]["analyzer_module_count"] == 1
    assert overview["catalog"]["strategy_module_count"] == 1
    assert overview["catalog"]["notebook_count"] == 1
    assert overview["outputs"]["status"] == "ready"
    assert overview["outputs"]["latest_ranking"]["row_count"] == 2
    assert overview["outputs"]["latest_ranking"]["rows"][0]["factor_name"] == "alpha_quality"
    assert overview["outputs"]["latest_ranking"]["overview_html"] == "/research-assets/ic_reports/factor_ranking.html"
    assert overview["outputs"]["factor_reports"][0]["factor_name"] == "alpha_quality"
    assert overview["outputs"]["factor_reports"][0]["assets"]["ic_plot"] == "/research-assets/ic_reports/alpha_quality_ic.png"
    assert overview["outputs"]["factor_reports"][0]["assets"]["detail_html"] == "/research-assets/ic_reports/alpha_quality_detail.html"
    assert overview["outputs"]["qualified_factor_summary"]["row_count"] == 1
    assert overview["outputs"]["strategy_comparison"]["rows"][0]["strategy_name"] == "ml_top10pct"
    assert overview["outputs"]["strategy_runs"][0]["summary"]["final_nav"] == 1.18
    assert any(item["name"] == "research-factor" for item in overview["commands"])


def test_get_research_overview_prefers_serving_snapshot_for_latest_ranking(tmp_path):
    research_root = tmp_path / "research"
    serving_dir = research_root / "output" / "serving" / "latest"
    ic_dir = research_root / "output" / "ic_reports"
    serving_dir.mkdir(parents=True)
    ic_dir.mkdir(parents=True)

    (serving_dir / "factors.json").write_text(
        json.dumps(
            {
                "available": True,
                "row_count": 3,
                "latest_trade_date": "2026-04-03",
                "supports_picks": True,
                "rows": [
                    {"factor_name": "quality_alpha", "ic_ir": 1.2},
                    {"factor_name": "flow_beta", "ic_ir": 0.9},
                    {"factor_name": "event_gamma", "ic_ir": 0.7},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "mean_ic": 0.032, "rank_ic": 0.041, "ic_ir": 0.83, "positive_rate": 0.61},
        ]
    ).to_csv(ic_dir / "factor_ranking.csv", index=False)

    overview = get_research_overview(base_dir=research_root, asset_base_url="/research-assets")

    assert overview["outputs"]["latest_ranking"]["row_count"] == 3
    assert overview["outputs"]["latest_ranking"]["rows"][0]["factor_name"] == "quality_alpha"
    assert overview["outputs"]["latest_ranking"]["source"] == "serving_snapshot"
    assert overview["outputs"]["latest_ranking"]["supports_picks"] is True
    assert overview["outputs"]["latest_ranking"]["overview_html"] is None


def test_get_research_overview_reads_split_and_qualified_summaries_from_full_research(tmp_path):
    research_root = tmp_path / "research"
    full_research_dir = research_root / "output" / "full_research"
    full_research_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "train_ic_ir": 0.8, "validation_ic_ir": 0.5, "passes_research_gate": True},
        ]
    ).to_csv(full_research_dir / "split_factor_summary.csv", index=False)
    (full_research_dir / "split_factor_summary.html").write_text("<html></html>", encoding="utf-8")
    pd.DataFrame(
        [
            {"factor_name": "alpha_quality", "train_ic_ir": 0.8, "validation_ic_ir": 0.5, "passes_research_gate": True},
        ]
    ).to_csv(full_research_dir / "qualified_factor_summary.csv", index=False)
    (full_research_dir / "qualified_factor_summary.html").write_text("<html></html>", encoding="utf-8")

    overview = get_research_overview(base_dir=research_root, asset_base_url="/research-assets")

    assert overview["outputs"]["split_factor_summary"]["row_count"] == 1
    assert overview["outputs"]["split_factor_summary"]["asset_url"] == "/research-assets/full_research/split_factor_summary.csv"
    assert overview["outputs"]["qualified_factor_summary"]["row_count"] == 1
    assert overview["outputs"]["qualified_factor_summary"]["asset_url"] == "/research-assets/full_research/qualified_factor_summary.csv"


def test_research_overview_route_wraps_service_payload(monkeypatch):
    app = FastAPI()
    app.include_router(research_api.router)
    payload = {"catalog": {"factor_module_count": 12}, "outputs": {"status": "empty"}}
    monkeypatch.setattr(research_api, "get_research_overview", lambda: payload)

    client = TestClient(app)
    response = client.get("/api/research/overview")

    assert response.status_code == 200
    assert response.json() == {"code": 0, "data": payload}


def test_research_notebooks_are_populated_templates():
    notebook_root = Path(__file__).resolve().parents[1] / "research" / "notebooks"
    notebook_paths = sorted(notebook_root.glob("*.ipynb"))

    assert len(notebook_paths) == 5
    for path in notebook_paths:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells = notebook.get("cells", [])
        assert len(cells) >= 4
        assert any(cell.get("cell_type") == "markdown" for cell in cells)
        assert any(cell.get("cell_type") == "code" for cell in cells)
