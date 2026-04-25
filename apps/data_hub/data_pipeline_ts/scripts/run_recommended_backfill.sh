#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
PYTHON_RESOLVER="${REPO_ROOT}/shared/scripts/resolve_project_python.sh"

if [[ ! -x "${PYTHON_RESOLVER}" ]]; then
  echo "Missing Python resolver: ${PYTHON_RESOLVER}" >&2
  exit 1
fi

PROJECT_PYTHON=""
for candidate in \
  "${REPO_ROOT}/apps/.venv/bin/python"; do
  if [[ -x "${candidate}" ]]; then
    PROJECT_PYTHON="${candidate}"
    break
  fi
done

if [[ -z "${PROJECT_PYTHON}" ]]; then
  PROJECT_PYTHON="$("${PYTHON_RESOLVER}")"
fi

SCRIPT_LOG_DIR="${RECOMMENDED_BACKFILL_LOG_DIR:-${SCRIPT_DIR}/logs}"
DATE_COUNT_HELPER="${RECOMMENDED_BACKFILL_DATE_COUNT_HELPER:-${SCRIPT_DIR}/backfill_date_counts.py}"
SYNC_INFRASTRUCTURE_SCRIPT="${RECOMMENDED_BACKFILL_SYNC_INFRASTRUCTURE_SCRIPT:-${SCRIPT_DIR}/sync_infrastructure.sh}"
RUN_BACKFILL_SCRIPT="${RECOMMENDED_BACKFILL_RUN_BACKFILL_SCRIPT:-${SCRIPT_DIR}/run_backfill.sh}"
RUN_JOB_SCRIPT="${RECOMMENDED_BACKFILL_RUN_JOB_SCRIPT:-${SCRIPT_DIR}/run_job.sh}"

START_DATE=""
END_DATE=""
SNAPSHOT_DATE=""
MAX_WORKERS=""
INCLUDE_STEP4=0
ONLY_STEP4=0
DRY_RUN=0
LOG_FILE=""

PARALLEL_PIDS=()
PARALLEL_LABELS=()
PARALLEL_OUTPUT_FILES=()
PARALLEL_COMMANDS=()
PARALLEL_DURATION_FILES=()

usage() {
  cat <<'EOF'
Usage:
  bash apps/data_hub/data_pipeline_ts/scripts/run_recommended_backfill.sh \
    --start YYYYMMDD \
    --end YYYYMMDD \
    [--include-step4 | --only-step4] \
    [--snapshot-date YYYYMMDD] \
    [--max-workers N] \
    [--dry-run]

Behavior:
  Default: run README-recommended backfill steps 1-3
  --include-step4: append step 4 after steps 1-3
  --only-step4: run only step 4
  --snapshot-date: override hm_list / pledge_detail snapshot_date, defaults to --end
  --max-workers: pass through to run_backfill.sh
  --dry-run: print commands without executing them
EOF
}

validate_compact_date() {
  local value="$1"
  local label="$2"
  if [[ ! "${value}" =~ ^[0-9]{8}$ ]]; then
    echo "${label} must use YYYYMMDD, got: ${value}" >&2
    exit 1
  fi
}

