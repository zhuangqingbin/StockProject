import os
from pathlib import Path
from typing import Iterable, Optional, Tuple


def _iter_candidate_paths(directory: Path) -> Iterable[Path]:
    yield directory / ".env.local"
    yield directory / ".env"


def _primary_checkout_root(repo_root: Path) -> Optional[Path]:
    parts = repo_root.parts
    if ".worktrees" not in parts:
        return None
    index = parts.index(".worktrees")
    return Path(*parts[:index]) if index > 0 else Path(repo_root.anchor)


def discover_env_files(start_dir: Path, repo_root: Path) -> list[Path]:
    start_dir = Path(start_dir).resolve()
    repo_root = Path(repo_root).resolve()

    candidates: list[Path] = []
    seen: set[Path] = set()

    current = start_dir
    while True:
        for path in _iter_candidate_paths(current):
            resolved = path.resolve()
            if path.exists() and resolved not in seen:
                seen.add(resolved)
                candidates.append(path)
        if current == repo_root:
            break
        if repo_root not in current.parents:
            break
        current = current.parent

    primary_root = _primary_checkout_root(repo_root)
    if primary_root is not None:
        for path in _iter_candidate_paths(primary_root):
            resolved = path.resolve()
            if path.exists() and resolved not in seen:
                seen.add(resolved)
                candidates.append(path)

    return candidates


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    return key.strip(), value.strip()


def load_env_files(paths: Iterable[Path], environ: Optional[dict] = None, override: bool = False) -> list[Path]:
    environ = environ if environ is not None else os.environ
    loaded: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            parsed = _parse_env_line(line)
            if parsed is None:
                continue
            key, value = parsed
            if override or key not in environ:
                environ[key] = value
        loaded.append(path)
    return loaded


def bootstrap_project_env(module_file: str) -> list[Path]:
    repo_root = Path(module_file).resolve().parents[2]
    start_dir = Path.cwd().resolve()
    return load_env_files(discover_env_files(start_dir=start_dir, repo_root=repo_root))
