import os
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
    return os.path.realpath(current_python) != os.path.realpath(target_python)


def ensure_local_runtime(app_dir: Path, current_python: str = None) -> dict:
    paths = resolve_runtime_paths(app_dir)
    current_python = current_python or sys.executable

    if paths["venv_python"].exists():
        return paths

    subprocess.run([current_python, "-m", "venv", str(paths["venv_dir"])], check=True)
    subprocess.run(
        [str(paths["venv_pip"]), "install", "-q", "-r", str(paths["requirements_file"])],
        check=True,
        env=build_runtime_env(os.environ, str(paths["repo_root"])),
    )
    return paths
