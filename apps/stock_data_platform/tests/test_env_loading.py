import os
from pathlib import Path

from shared.stock_core.env import discover_env_files, load_env_files


def test_discover_env_files_includes_cwd_repo_and_primary_checkout(tmp_path, monkeypatch):
    primary_root = tmp_path / "StockProject"
    worktree_root = primary_root / ".worktrees" / "refactor-stock-bi-modules"
    app_dir = worktree_root / "apps" / "stock_bi" / "codex"
    app_dir.mkdir(parents=True)

    repo_env = worktree_root / ".env"
    app_env = app_dir / ".env.local"
    primary_env = primary_root / ".env"
    repo_env.write_text("WORKTREE=1\n")
    app_env.write_text("APP=1\n")
    primary_env.write_text("PRIMARY=1\n")

    monkeypatch.chdir(app_dir)

    env_files = discover_env_files(start_dir=app_dir, repo_root=worktree_root)

    assert env_files == [app_env, repo_env, primary_env]


def test_load_env_files_sets_missing_values_without_overriding_existing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "MYSQL_USER=stock_user",
                "MYSQL_PASSWORD=secret pass",
                "EMPTY_VALUE=",
            ]
        )
    )

    monkeypatch.setenv("MYSQL_USER", "existing_user")
    env = {"MYSQL_USER": os.environ["MYSQL_USER"]}

    loaded = load_env_files([env_file], environ=env, override=False)

    assert loaded == [env_file]
    assert env["MYSQL_USER"] == "existing_user"
    assert env["MYSQL_PASSWORD"] == "secret pass"
    assert env["EMPTY_VALUE"] == ""
