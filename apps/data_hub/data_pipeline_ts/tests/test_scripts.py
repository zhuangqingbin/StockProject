from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess


def _write_executable(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def _run_install_launchd(tmp_path: Path, *args: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    script_path = scripts_dir / "install_launchd.sh"
    fake_home = tmp_path / "home"
    fake_bin = tmp_path / "bin"
    fake_home.mkdir()
    fake_bin.mkdir()

    fake_launchctl = fake_bin / "launchctl"
    fake_launchctl.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_launchctl.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    subprocess.run(
        ["bash", str(script_path), *args],
        check=True,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    return fake_home / "Library" / "LaunchAgents"


def _run_recommended_backfill(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[3]
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    script_path = scripts_dir / "run_recommended_backfill.sh"

    return subprocess.run(
        ["bash", str(script_path), *args],
        check=False,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )


def _build_recommended_backfill_test_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    fake_dir = tmp_path / "fake_scripts"
    fake_dir.mkdir()
    log_dir = tmp_path / "logs"

    sync_script = _write_executable(
        fake_dir / "sync_infrastructure.sh",
        """#!/usr/bin/env bash
set -euo pipefail
args="$*"
if [[ "${FAIL_SYNC_TARGET:-}" == "trade_cal" && "${args}" == *"trade_cal"* ]]; then
  echo "sync failed for trade_cal" >&2
  exit 11
fi
echo "sync ok: ${args}"
""",
    )
    backfill_script = _write_executable(
        fake_dir / "run_backfill.sh",
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${FAIL_STEP2:-0}" == "1" ]]; then
  echo "bulk backfill failed" >&2
  exit 22
fi
echo "bulk backfill ok: $*"
""",
    )
    run_job_script = _write_executable(
        fake_dir / "run_job.sh",
        """#!/usr/bin/env bash
set -euo pipefail
job=""
while (($#)); do
  case "$1" in
    --job)
      job="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [[ -n "${FAIL_JOB:-}" && "${FAIL_JOB}" == "${job}" ]]; then
  echo "job failed: ${job}" >&2
  exit 33
fi
table_name=""
rows_fetched=0
rows_written=0
case "${job}" in
  kpl_list)
    table_name="stock_kpl_list"
    rows_fetched=11
    rows_written=11
    ;;
  report_rc)
    table_name="stock_report_rc"
    rows_fetched=7
    rows_written=7
    ;;
  hm_list)
    table_name="stock_hm_list"
    rows_fetched=2
    rows_written=2
    ;;
  pledge_detail)
    table_name="stock_pledge_detail"
    rows_fetched=3
    rows_written=3
    ;;
  cyq_chips)
    table_name="stock_cyq_chips"
    rows_fetched=4
    rows_written=4
    ;;
  fina_audit)
    table_name="stock_fina_audit"
    rows_fetched=5
    rows_written=5
    ;;
esac
printf '{"job_name":"%s","table_name":"%s","status":"success","rows_fetched":%s,"rows_written":%s,"run_id":"test-%s","params":{},"error":null}\n' \
  "${job}" "${table_name}" "${rows_fetched}" "${rows_written}" "${job}"
""",
    )
    date_count_helper = _write_executable(
        fake_dir / "backfill_date_counts.py",
        """#!/usr/bin/env python3
import sys

job = ""
for index, arg in enumerate(sys.argv):
    if arg == "--job" and index + 1 < len(sys.argv):
        job = sys.argv[index + 1]
        break

