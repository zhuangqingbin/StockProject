from __future__ import annotations

from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_mkdocs_config() -> dict:
    return yaml.safe_load((_repo_root() / "mkdocs.yml").read_text(encoding="utf-8"))


def _read_site_page(relative_path: str) -> str:
    return (_repo_root() / "site_docs" / relative_path).read_text(encoding="utf-8")


def _collect_nav_paths(nav_items: list[object]) -> list[str]:
    paths: list[str] = []
    for item in nav_items:
        if not isinstance(item, dict):
            continue
        value = next(iter(item.values()))
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, list):
            paths.extend(_collect_nav_paths(value))
    return paths


def test_apps_requirements_include_mkdocs_stack():
    content = (_repo_root() / "apps" / "requirements.txt").read_text(encoding="utf-8")

    assert "mkdocs>=1.6" in content
    assert "mkdocs-material>=9.6" in content
    assert "pymdown-extensions>=10.0" in content


def test_gitignore_ignores_mkdocs_build_output():
    lines = (_repo_root() / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "site/" in lines


def test_mkdocs_config_uses_site_docs_and_explicit_nav():
    config = _load_mkdocs_config()
    top_labels = [next(iter(item)) for item in config["nav"]]

    assert config["site_name"] == "StockProject Docs"
    assert config["docs_dir"] == "site_docs"
    assert config["site_dir"] == "site"
    assert config["theme"]["name"] == "material"
    assert top_labels == [
        "Home",
        "Getting Started",
        "Data Hub",
        "Quant Platform",
        "Ops / Dev",
        "Repo Governance",
    ]


def test_all_nav_pages_exist_under_site_docs():
    repo_root = _repo_root()
    site_docs = repo_root / "site_docs"
    nav_paths = _collect_nav_paths(_load_mkdocs_config()["nav"])

    assert nav_paths
    for relative_path in nav_paths:
        assert (site_docs / relative_path).exists(), relative_path


def test_root_readme_mentions_docs_preview_command():
    content = (_repo_root() / "README.md").read_text(encoding="utf-8")

    assert "## Docs Portal" in content
    assert 'mkdocs serve' in content
    assert "`site_docs/`" in content


def test_data_hub_pages_cover_pipeline_and_explorer_entrypoints():
    overview = _read_site_page("data-hub/index.md")
    pipeline = _read_site_page("data-hub/data-pipeline-ts.md")
    ak = _read_site_page("data-hub/data-pipeline-ak.md")
    explorer = _read_site_page("data-hub/data-explorer.md")

    assert "`data_hub`" in overview
    assert "`data_pipeline_ts`" in overview
    assert "`data_pipeline_ak`" in overview
    assert "run_daily.sh" in pipeline
    assert "run_backfill.sh" in pipeline
    assert "stock_stk_factor_pro" in pipeline
    assert "AkShare" in ak
    assert "calendar.py" in ak
    assert "run.sh backend" in explorer
    assert "run.sh frontend" in explorer


def test_analysis_pages_document_strategy_suite_and_findings():
    overview = _read_site_page("data-hub/analysis/index.md")
    suite = _read_site_page("data-hub/analysis/strategy-suite.md")
    findings = _read_site_page("data-hub/analysis/findings.md")

    assert "bottom_volume_matrix" in overview
    assert "run_strategy_suite.py" in overview
    assert "suite_summary.csv" in suite
    assert "--strategies bottom_volume_matrix,limit_inst_matrix,top_list_matrix" in suite
    assert "首板涨停 + 主力大幅流入" in findings
    assert "跌停 + 主力大幅流出" in findings


def test_quant_platform_pages_cover_app_and_research_workflow():
    overview = _read_site_page("quant-platform/index.md")
    research = _read_site_page("quant-platform/research.md")

    assert "run.sh backend" in overview
    assert "run.sh frontend" in overview
    assert "`/research`" in research
    assert "research-factor --from-db" in research
    assert "run_full_pipeline" in research


def test_ops_and_governance_pages_cover_env_test_and_docs_boundaries():
    environment = _read_site_page("ops/environment.md")
    testing = _read_site_page("ops/testing.md")
    commands = _read_site_page("ops/common-commands.md")
    governance = _read_site_page("repo-governance/index.md")
    inventory = _read_site_page("repo-governance/inventory.md")

    assert "TUSHARE_TOKEN" in environment
    assert "TS_MYSQL_DATABASE" in environment
    assert "python -m pytest -q" in testing
    assert "npm --prefix apps/data_hub/data_explorer/frontend test" in testing
    assert "mkdocs serve" in commands
    assert "project-specific design and implementation notes" in governance
    assert "docs/ should only hold repo-wide material" in inventory
