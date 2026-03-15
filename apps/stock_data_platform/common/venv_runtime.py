from __future__ import annotations

import platform
from pathlib import Path


MANAGED_VENV_BASENAME = ".venv-stock-data"


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def normalize_arch(machine: str) -> str:
    normalized = machine.strip().lower()
    if normalized in {"arm64", "arm64e", "aarch64"}:
        return "arm64"
    if normalized in {"x86_64", "amd64", "i386"}:
        return "x86_64"
    return normalized


def current_arch(machine: str | None = None) -> str:
    return normalize_arch(machine or platform.machine())


def venv_dir(repo_root: Path | None = None, arch: str | None = None) -> Path:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    resolved_arch = current_arch(arch)
    return resolved_repo_root / f"{MANAGED_VENV_BASENAME}-{resolved_arch}"


def default_venv_link(repo_root: Path | None = None) -> Path:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    return resolved_repo_root / MANAGED_VENV_BASENAME


def python_bin(repo_root: Path | None = None, arch: str | None = None) -> Path:
    return venv_dir(repo_root, arch) / "bin" / "python"


def python_launcher_script(repo_root: Path | None = None) -> Path:
    resolved_repo_root = Path(repo_root) if repo_root is not None else default_repo_root()
    return resolved_repo_root / "apps" / "stock_data_platform" / "scripts" / "dispatch_stock_data_python.sh"
