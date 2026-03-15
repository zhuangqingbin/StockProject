from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from apps.stock_data_platform.common.venv_runtime import (
    current_arch,
    default_repo_root as venv_default_repo_root,
    python_bin,
    python_launcher_script,
)


PROJECT_KERNEL_NAME = "stock-data-platform"
PROJECT_KERNEL_DISPLAY_NAME = "Python (stock_data_platform)"
DEFAULT_KERNEL_NAME = "python3"
DEFAULT_KERNEL_DISPLAY_NAME = "Python 3"


def default_repo_root() -> Path:
    return venv_default_repo_root()


def project_venv_python(repo_root: Path | None = None, arch: str | None = None) -> Path:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    return python_bin(resolved_repo_root, arch)


def project_kernel_spec_path() -> Path:
    return Path.home() / "Library" / "Jupyter" / "kernels" / PROJECT_KERNEL_NAME / "kernel.json"


def default_kernel_spec_path() -> Path:
    return Path.home() / "Library" / "Jupyter" / "kernels" / DEFAULT_KERNEL_NAME / "kernel.json"


def legacy_default_kernel_spec_path() -> Path:
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return Path.home() / "Library" / "Python" / version / "share" / "jupyter" / "kernels" / DEFAULT_KERNEL_NAME / "kernel.json"


def build_kernel_install_command(repo_root: Path | None = None, arch: str | None = None) -> list[str]:
    resolved_python_bin = project_venv_python(repo_root, arch)
    return [
        str(resolved_python_bin),
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        PROJECT_KERNEL_NAME,
        "--display-name",
        PROJECT_KERNEL_DISPLAY_NAME,
    ]


def build_default_kernel_install_command(repo_root: Path | None = None, arch: str | None = None) -> list[str]:
    resolved_python_bin = project_venv_python(repo_root, arch)
    return [
        str(resolved_python_bin),
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        DEFAULT_KERNEL_NAME,
        "--display-name",
        DEFAULT_KERNEL_DISPLAY_NAME,
    ]


def build_jupyterlab_command(repo_root: Path | None = None) -> list[str]:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    return [
        str(python_launcher_script(resolved_repo_root)),
        "-m",
        "jupyterlab",
    ]


def _run(command: Sequence[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(list(command), check=True, env=env)


def ensure_kernel_spec_defaults(kernel_spec_path: Path, launcher_script: Path, display_name: str) -> Path:
    payload = json.loads(Path(kernel_spec_path).read_text(encoding="utf-8"))
    payload["argv"] = [
        str(launcher_script),
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]
    payload["display_name"] = display_name
    payload["language"] = "python"
    payload.setdefault("metadata", {})
    payload.setdefault("env", {})
    payload["env"]["PYTHONNOUSERSITE"] = "1"
    Path(kernel_spec_path).write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return Path(kernel_spec_path)


def ensure_kernel_spec_env(kernel_spec_path: Path | None = None) -> Path:
    resolved_kernel_spec_path = Path(kernel_spec_path) if kernel_spec_path is not None else project_kernel_spec_path()
    payload = json.loads(resolved_kernel_spec_path.read_text(encoding="utf-8"))
    payload.setdefault("env", {})
    payload["env"]["PYTHONNOUSERSITE"] = "1"
    resolved_kernel_spec_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return resolved_kernel_spec_path


def ensure_project_kernel(repo_root: Path | None = None) -> None:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    resolved_arch = current_arch()
    resolved_python_bin = project_venv_python(resolved_repo_root, resolved_arch)
    if not resolved_python_bin.exists():
        raise FileNotFoundError(
            f"Missing stock_data_platform venv for {resolved_arch}: {resolved_python_bin.parent.parent}. "
            "Run: bash apps/stock_data_platform/scripts/setup_stock_data_daily_env.sh"
        )

    launcher_script = python_launcher_script(resolved_repo_root)
    _run(build_kernel_install_command(resolved_repo_root, arch=resolved_arch))
    _run(build_default_kernel_install_command(resolved_repo_root, arch=resolved_arch))
    ensure_kernel_spec_defaults(project_kernel_spec_path(), launcher_script, PROJECT_KERNEL_DISPLAY_NAME)
    ensure_kernel_spec_defaults(default_kernel_spec_path(), launcher_script, DEFAULT_KERNEL_DISPLAY_NAME)

    legacy_kernel_spec = legacy_default_kernel_spec_path()
    if legacy_kernel_spec.exists():
        ensure_kernel_spec_defaults(legacy_kernel_spec, launcher_script, DEFAULT_KERNEL_DISPLAY_NAME)


def launch_jupyterlab(repo_root: Path | None = None, extra_args: Sequence[str] = ()) -> None:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"

    command = [
        *build_jupyterlab_command(resolved_repo_root),
        *extra_args,
    ]
    _run(command, env=env)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run JupyterLab for stock_data_platform using the project venv.")
    parser.add_argument(
        "--install-kernel-only",
        action="store_true",
        help="Only install the project Jupyter kernel and exit.",
    )
    parser.add_argument(
        "jupyter_args",
        nargs="*",
        help="Extra arguments passed through to jupyterlab.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ensure_project_kernel()

    if args.install_kernel_only:
        print(f"Installed Jupyter kernel: {PROJECT_KERNEL_NAME}")
        return 0

    launch_jupyterlab(extra_args=args.jupyter_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
