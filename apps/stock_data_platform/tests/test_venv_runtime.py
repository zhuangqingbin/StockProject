from __future__ import annotations

import os
import subprocess
from pathlib import Path

import apps.stock_data_platform.common.venv_runtime as venv_runtime


def test_normalize_arch_handles_macos_aliases():
    assert venv_runtime.normalize_arch("arm64") == "arm64"
    assert venv_runtime.normalize_arch("arm64e") == "arm64"
    assert venv_runtime.normalize_arch("aarch64") == "arm64"
    assert venv_runtime.normalize_arch("x86_64") == "x86_64"
    assert venv_runtime.normalize_arch("amd64") == "x86_64"
    assert venv_runtime.normalize_arch("i386") == "x86_64"


def test_arch_specific_venv_paths_use_suffixes(tmp_path):
    repo_root = tmp_path / "repo"

    assert venv_runtime.venv_dir(repo_root, "arm64") == repo_root / ".venv-stock-data-arm64"
    assert venv_runtime.venv_dir(repo_root, "x86_64") == repo_root / ".venv-stock-data-x86_64"
    assert venv_runtime.default_venv_link(repo_root) == repo_root / ".venv-stock-data"


def test_python_bin_and_dispatcher_script_paths_are_stable(tmp_path):
    repo_root = tmp_path / "repo"

    assert venv_runtime.python_bin(repo_root, "arm64") == repo_root / ".venv-stock-data-arm64" / "bin" / "python"
    assert venv_runtime.python_bin(repo_root, "x86_64") == repo_root / ".venv-stock-data-x86_64" / "bin" / "python"
    assert venv_runtime.python_launcher_script(repo_root) == (
        repo_root / "apps" / "stock_data_platform" / "scripts" / "dispatch_stock_data_python.sh"
    )


def test_system_python_can_import_venv_runtime_without_optional_runtime_dependencies():
    repo_root = Path.cwd()
    system_python = "/Library/Developer/CommandLineTools/usr/bin/python3"
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        [system_python, "-c", "from apps.stock_data_platform.common.venv_runtime import current_arch; print(current_arch())"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
