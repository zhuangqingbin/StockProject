from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_apps_requirements_include_mkdocs_stack():
    content = (_repo_root() / "apps" / "requirements.txt").read_text(encoding="utf-8")

    assert "mkdocs>=1.6" in content
    assert "mkdocs-material>=9.6" in content
    assert "pymdown-extensions>=10.0" in content


def test_gitignore_ignores_mkdocs_build_output():
    lines = (_repo_root() / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "site/" in lines
