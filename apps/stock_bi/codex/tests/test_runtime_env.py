from pathlib import Path

from apps.stock_bi.codex.launch_env import (
    build_exec_args,
    build_runtime_env,
    resolve_runtime_paths,
    should_reexec_for_arch,
    should_reexec,
)


def test_build_runtime_env_disables_user_site_and_prepends_repo_root():
    env = build_runtime_env(
        {"PYTHONPATH": "/existing/path", "OTHER": "value"},
        repo_root="/repo/root",
    )

    assert env["PYTHONNOUSERSITE"] == "1"
    assert env["PYTHONPATH"] == "/repo/root:/existing/path"
    assert env["OTHER"] == "value"


def test_resolve_runtime_paths_returns_repo_and_venv_locations():
    app_dir = Path("/tmp/worktree/apps/stock_bi/codex")
    resolved_app_dir = app_dir.resolve()

    paths = resolve_runtime_paths(app_dir)

    assert paths["app_dir"] == resolved_app_dir
    assert paths["repo_root"] == resolved_app_dir.parents[2]
    assert paths["venv_dir"] == resolved_app_dir / ".venv"
    assert paths["venv_python"] == resolved_app_dir / ".venv" / "bin" / "python"
    assert paths["venv_pip"] == resolved_app_dir / ".venv" / "bin" / "pip"


def test_should_reexec_only_when_current_python_differs_from_target():
    assert should_reexec("/usr/bin/python3", "/tmp/.venv/bin/python") is True
    assert should_reexec("/tmp/.venv/bin/python", "/tmp/.venv/bin/python") is False


def test_should_reexec_for_arch_only_when_runtime_arch_differs():
    assert should_reexec_for_arch("x86_64", "arm64") is True
    assert should_reexec_for_arch("arm64", "arm64") is False
    assert should_reexec_for_arch("x86_64", None) is False


def test_build_exec_args_uses_arch_wrapper_when_python_supports_target(monkeypatch):
    monkeypatch.setattr(
        "apps.stock_bi.codex.launch_env.detect_binary_architectures",
        lambda path: {"x86_64", "arm64"},
    )
    monkeypatch.setattr("apps.stock_bi.codex.launch_env.shutil.which", lambda name: "/usr/bin/arch")

    assert build_exec_args("/tmp/.venv/bin/python", "arm64") == [
        "/usr/bin/arch",
        "-arm64",
        "/tmp/.venv/bin/python",
    ]


def test_build_exec_args_skips_arch_wrapper_when_python_lacks_target(monkeypatch):
    monkeypatch.setattr(
        "apps.stock_bi.codex.launch_env.detect_binary_architectures",
        lambda path: {"x86_64"},
    )
    monkeypatch.setattr("apps.stock_bi.codex.launch_env.shutil.which", lambda name: "/usr/bin/arch")

    assert build_exec_args("/tmp/.venv/bin/python", "arm64") == ["/tmp/.venv/bin/python"]
