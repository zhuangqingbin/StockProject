#!/usr/bin/env python3
"""
Stock BI 启动脚本
"""
import os
import platform
import sys
from pathlib import Path

from launch_env import (
    build_exec_args,
    build_runtime_env,
    ensure_local_runtime,
    resolve_runtime_architecture,
    should_reexec,
    should_reexec_for_arch,
)

APP_DIR = Path(__file__).resolve().parent
PATHS = ensure_local_runtime(APP_DIR)
RUNTIME_ARCH = resolve_runtime_architecture(PATHS["venv_dir"])

if should_reexec(sys.executable, str(PATHS["venv_python"])) or should_reexec_for_arch(
    platform.machine(),
    RUNTIME_ARCH,
):
    exec_args = build_exec_args(str(PATHS["venv_python"]), RUNTIME_ARCH)
    os.execve(
        exec_args[0],
        [exec_args[0], *exec_args[1:], __file__, *sys.argv[1:]],
        build_runtime_env(os.environ, str(PATHS["repo_root"])),
    )

sys.path.insert(0, str(PATHS["repo_root"]))

import uvicorn
from runtime_server import build_local_urls, resolve_server_host_port

if __name__ == "__main__":
    host, port = resolve_server_host_port()
    os.environ["API_HOST"] = host
    os.environ["API_PORT"] = str(port)
    frontend_url, docs_url = build_local_urls(port)

    print("=" * 60)
    print("  Stock BI - A股数据可视化平台")
    print("=" * 60)
    print()
    print(f"  Frontend: {frontend_url}/")
    print(f"  API Docs: {docs_url}")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(APP_DIR)],
    )
