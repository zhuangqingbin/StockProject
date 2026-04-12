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

START_DATE=""
END_DATE=""
SNAPSHOT_DATE=""
MAX_WORKERS=""
INCLUDE_STEP4=0
ONLY_STEP4=0
DRY_RUN=0

PARALLEL_PIDS=()
PARALLEL_LABELS=()

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

run_command_in_background() {
  local label="$1"
  shift
  if ((DRY_RUN)); then
    print_command "$@"
    return 0
  fi
  "$@" &
  PARALLEL_PIDS+=($!)
  PARALLEL_LABELS+=("${label}")
}

wait_for_parallel_group() {
  local failures=0
  local index=0
  local count="${#PARALLEL_PIDS[@]}"
  if ((count == 0)); then
    PARALLEL_PIDS=()
    PARALLEL_LABELS=()
    return 0
  fi
  for pid in "${PARALLEL_PIDS[@]}"; do
    if ! wait "${pid}"; then
      echo "Parallel command failed: ${PARALLEL_LABELS[$index]}" >&2
      failures=1
    fi
    index=$((index + 1))
  done
  PARALLEL_PIDS=()
  PARALLEL_LABELS=()
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
  echo "[step1] sync infrastructure"
  run_command_in_background \
    "step1.stock_basic_company" \
    bash "${SCRIPT_DIR}/sync_infrastructure.sh" --targets stock_basic,stock_company
  run_command_in_background \
    "step1.trade_cal" \
    bash "${SCRIPT_DIR}/sync_infrastructure.sh" --targets trade_cal --start "${START_DATE}" --end "${END_DATE}"
  wait_for_parallel_group
}

run_step2() {
  local backfill_jobs
  backfill_jobs="$(build_backfill_jobs)"
  if [[ -z "${backfill_jobs}" ]]; then
    echo "Failed to resolve recommended backfill job list" >&2
    exit 1
  fi

  echo "[step2] run bulk backfill excluding manual jobs and explicit range jobs"
  local cmd=(
    bash "${SCRIPT_DIR}/run_backfill.sh"
    --jobs "${backfill_jobs}"
    --start "${START_DATE}"
    --end "${END_DATE}"
  )
  if [[ -n "${MAX_WORKERS}" ]]; then
    cmd+=(--max-workers "${MAX_WORKERS}")
  fi
  run_command "${cmd[@]}"
}

run_step3() {
  echo "[step3] run explicit range jobs"
  run_command_in_background \
    "step3.kpl_list" \
    bash "${SCRIPT_DIR}/run_job.sh" --job kpl_list --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  run_command_in_background \
    "step3.report_rc" \
    bash "${SCRIPT_DIR}/run_job.sh" --job report_rc --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  wait_for_parallel_group
}

run_step4() {
  echo "[step4] run optional manual backfill jobs"
  run_command_in_background \
    "step4.hm_list" \
    bash "${SCRIPT_DIR}/run_job.sh" --job hm_list --param "snapshot_date=${SNAPSHOT_DATE}"
  run_command_in_background \
    "step4.pledge_detail" \
    bash "${SCRIPT_DIR}/run_job.sh" --job pledge_detail --param "snapshot_date=${SNAPSHOT_DATE}"
  run_command_in_background \
    "step4.cyq_chips" \
    bash "${SCRIPT_DIR}/run_job.sh" --job cyq_chips --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
  run_command_in_background \
    "step4.fina_audit" \
    bash "${SCRIPT_DIR}/run_job.sh" --job fina_audit --param "start_date=${START_DATE}" --param "end_date=${END_DATE}"
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
