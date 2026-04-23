from __future__ import annotations

from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_mkdocs_config() -> dict:
    return yaml.safe_load((_repo_root() / "mkdocs.yml").read_text(encoding="utf-8"))


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


def test_top_level_site_docs_pages_exist():
    repo_root = _repo_root()
    assert (repo_root / "site_docs" / "index.md").exists()
    assert (repo_root / "site_docs" / "getting-started.md").exists()


def test_root_readme_mentions_docs_preview_command():
    content = (_repo_root() / "README.md").read_text(encoding="utf-8")

    assert "## Docs Portal" in content
    assert "mkdocs serve" in content
    assert "`site_docs/`" in content
