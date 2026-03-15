#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SYSTEM_PYTHON="/Library/Developer/CommandLineTools/usr/bin/python3"
REQUIREMENTS_FILE="${REPO_ROOT}/apps/stock_data_platform/requirements.txt"
DEFAULT_VENV_LINK="${REPO_ROOT}/.venv-stock-data"

cd "${REPO_ROOT}"

normalize_arch() {
  case "$1" in
    arm64|arm64e|aarch64)
      echo "arm64"
      ;;
    x86_64|amd64|i386)
      echo "x86_64"
      ;;
    *)
      echo "$1"
      ;;
  esac
}

detect_supported_arches() {
  local detected=()

  if command -v arch >/dev/null 2>&1; then
    if [[ "$(arch -arm64 "${SYSTEM_PYTHON}" -c 'import platform; print(platform.machine())' 2>/dev/null || true)" == "arm64" ]]; then
      detected+=("arm64")
    fi
    if [[ "$(arch -x86_64 "${SYSTEM_PYTHON}" -c 'import platform; print(platform.machine())' 2>/dev/null || true)" == "x86_64" ]]; then
      detected+=("x86_64")
    fi
  fi

  if [[ "${#detected[@]}" -eq 0 ]]; then
    detected+=("$(normalize_arch "$(uname -m)")")
  fi

  printf '%s\n' "${detected[@]}"
}

create_env_for_arch() {
  local target_arch="$1"
  local venv_dir="${REPO_ROOT}/.venv-stock-data-${target_arch}"
  local arch_wrapper=()

  if command -v arch >/dev/null 2>&1; then
    arch_wrapper=(arch "-${target_arch}")
  fi

  "${arch_wrapper[@]}" "${SYSTEM_PYTHON}" -m venv "${venv_dir}"
  "${arch_wrapper[@]}" "${venv_dir}/bin/python" -m pip install --upgrade pip setuptools wheel
  "${arch_wrapper[@]}" "${venv_dir}/bin/pip" install -r "${REQUIREMENTS_FILE}"
  printf '%s\n' "${target_arch}" > "${venv_dir}/.python-arch"
}

SUPPORTED_ARCHES=()
while IFS= read -r detected_arch; do
  SUPPORTED_ARCHES+=("${detected_arch}")
done < <(detect_supported_arches)
for target_arch in "${SUPPORTED_ARCHES[@]}"; do
  create_env_for_arch "${target_arch}"
done

CURRENT_ARCH="$(normalize_arch "$(uname -m)")"
DEFAULT_LINK_ARCH="${CURRENT_ARCH}"
for supported_arch in "${SUPPORTED_ARCHES[@]}"; do
  if [[ "${supported_arch}" == "arm64" ]]; then
    DEFAULT_LINK_ARCH="arm64"
    break
  fi
done
if [[ -e "${DEFAULT_VENV_LINK}" && ! -L "${DEFAULT_VENV_LINK}" ]]; then
  rm -rf "${DEFAULT_VENV_LINK}"
fi
ln -sfn ".venv-stock-data-${DEFAULT_LINK_ARCH}" "${DEFAULT_VENV_LINK}"

echo "Created stock_data_platform environments:"
printf '  %s\n' "${SUPPORTED_ARCHES[@]/#/${REPO_ROOT}/.venv-stock-data-}"
echo "Updated ${DEFAULT_VENV_LINK} -> .venv-stock-data-${DEFAULT_LINK_ARCH}"
echo "Run jobs with: bash apps/stock_data_platform/scripts/run_stock_data_daily.sh --as-of 2026-02-09"