payloads = {
    "kpl_list": "[date-counts]\\njob=kpl_list table=stock_kpl_list date_column=trade_date\\nwindow=20260101~20260131\\n20260101 11\\ntotal_rows=11",
    "report_rc": "[date-counts]\\njob=report_rc table=stock_report_rc date_column=report_date\\nwindow=20260101~20260131\\n20260101 7\\ntotal_rows=7",
    "hm_list": "[date-counts]\\njob=hm_list table=stock_hm_list date_column=snapshot_date\\nwindow=20260131\\n20260131 2\\ntotal_rows=2",
    "pledge_detail": "[date-counts]\\njob=pledge_detail table=stock_pledge_detail date_column=snapshot_date\\nwindow=20260131\\n20260131 3\\ntotal_rows=3",
    "cyq_chips": "[date-counts]\\njob=cyq_chips table=stock_cyq_chips date_column=trade_date\\nwindow=20260101~20260131\\n20260101 4\\ntotal_rows=4",
    "fina_audit": "[date-counts]\\njob=fina_audit table=stock_fina_audit date_column=ann_date\\nwindow=20260101~20260131\\n20260101 5\\ntotal_rows=5",
}

print(payloads[job])
""",
    )

    env = os.environ.copy()
    env["RECOMMENDED_BACKFILL_LOG_DIR"] = str(log_dir)
    env["RECOMMENDED_BACKFILL_LOG_TIMESTAMP"] = "202604181001"
    env["RECOMMENDED_BACKFILL_SYNC_INFRASTRUCTURE_SCRIPT"] = str(sync_script)
    env["RECOMMENDED_BACKFILL_RUN_BACKFILL_SCRIPT"] = str(backfill_script)
    env["RECOMMENDED_BACKFILL_RUN_JOB_SCRIPT"] = str(run_job_script)
    env["RECOMMENDED_BACKFILL_DATE_COUNT_HELPER"] = str(date_count_helper)
    return env, log_dir


def test_data_pipeline_ts_scripts_are_self_contained():
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"

    run_daily = (scripts_dir / "run_daily.sh").read_text(encoding="utf-8")
    run_backfill = (scripts_dir / "run_backfill.sh").read_text(encoding="utf-8")
    run_job = (scripts_dir / "run_job.sh").read_text(encoding="utf-8")
    run_recommended_backfill = (scripts_dir / "run_recommended_backfill.sh").read_text(encoding="utf-8")
    sync_infrastructure = (scripts_dir / "sync_infrastructure.sh").read_text(encoding="utf-8")
    install_launchd = (scripts_dir / "install_launchd.sh").read_text(encoding="utf-8")

    assert "apps.data_hub.data_pipeline_ts.main" in run_daily
    assert "--mode once" not in run_daily
    assert 'QV_RESEARCH_AUTO_PUBLISH_ENABLED="${QV_RESEARCH_AUTO_PUBLISH_ENABLED:-1}"' in run_daily
    assert 'QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION="${QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION:-1}"' in run_daily
    assert "--mode backfill" in run_backfill
    assert "apps.data_hub.data_pipeline_ts.run_job" in run_job
    assert "sync_infrastructure.sh" in run_recommended_backfill
    assert "run_backfill.sh" in run_recommended_backfill
    assert "run_job.sh" in run_recommended_backfill
    assert 'SCRIPT_LOG_DIR="${RECOMMENDED_BACKFILL_LOG_DIR:-${SCRIPT_DIR}/logs}"' in run_recommended_backfill
    assert 'RECOMMENDED_BACKFILL_LOG_TIMESTAMP' in run_recommended_backfill
    assert 'LOG_FILE="${SCRIPT_LOG_DIR}/${log_timestamp}.log"' in run_recommended_backfill
    assert 'RECOMMENDED_BACKFILL_SYNC_INFRASTRUCTURE_SCRIPT' in run_recommended_backfill
    assert 'RECOMMENDED_BACKFILL_RUN_BACKFILL_SCRIPT' in run_recommended_backfill
    assert 'RECOMMENDED_BACKFILL_RUN_JOB_SCRIPT' in run_recommended_backfill
    assert "backfill_date_counts.py" in run_recommended_backfill
    assert "--mode infrastructure" in sync_infrastructure
    assert "data_pipeline_ts/scripts/run_daily.sh" in install_launchd
    assert "PROFILE_SPECS" in install_launchd
    assert 'install_plan "com.stockproject.stock-data-v1-orchestrator-v2.pre-open"' not in install_launchd
    assert "apps/data_hub/scripts" not in install_launchd
    assert "ORCHESTRATOR_V2_PRECOMPUTE_ENABLED" not in install_launchd
    assert 'REPO_ROOT}/apps/.venv/bin/python' in run_daily
    assert 'REPO_ROOT}/apps/.venv/bin/python' in install_launchd
    assert "apps/data_hub/.venv" not in run_daily
    assert "apps/data_hub/.venv" not in install_launchd


def test_install_launchd_does_not_emit_max_workers_by_default(tmp_path):
    agents_dir = _run_install_launchd(tmp_path)
    plist = (agents_dir / "com.stockproject.stock-data-v1-orchestrator-v2.trade-day-post-close-core.plist").read_text(encoding="utf-8")

    assert "--profiles" in plist
    assert "--max-workers" not in plist


def test_install_launchd_emits_max_workers_when_requested(tmp_path):
    agents_dir = _run_install_launchd(tmp_path, "--max-workers", "1")
    plist = (agents_dir / "com.stockproject.stock-data-v1-orchestrator-v2.trade-day-post-close-core.plist").read_text(encoding="utf-8")

    assert "<string>--max-workers</string>" in plist
    assert "<string>1</string>" in plist


def test_run_recommended_backfill_dry_run_defaults_to_steps_one_to_three():
    result = _run_recommended_backfill("--start", "20260101", "--end", "20260131", "--dry-run")

    assert result.returncode == 0
    assert "sync_infrastructure.sh --targets stock_basic,stock_company" in result.stdout
    assert "sync_infrastructure.sh --targets trade_cal --start 20260101 --end 20260131" in result.stdout
    assert "run_backfill.sh --jobs " in result.stdout
    assert "--start 20260101 --end 20260131" in result.stdout
    assert "run_job.sh --job kpl_list --param start_date=20260101 --param end_date=20260131" in result.stdout
    assert "run_job.sh --job report_rc --param start_date=20260101 --param end_date=20260131" in result.stdout
    assert "run_job.sh --job hm_list" not in result.stdout
    assert "run_job.sh --job pledge_detail" not in result.stdout


def test_run_recommended_backfill_dry_run_include_step4_uses_end_date_as_default_snapshot_date():
    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        "--include-step4",
        "--dry-run",
    )

    assert result.returncode == 0
    assert "run_job.sh --job hm_list --param snapshot_date=20260131" in result.stdout
    assert "run_job.sh --job pledge_detail --param snapshot_date=20260131" in result.stdout
    assert "run_job.sh --job cyq_chips --param start_date=20260101 --param end_date=20260131" in result.stdout
    assert "run_job.sh --job fina_audit --param start_date=20260101 --param end_date=20260131" in result.stdout


def test_run_recommended_backfill_dry_run_only_step4_skips_steps_one_to_three_and_honors_snapshot_override():
    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        "--only-step4",
        "--snapshot-date",
        "20260115",
        "--dry-run",
    )

    assert result.returncode == 0
    assert "sync_infrastructure.sh --targets stock_basic,stock_company" not in result.stdout
    assert "sync_infrastructure.sh --targets trade_cal" not in result.stdout
    assert "run_backfill.sh --jobs " not in result.stdout
    assert "run_job.sh --job kpl_list" not in result.stdout
    assert "run_job.sh --job report_rc" not in result.stdout
    assert "run_job.sh --job hm_list --param snapshot_date=20260115" in result.stdout
    assert "run_job.sh --job pledge_detail --param snapshot_date=20260115" in result.stdout


def test_run_recommended_backfill_writes_minute_log_with_step3_date_counts_only(tmp_path):
    env, log_dir = _build_recommended_backfill_test_env(tmp_path)

    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        "--include-step4",
        env=env,
    )

    assert result.returncode == 0
    log_path = log_dir / "202604181001.log"
    assert log_path.exists()
    assert '"job_name"' not in result.stdout
    assert "fake_scripts" not in result.stdout
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step1\] Sync infrastructure",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step1\.stock_basic_company\] start: sync_infrastructure\.sh --targets stock_basic,stock_company",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step2\.backfill\] start: run_backfill\.sh --jobs ",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step3\.kpl_list\] start: run_job\.sh --job kpl_list --param start_date=20260101 --param end_date=20260131",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step2\.backfill\] success duration=\d+\.\d{2}s",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step3\.kpl_list\] success duration=\d+\.\d{2}s table=stock_kpl_list rows_fetched=11 rows_written=11",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step3\.report_rc\] success duration=\d+\.\d{2}s table=stock_report_rc rows_fetched=7 rows_written=7",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[date-counts\] job=kpl_list window=20260101~20260131 total_rows=11",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[date-counts\] 20260101 -> 11",
        result.stdout,
    )

    log_text = log_path.read_text(encoding="utf-8")
    assert "job=kpl_list table=stock_kpl_list date_column=trade_date" in log_text
    assert "job=report_rc table=stock_report_rc date_column=report_date" in log_text
    assert "20260101 11" in log_text
    assert "20260101 7" in log_text
    assert "job=hm_list" not in log_text
    assert "job=pledge_detail" not in log_text
    assert "job=cyq_chips" not in log_text
    assert "job=fina_audit" not in log_text
    assert "sync ok:" not in log_text
    assert "bulk backfill ok:" not in log_text
    assert '"job": "hm_list"' not in log_text


def test_run_recommended_backfill_logs_step1_failure_only_as_error(tmp_path):
    env, log_dir = _build_recommended_backfill_test_env(tmp_path)
    env["FAIL_SYNC_TARGET"] = "trade_cal"

    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        env=env,
    )

    assert result.returncode != 0
    log_text = (log_dir / "202604181001.log").read_text(encoding="utf-8")
    assert "[error]" in log_text
    assert "step=step1.trade_cal" in log_text
    assert "exit_code=11" in log_text
    assert "sync failed for trade_cal" in log_text
    assert "sync ok:" not in log_text
    assert "job=kpl_list" not in log_text


def test_run_recommended_backfill_logs_step2_failure_only_as_error(tmp_path):
    env, log_dir = _build_recommended_backfill_test_env(tmp_path)
    env["FAIL_STEP2"] = "1"

    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        env=env,
    )

    assert result.returncode != 0
    log_text = (log_dir / "202604181001.log").read_text(encoding="utf-8")
    assert "[error]" in log_text
    assert "step=step2.backfill" in log_text
    assert "exit_code=22" in log_text
    assert "bulk backfill failed" in log_text
    assert "bulk backfill ok:" not in log_text
    assert "job=kpl_list" not in log_text


def test_run_recommended_backfill_logs_step4_failure_only_as_error(tmp_path):
    env, log_dir = _build_recommended_backfill_test_env(tmp_path)
    env["FAIL_JOB"] = "hm_list"

    result = _run_recommended_backfill(
        "--start",
        "20260101",
        "--end",
        "20260131",
        "--only-step4",
        env=env,
    )

    assert result.returncode != 0
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step4\.hm_list\] failed exit_code=33 duration=\d+\.\d{2}s",
        result.stdout,
    )
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[step4\.hm_list\] job failed: hm_list",
        result.stdout,
    )
    log_text = (log_dir / "202604181001.log").read_text(encoding="utf-8")
    assert "[error]" in log_text
    assert "step=step4.hm_list" in log_text
    assert "exit_code=33" in log_text
    assert "job failed: hm_list" in log_text
    assert "job=hm_list" not in log_text
    assert "job=cyq_chips" not in log_text