print_command() {
  printf '[dry-run]'
  while (($#)); do
    printf ' %s' "$1"
    shift
  done
  printf '\n'
}

run_command() {
  if ((DRY_RUN)); then
    print_command "$@"
    return 0
  fi
  "$@"
}

current_timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

current_perf_counter() {
  PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - <<'PY'
import time

print(f"{time.perf_counter():.6f}")
PY
}

format_duration() {
  local started_at="$1"
  local ended_at="$2"
  PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - "${started_at}" "${ended_at}" <<'PY'
import sys

started_at = float(sys.argv[1])
ended_at = float(sys.argv[2])
print(f"{max(ended_at - started_at, 0.0):.2f}s")
PY
}

print_status_line() {
  local label="$1"
  shift
  printf '[%s] [%s]' "$(current_timestamp)" "${label}"
  if (($#)); then
    printf ' %s' "$1"
    shift
    while (($#)); do
      printf ' %s' "$1"
      shift
    done
  fi
  printf '\n'
}

format_command() {
  local rendered=""
  local quoted_arg=""
  local arg
  for arg in "$@"; do
    printf -v quoted_arg '%q' "${arg}"
    if [[ -n "${rendered}" ]]; then
      rendered+=" "
    fi
    rendered+="${quoted_arg}"
  done
  printf '%s\n' "${rendered}"
}

format_display_command() {
  local args=("$@")
  local rendered=""
  local arg=""

  if ((${#args[@]} >= 2)) && [[ "${args[0]}" == "bash" ]] && [[ "${args[1]}" == */* ]]; then
    args=("$(basename "${args[1]}")" "${args[@]:2}")
  elif ((${#args[@]} >= 1)) && [[ "${args[0]}" == */* ]]; then
    args=("$(basename "${args[0]}")" "${args[@]:1}")
  fi

  for arg in "${args[@]}"; do
    if [[ -n "${rendered}" ]]; then
      rendered+=" "
    fi
    if [[ "${arg}" =~ [[:space:]] ]]; then
      local quoted_arg=""
      printf -v quoted_arg '%q' "${arg}"
      rendered+="${quoted_arg}"
    else
      rendered+="${arg}"
    fi
  done

  printf '%s\n' "${rendered}"
}

append_command_failure_with_text() {
  local step="$1"
  local exit_code="$2"
  local command_text="$3"
  local output_file="$4"
  local output=""
  if [[ -f "${output_file}" ]]; then
    output="$(cat "${output_file}")"
  fi
  append_log_block \
    "[error]" \
    "step=${step}" \
    "exit_code=${exit_code}" \
    "command=${command_text}" \
    "${output}"
}

is_structured_job_output_line() {
  local line="$1"
  [[ "${line}" == \{* ]] || return 1
  [[ "${line}" == *'"job_name"'* ]] || return 1
  [[ "${line}" == *'"table_name"'* ]] || return 1
  [[ "${line}" == *'"status"'* ]] || return 1
  [[ "${line}" == *'"rows_written"'* ]] || return 1
  return 0
}

stream_command_output() {
  local label="$1"
  local output_file="$2"
  local line=""
  while IFS= read -r line || [[ -n "${line}" ]]; do
    printf '%s\n' "${line}" >> "${output_file}"
    if is_structured_job_output_line "${line}"; then
      continue
    fi
    print_status_line "${label}" "${line}"
  done
}

emit_structured_job_summary_from_file() {
  local label="$1"
  local duration="$2"
  local output_file="$3"
  local rendered=""
  rendered="$(
    PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - "${output_file}" "${duration}" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

output_path = Path(sys.argv[1])
duration = sys.argv[2]
payload = None

for raw_line in output_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line.startswith("{"):
        continue
    try:
        candidate = json.loads(line)
    except json.JSONDecodeError:
        continue
    required = {"job_name", "table_name", "status", "rows_fetched", "rows_written"}
    if required.issubset(candidate):
        payload = candidate

if payload is None:
    raise SystemExit(1)

parts = [
    str(payload["status"]),
    f"duration={duration}",
]
table_name = payload.get("table_name")
if table_name:
    parts.append(f"table={table_name}")
parts.append(f"rows_fetched={payload.get('rows_fetched', 0)}")
parts.append(f"rows_written={payload.get('rows_written', 0)}")
print(" ".join(parts))

error = payload.get("error")
if error:
    print(f"error: {error}")
PY
  )" || return 1

  local rendered_line=""
  while IFS= read -r rendered_line || [[ -n "${rendered_line}" ]]; do
    print_status_line "${label}" "${rendered_line}"
  done <<< "${rendered}"
}

emit_date_count_summary() {
  local rendered="$1"
  local formatted=""
  formatted="$(
    PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - "${rendered}" <<'PY'
from __future__ import annotations

import sys

raw_block = sys.argv[1]
job_name = None
window = ""
status = ""
total_rows = "0"
rows: list[tuple[str, str]] = []

for raw_line in raw_block.splitlines():
    line = raw_line.strip()
    if not line or line == "[date-counts]":
        continue
    if line.startswith("job="):
        for token in line.split():
            if token.startswith("job="):
                job_name = token.split("=", 1)[1]
                break
        continue
    if line.startswith("window="):
        window = line.split("=", 1)[1]
        continue
    if line.startswith("status="):
        status = line.split("=", 1)[1]
        continue
    if line.startswith("total_rows="):
        total_rows = line.split("=", 1)[1]
        continue
    parts = line.split()
    if len(parts) == 2:
        rows.append((parts[0], parts[1]))

if job_name is None:
    raise SystemExit(1)

summary_parts = [f"job={job_name}"]
if window:
    summary_parts.append(f"window={window}")
if status:
    summary_parts.append(f"status={status}")
summary_parts.append(f"total_rows={total_rows}")
print(" ".join(summary_parts))
for bucket, row_count in rows:
    print(f"{bucket} -> {row_count}")
PY
  )" || return 1

  local formatted_line=""
  while IFS= read -r formatted_line || [[ -n "${formatted_line}" ]]; do
    print_status_line "date-counts" "${formatted_line}"
  done <<< "${formatted}"
}

run_command_with_error_logging() {
  local step="$1"
  shift
  if ((DRY_RUN)); then
    print_command "$@"
    return 0
  fi

  local output_file
  local started_at
  local ended_at
  local duration
  local exit_code=0
  output_file="$(mktemp)"
  print_status_line "${step}" "start: $(format_display_command "$@")"
  started_at="$(current_perf_counter)"
  set +e
  "$@" 2>&1 | stream_command_output "${step}" "${output_file}"
  exit_code=${PIPESTATUS[0]}
  set -e
  ended_at="$(current_perf_counter)"
  duration="$(format_duration "${started_at}" "${ended_at}")"
  if ((exit_code == 0)); then
    if ! emit_structured_job_summary_from_file "${step}" "${duration}" "${output_file}"; then
      print_status_line "${step}" "success duration=${duration}"
    fi
    rm -f "${output_file}"
    return 0
  fi

  if ! emit_structured_job_summary_from_file "${step}" "${duration}" "${output_file}"; then
    print_status_line "${step}" "failed exit_code=${exit_code} duration=${duration}"
  fi
  append_command_failure_with_text "${step}" "${exit_code}" "$(format_command "$@")" "${output_file}"
  rm -f "${output_file}"
  return "${exit_code}"
}

run_command_in_background() {
  local label="$1"
  shift
  if ((DRY_RUN)); then
    print_command "$@"
    return 0
  fi
  local output_file
  local duration_file
  output_file="$(mktemp)"
  duration_file="$(mktemp)"
  print_status_line "${label}" "start: $(format_display_command "$@")"
  (
    local started_at
    local ended_at
    local duration
    local exit_code=0
    started_at="$(current_perf_counter)"
    set +e
    "$@" 2>&1 | stream_command_output "${label}" "${output_file}"
    exit_code=${PIPESTATUS[0]}
    set -e
    ended_at="$(current_perf_counter)"
    duration="$(format_duration "${started_at}" "${ended_at}")"
    printf '%s\n' "${duration}" > "${duration_file}"
    exit "${exit_code}"
  ) &
  PARALLEL_PIDS+=("$!")
  PARALLEL_LABELS+=("${label}")
  PARALLEL_OUTPUT_FILES+=("${output_file}")
  PARALLEL_COMMANDS+=("$(format_command "$@")")
  PARALLEL_DURATION_FILES+=("${duration_file}")
}

append_log_block() {
  if ((DRY_RUN)); then
    return 0
  fi
  if [[ -z "${LOG_FILE}" ]]; then
    echo "LOG_FILE is not initialized" >&2
    exit 1
  fi
  {
    printf '%s\n' "$@"
    printf '\n'
  } >> "${LOG_FILE}"
}

init_log_file() {
  if ((DRY_RUN)); then
    return 0
  fi
  local log_timestamp="${RECOMMENDED_BACKFILL_LOG_TIMESTAMP:-}"
  if [[ -z "${log_timestamp}" ]]; then
    log_timestamp="$(date '+%Y%m%d%H%M')"
  fi
  mkdir -p "${SCRIPT_LOG_DIR}"
  LOG_FILE="${SCRIPT_LOG_DIR}/${log_timestamp}.log"
  : > "${LOG_FILE}"
  print_status_line "log" "${LOG_FILE}"
}

append_job_date_counts() {
  local job_name="$1"
  shift
  if ((DRY_RUN)); then
    return 0
  fi
  if [[ ! -f "${DATE_COUNT_HELPER}" ]]; then
    echo "Missing date count helper: ${DATE_COUNT_HELPER}" >&2
    exit 1
  fi
  local rendered
  rendered="$(PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" "${DATE_COUNT_HELPER}" --job "${job_name}" "$@")"
  append_log_block "${rendered}"
  emit_date_count_summary "${rendered}"
}

wait_for_parallel_group() {
  local failures=0
  local index=0
  local count="${#PARALLEL_PIDS[@]}"
  if ((count == 0)); then
    PARALLEL_PIDS=()
    PARALLEL_LABELS=()
    PARALLEL_OUTPUT_FILES=()
    PARALLEL_COMMANDS=()
    PARALLEL_DURATION_FILES=()
    return 0
  fi
  for pid in "${PARALLEL_PIDS[@]}"; do
    local exit_code=0
    local duration=""
    if wait "${pid}"; then
      exit_code=0
    else
      exit_code=$?
    fi
    if [[ -f "${PARALLEL_DURATION_FILES[$index]}" ]]; then
      duration="$(cat "${PARALLEL_DURATION_FILES[$index]}")"
    fi
    if ((exit_code != 0)); then
      if ! emit_structured_job_summary_from_file "${PARALLEL_LABELS[$index]}" "${duration}" "${PARALLEL_OUTPUT_FILES[$index]}"; then
        print_status_line "${PARALLEL_LABELS[$index]}" "failed exit_code=${exit_code} duration=${duration}"
      fi
      append_command_failure_with_text \
        "${PARALLEL_LABELS[$index]}" \
        "${exit_code}" \
        "${PARALLEL_COMMANDS[$index]}" \
        "${PARALLEL_OUTPUT_FILES[$index]}"
      failures=1
    else
      if ! emit_structured_job_summary_from_file "${PARALLEL_LABELS[$index]}" "${duration}" "${PARALLEL_OUTPUT_FILES[$index]}"; then
        print_status_line "${PARALLEL_LABELS[$index]}" "success duration=${duration}"
      fi
    fi
    rm -f "${PARALLEL_OUTPUT_FILES[$index]}"
    rm -f "${PARALLEL_DURATION_FILES[$index]}"
    index=$((index + 1))
  done
  PARALLEL_PIDS=()
  PARALLEL_LABELS=()
  PARALLEL_OUTPUT_FILES=()
  PARALLEL_COMMANDS=()
  PARALLEL_DURATION_FILES=()
  if ((failures)); then
    exit 1
  fi
}

build_backfill_jobs() {
  PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - <<'PY'
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS

excluded = {
    "hm_list",
    "pledge_detail",
    "cyq_chips",
    "fina_audit",
    "stock_daily",
    "stock_daily_basic",
    "kpl_list",
    "report_rc",
}

print(",".join(job.name for job in ALL_JOBS if job.name not in excluded))
PY
}

run_step1() {
  print_status_line "step1" "Sync infrastructure"
  run_command_in_background \
    "step1.stock_basic_company" \
    bash "${SYNC_INFRASTRUCTURE_SCRIPT}" --targets stock_basic,stock_company
  run_command_in_background \
    "step1.trade_cal" \
    bash "${SYNC_INFRASTRUCTURE_SCRIPT}" --targets trade_cal --start "${START_DATE}" --end "${END_DATE}"
  wait_for_parallel_group
}

run_step2() {
  local backfill_jobs
  backfill_jobs="$(build_backfill_jobs)"
  if [[ -z "${backfill_jobs}" ]]; then
    echo "Failed to resolve recommended backfill job list" >&2
    exit 1
  fi

  print_status_line "step2" "Bulk backfill excluding manual jobs and explicit range jobs"
  local cmd=(
    bash "${RUN_BACKFILL_SCRIPT}"
    --jobs "${backfill_jobs}"
    --start "${START_DATE}"
    --end "${END_DATE}"
  )
  if [[ -n "${MAX_WORKERS}" ]]; then
    cmd+=(--max-workers "${MAX_WORKERS}")
  fi
  run_command_with_error_logging "step2.backfill" "${cmd[@]}"
}

run_step3() {
  print_status_line "step3" "Run explicit range jobs"
  run_command_in_background \
    "step3.kpl_list" \
    bash "${RUN_JOB_SCRIPT}" --job kpl_list --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  run_command_in_background \
    "step3.report_rc" \
    bash "${RUN_JOB_SCRIPT}" --job report_rc --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  wait_for_parallel_group
  append_job_date_counts "kpl_list" --start-date "${START_DATE}" --end-date "${END_DATE}"
  append_job_date_counts "report_rc" --start-date "${START_DATE}" --end-date "${END_DATE}"
}

run_step4() {
  print_status_line "step4" "Run optional manual backfill jobs"
  run_command_in_background \
    "step4.hm_list" \
    bash "${RUN_JOB_SCRIPT}" --job hm_list --param "snapshot_date=${SNAPSHOT_DATE}"
  run_command_in_background \
    "step4.pledge_detail" \
    bash "${RUN_JOB_SCRIPT}" --job pledge_detail --param "snapshot_date=${SNAPSHOT_DATE}"
  run_command_in_background \
    "step4.cyq_chips" \
    bash "${RUN_JOB_SCRIPT}" --job cyq_chips --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  run_command_in_background \
    "step4.fina_audit" \
    bash "${RUN_JOB_SCRIPT}" --job fina_audit --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  wait_for_parallel_group
}

while (($#)); do
  case "$1" in
    --start)
      START_DATE="${2:-}"
      shift 2
      ;;
    --end)
      END_DATE="${2:-}"
      shift 2
      ;;
    --snapshot-date)
      SNAPSHOT_DATE="${2:-}"
      shift 2
      ;;
    --max-workers)
      MAX_WORKERS="${2:-}"
      shift 2
      ;;
    --include-step4)
      INCLUDE_STEP4=1
      shift
      ;;
    --only-step4)
      ONLY_STEP4=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${START_DATE}" || -z "${END_DATE}" ]]; then
  echo "--start and --end are required" >&2
  usage >&2
  exit 1
fi

validate_compact_date "${START_DATE}" "start_date"
validate_compact_date "${END_DATE}" "end_date"

if ((INCLUDE_STEP4 && ONLY_STEP4)); then
  echo "--include-step4 and --only-step4 cannot be used together" >&2
  exit 1
fi

if [[ -z "${SNAPSHOT_DATE}" ]]; then
  SNAPSHOT_DATE="${END_DATE}"
fi
validate_compact_date "${SNAPSHOT_DATE}" "snapshot_date"

cd "${REPO_ROOT}"
init_log_file

if ((ONLY_STEP4)); then
  run_step4
  exit 0
fi

run_step1
run_step2
run_step3

if ((INCLUDE_STEP4)); then
  run_step4
fi
