from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_runtime_paths(app_dir: Path) -> dict:
    app_dir = Path(app_dir).resolve()
    repo_root = app_dir.parents[2]
    venv_dir = app_dir / ".venv"
    return {
        "app_dir": app_dir,
        "repo_root": repo_root,
        "venv_dir": venv_dir,
        "venv_python": venv_dir / "bin" / "python",
        "venv_pip": venv_dir / "bin" / "pip",
        "requirements_file": app_dir / "requirements.txt",
    }


def build_runtime_env(base_env: dict, repo_root: str) -> dict:
    env = dict(base_env)
    env["PYTHONNOUSERSITE"] = "1"
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{repo_root}:{existing_pythonpath}" if existing_pythonpath else str(repo_root)
    return env


def should_reexec(current_python: str, target_python: str) -> bool:
    return os.path.abspath(current_python) != os.path.abspath(target_python)


def should_reexec_for_arch(current_arch: str, runtime_arch: str | None) -> bool:
    return bool(runtime_arch) and current_arch != runtime_arch


def detect_binary_architectures(path: str | Path) -> set[str]:
    target_path = Path(path)
    if not target_path.exists():
        return set()

    result = subprocess.run(
        ["file", str(target_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    detected: set[str] = set()

    for arch_name in ("x86_64", "arm64"):
        if arch_name in output:
            detected.add(arch_name)

    return detected


def resolve_runtime_architecture(venv_dir: Path) -> str | None:
    candidates = sorted(venv_dir.glob("lib/python*/site-packages/pydantic_core/_pydantic_core*.so"))
    for candidate in candidates:
        candidate_archs = detect_binary_architectures(candidate)
        if "arm64" in candidate_archs:
            return "arm64"
        if "x86_64" in candidate_archs:
            return "x86_64"
    return None


def build_exec_args(target_python: str, runtime_arch: str | None = None) -> list[str]:
    if not runtime_arch:
        return [target_python]

    arch_binary = shutil.which("arch")
    if not arch_binary:
        return [target_python]

    python_archs = detect_binary_architectures(target_python)
    if python_archs and runtime_arch not in python_archs:
        return [target_python]

    return [arch_binary, f"-{runtime_arch}", target_python]


def _venv_has_runtime_dependencies(venv_python: Path) -> bool:
    if not venv_python.exists():
        return False

    result = subprocess.run(
        [str(venv_python), "-c", "import fastapi, uvicorn, pydantic"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def ensure_local_runtime(app_dir: Path, current_python: str = None) -> dict:
    paths = resolve_runtime_paths(app_dir)
    current_python = current_python or sys.executable

    needs_rebuild = paths["venv_python"].exists() and not _venv_has_runtime_dependencies(paths["venv_python"])
    if needs_rebuild:
        shutil.rmtree(paths["venv_dir"], ignore_errors=True)

    if needs_rebuild or not paths["venv_python"].exists():
        subprocess.run([current_python, "-m", "venv", str(paths["venv_dir"])], check=True)

    if not _venv_has_runtime_dependencies(paths["venv_python"]):
        subprocess.run(
            [str(paths["venv_pip"]), "install", "-q", "-r", str(paths["requirements_file"])],
            check=True,
            env=build_runtime_env(os.environ, str(paths["repo_root"])),
        )

    return paths
