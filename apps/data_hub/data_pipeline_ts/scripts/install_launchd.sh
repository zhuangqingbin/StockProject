#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
AGENT_DIR="${HOME}/Library/LaunchAgents"
LOG_DIR="${REPO_ROOT}/apps/data_hub/data_pipeline_ts/.logs"
RUN_SCRIPT="${REPO_ROOT}/apps/data_hub/data_pipeline_ts/scripts/run_daily.sh"
PYTHON_RESOLVER="${REPO_ROOT}/shared/scripts/resolve_project_python.sh"
DEFAULT_PATH="/usr/bin:/bin:/usr/sbin:/sbin:/Library/Developer/CommandLineTools/usr/bin"
MAX_WORKERS=""
mkdir -p "${AGENT_DIR}" "${LOG_DIR}"

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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-workers)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --max-workers" >&2
        exit 1
      fi
      if ! [[ "$2" =~ ^[1-9][0-9]*$ ]]; then
        echo "--max-workers must be a positive integer" >&2
        exit 1
      fi
      MAX_WORKERS="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

install_plan() {
  local label="$1"
  local hour="$2"
  local minute="$3"
  local profiles="$4"
  local max_workers="$5"
  local plist_path="${AGENT_DIR}/${label}.plist"
  local extra_program_arguments=""

  if [[ -n "${max_workers}" ]]; then
    extra_program_arguments=$(cat <<PLIST
    <string>--max-workers</string>
    <string>${max_workers}</string>
PLIST
)
  fi

  cat > "${plist_path}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${RUN_SCRIPT}</string>
    <string>--profiles</string>
    <string>${profiles}</string>
${extra_program_arguments}
  </array>
  <key>WorkingDirectory</key>
  <string>${REPO_ROOT}</string>
  <key>RunAtLoad</key>
  <false/>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>${hour}</integer>
    <key>Minute</key>
    <integer>${minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/${label}.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/${label}.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME}</string>
    <key>PATH</key>
    <string>${DEFAULT_PATH}</string>
    <key>PYTHONNOUSERSITE</key>
    <string>1</string>
  </dict>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
PLIST

  launchctl bootout "gui/$(id -u)" "${plist_path}" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "${plist_path}"
  echo "Installed ${plist_path}"
}

while IFS='|' read -r profile hour minute; do
  install_plan \
    "com.stockproject.stock-data-v1-orchestrator-v2.${profile//_/-}" \
    "${hour}" \
    "${minute}" \
    "${profile}" \
    "${MAX_WORKERS}"
done < <(
  cd "${REPO_ROOT}"
  PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" - <<'PY'
from apps.data_hub.data_pipeline_ts.jobs.profiles import PROFILE_SPECS


def parse_launchd_cron(raw_value: str) -> tuple[int, int]:
    minute, hour, day_of_month, month, day_of_week = raw_value.split()
    if day_of_month != "*" or month != "*" or day_of_week != "*":
        raise ValueError(f"Unsupported launchd cron schedule: {raw_value}")
    return int(hour), int(minute)


for profile, spec in PROFILE_SPECS.items():
    if spec.cron is None:
        continue
    hour, minute = parse_launchd_cron(spec.cron)
    print(f"{profile.value}|{hour}|{minute}")
PY
)
