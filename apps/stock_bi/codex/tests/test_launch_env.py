from pathlib import Path

from apps.stock_bi.codex import launch_env


def test_should_reexec_when_target_python_is_a_symlink(tmp_path):
    current_python = tmp_path / "python3"
    current_python.write_text("")
    target_python = tmp_path / ".venv" / "bin" / "python"
    target_python.parent.mkdir(parents=True)
    target_python.symlink_to(current_python)

    assert launch_env.should_reexec(str(current_python), str(target_python))


def test_should_not_reexec_when_already_using_target_python(tmp_path):
    target_python = tmp_path / ".venv" / "bin" / "python"
    target_python.parent.mkdir(parents=True)
    target_python.write_text("")

    assert not launch_env.should_reexec(str(target_python), str(target_python))


def test_ensure_local_runtime_installs_requirements_when_venv_exists_but_is_incomplete(monkeypatch, tmp_path):
    app_dir = tmp_path / "app"
    venv_dir = app_dir / ".venv" / "bin"
    venv_dir.mkdir(parents=True)
    (venv_dir / "python").write_text("")
    (venv_dir / "pip").write_text("")
    (app_dir / "requirements.txt").write_text("fastapi>=0.104.0\n")

    calls = []

    def fake_run(args, check, env=None, stdout=None, stderr=None):
        calls.append({"args": args, "env": env, "stdout": stdout, "stderr": stderr})

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(launch_env.subprocess, "run", fake_run)
    monkeypatch.setattr(launch_env, "_venv_has_runtime_dependencies", lambda _: False)

    paths = launch_env.ensure_local_runtime(app_dir, current_python="/usr/bin/python3")

    assert paths["venv_python"] == app_dir / ".venv" / "bin" / "python"
    assert [call["args"] for call in calls] == [
        ["/usr/bin/python3", "-m", "venv", str(app_dir / ".venv")],
        [str(paths["venv_pip"]), "install", "-q", "-r", str(app_dir / "requirements.txt")],
    ]
