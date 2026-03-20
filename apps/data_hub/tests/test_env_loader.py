from __future__ import annotations

from pathlib import Path

from shared.stock_core.env import discover_env_files


def test_discover_env_files_prefers_dot_env_dot_local_name(tmp_path: Path):
    repo_root = tmp_path / "repo"
    nested_dir = repo_root / "apps" / "data_hub"
    nested_dir.mkdir(parents=True)

    (repo_root / ".env").write_text("ROOT_ENV=1\n", encoding="utf-8")
    (repo_root / ".env_local").write_text("LEGACY_LOCAL=1\n", encoding="utf-8")
    (repo_root / ".env.local").write_text("ROOT_LOCAL=1\n", encoding="utf-8")

    discovered = discover_env_files(start_dir=nested_dir, repo_root=repo_root)

    assert discovered == [
        repo_root / ".env.local",
        repo_root / ".env",
    ]


def test_repo_uses_env_example_file_name() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    assert (repo_root / "env.example").exists()
    assert not (repo_root / ".env_example").exists()
