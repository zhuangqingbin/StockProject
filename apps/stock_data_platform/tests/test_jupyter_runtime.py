from __future__ import annotations

from pathlib import Path
import json

from apps.stock_data_platform.notebooks import jupyter_runtime


def test_build_kernel_install_command_targets_project_venv(tmp_path):
    repo_root = tmp_path / "repo"

    command = jupyter_runtime.build_kernel_install_command(repo_root, arch="arm64")

    assert command == [
        str(repo_root / ".venv-stock-data-arm64" / "bin" / "python"),
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        jupyter_runtime.PROJECT_KERNEL_NAME,
        "--display-name",
        jupyter_runtime.PROJECT_KERNEL_DISPLAY_NAME,
    ]


def test_build_jupyterlab_command_targets_project_venv(tmp_path):
    repo_root = tmp_path / "repo"

    command = jupyter_runtime.build_jupyterlab_command(repo_root)

    assert command == [
        str(repo_root / "apps" / "stock_data_platform" / "scripts" / "dispatch_stock_data_python.sh"),
        "-m",
        "jupyterlab",
    ]


def test_build_default_kernel_install_command_targets_python3_alias(tmp_path):
    repo_root = tmp_path / "repo"

    command = jupyter_runtime.build_default_kernel_install_command(repo_root, arch="x86_64")

    assert command == [
        str(repo_root / ".venv-stock-data-x86_64" / "bin" / "python"),
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        "python3",
        "--display-name",
        "Python 3",
    ]


def test_default_repo_root_points_to_workspace_root():
    repo_root = jupyter_runtime.default_repo_root()

    assert (repo_root / "apps" / "stock_data_platform").exists()
    assert (repo_root / "apps" / "stock_data_platform" / "scripts" / "dispatch_stock_data_python.sh").exists()


def test_ensure_kernel_spec_env_writes_pythonnouser_site(tmp_path):
    kernel_spec_path = tmp_path / "kernel.json"
    kernel_spec_path.write_text(
        json.dumps(
            {
                "argv": ["/tmp/python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Python (stock_data_platform)",
                "language": "python",
            }
        ),
        encoding="utf-8",
    )

    jupyter_runtime.ensure_kernel_spec_env(kernel_spec_path)

    payload = json.loads(kernel_spec_path.read_text(encoding="utf-8"))
    assert payload["env"]["PYTHONNOUSERSITE"] == "1"


def test_ensure_kernel_spec_defaults_rewrites_argv_and_display_name(tmp_path):
    kernel_spec_path = tmp_path / "kernel.json"
    kernel_spec_path.write_text(
        json.dumps(
            {
                "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
            }
        ),
        encoding="utf-8",
    )

    jupyter_runtime.ensure_kernel_spec_defaults(
        kernel_spec_path=kernel_spec_path,
        launcher_script=Path("/tmp/dispatch_stock_data_python.sh"),
        display_name="Python 3",
    )

    payload = json.loads(kernel_spec_path.read_text(encoding="utf-8"))
    assert payload["argv"][0] == "/tmp/dispatch_stock_data_python.sh"
    assert payload["argv"][1:] == ["-m", "ipykernel_launcher", "-f", "{connection_file}"]
    assert payload["display_name"] == "Python 3"
    assert payload["env"]["PYTHONNOUSERSITE"] == "1"


def test_ensure_project_kernel_rewrites_legacy_python3_kernel(tmp_path, monkeypatch):
    project_kernel_spec_path = tmp_path / "project-kernel.json"
    default_kernel_spec_path = tmp_path / "default-kernel.json"
    legacy_kernel_spec_path = tmp_path / "legacy-python3-kernel.json"

    for kernel_spec_path in (project_kernel_spec_path, default_kernel_spec_path, legacy_kernel_spec_path):
        kernel_spec_path.write_text(
            json.dumps(
                {
                    "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "Python 3 (ipykernel)",
                    "language": "python",
                }
            ),
            encoding="utf-8",
        )

    recorded_commands: list[list[str]] = []

    monkeypatch.setattr(jupyter_runtime, "_run", lambda command, env=None: recorded_commands.append(list(command)))
    monkeypatch.setattr(jupyter_runtime, "project_kernel_spec_path", lambda: project_kernel_spec_path)
    monkeypatch.setattr(jupyter_runtime, "default_kernel_spec_path", lambda: default_kernel_spec_path)
    monkeypatch.setattr(jupyter_runtime, "legacy_default_kernel_spec_path", lambda: legacy_kernel_spec_path)
    monkeypatch.setattr(jupyter_runtime, "current_arch", lambda: "arm64")

    repo_root = tmp_path / "repo"
    managed_python = repo_root / ".venv-stock-data-arm64" / "bin" / "python"
    managed_python.parent.mkdir(parents=True)
    managed_python.write_text("", encoding="utf-8")
    jupyter_runtime.ensure_project_kernel(repo_root=repo_root)

    expected_python = str(repo_root / ".venv-stock-data-arm64" / "bin" / "python")
    expected_launcher = str(repo_root / "apps" / "stock_data_platform" / "scripts" / "dispatch_stock_data_python.sh")
    assert recorded_commands == [
        jupyter_runtime.build_kernel_install_command(repo_root, arch="arm64"),
        jupyter_runtime.build_default_kernel_install_command(repo_root, arch="arm64"),
    ]

    for kernel_spec_path, display_name in (
        (project_kernel_spec_path, jupyter_runtime.PROJECT_KERNEL_DISPLAY_NAME),
        (default_kernel_spec_path, jupyter_runtime.DEFAULT_KERNEL_DISPLAY_NAME),
        (legacy_kernel_spec_path, jupyter_runtime.DEFAULT_KERNEL_DISPLAY_NAME),
    ):
        payload = json.loads(kernel_spec_path.read_text(encoding="utf-8"))
        assert payload["argv"][0] == expected_launcher
        assert payload["argv"][1:] == ["-m", "ipykernel_launcher", "-f", "{connection_file}"]
        assert payload["display_name"] == display_name
        assert payload["env"]["PYTHONNOUSERSITE"] == "1"

    assert expected_python.endswith(".venv-stock-data-arm64/bin/python")
