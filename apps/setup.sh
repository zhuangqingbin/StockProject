#!/usr/bin/env bash
# ---------------------------------------------------------
# apps/setup.sh — one-command setup for the data_hub suite
#
# Supports macOS (arm64/x86_64) and Linux (Debian/Ubuntu/CentOS/Fedora).
# Idempotent: safe to re-run at any time.
#
# Usage:
#   bash apps/setup.sh              # full interactive setup
#   bash apps/setup.sh --skip-db    # skip MySQL database creation
#   bash apps/setup.sh --skip-infra # skip infrastructure data sync
#   bash apps/setup.sh --skip-fe    # skip frontend npm install
#   bash apps/setup.sh --skip-cron  # skip scheduled task installation
# ---------------------------------------------------------




set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/apps/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
FRONTEND_DIR="${REPO_ROOT}/apps/data_hub/data_explorer/frontend"
ENV_FILE="${REPO_ROOT}/.env"
ENV_EXAMPLE="${REPO_ROOT}/env.example"

# -- parse flags ----------------------------------------------------------
SKIP_DB=false
SKIP_INFRA=false
SKIP_FE=false
SKIP_CRON=false

for arg in "$@"; do
  case "${arg}" in
    --skip-db)    SKIP_DB=true ;;
    --skip-infra) SKIP_INFRA=true ;;
    --skip-fe)    SKIP_FE=true ;;
    --skip-cron)  SKIP_CRON=true ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown flag: ${arg}. Use --help for usage." >&2
      exit 1
      ;;
  esac
done

# -- helpers ---------------------------------------------------------------
info()  { printf "\033[1;34m[setup]\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m[  ok ]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
fail()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*" >&2; exit 1; }

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)  echo "linux" ;;
    *)      echo "unknown" ;;
  esac
}

OS="$(detect_os)"
if [[ "${OS}" == "unknown" ]]; then
  fail "Unsupported OS: $(uname -s). Only macOS and Linux are supported."
fi

# =========================================================================
# Step 1: Check system prerequisites
# =========================================================================
info "Step 1/7: Checking system prerequisites..."

# -- Python 3.11+ ---------------------------------------------------------
PYTHON3=""
for candidate in python3.11 python3.12 python3.13 python3; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    ver="$("${candidate}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    major="${ver%%.*}"
    minor="${ver#*.}"
    if [[ "${major}" -ge 3 ]] && [[ "${minor}" -ge 11 ]]; then
      PYTHON3="${candidate}"
      break
    fi
  fi
done

if [[ -z "${PYTHON3}" ]]; then
  echo ""
  warn "Python 3.11+ not found."
  if [[ "${OS}" == "macos" ]]; then
    echo "  Install with:  brew install python@3.11"
  else
    echo "  Debian/Ubuntu: sudo apt install python3.11 python3.11-venv"
    echo "  CentOS/Fedora: sudo dnf install python3.11"
  fi
  fail "Please install Python 3.11+ and re-run this script."
fi
ok "Python: ${PYTHON3} ($("${PYTHON3}" --version 2>&1))"

# -- Node.js (optional, for frontend) -------------------------------------
HAS_NODE=false
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  HAS_NODE=true
  ok "Node.js: $(node --version), npm: $(npm --version)"
else
  warn "Node.js / npm not found — frontend (data_explorer) will not be set up."
  if [[ "${OS}" == "macos" ]]; then
    echo "  Install with:  brew install node"
  else
    echo "  Debian/Ubuntu: sudo apt install nodejs npm"
    echo "  Or use nvm:    https://github.com/nvm-sh/nvm"
  fi
  SKIP_FE=true
fi

# =========================================================================
# Step 2: Create virtualenv & install Python dependencies
# =========================================================================
info "Step 2/7: Setting up Python virtualenv..."

if [[ ! -x "${PYTHON_BIN}" ]]; then
  "${PYTHON3}" -m venv "${VENV_DIR}"
  info "Created virtualenv at ${VENV_DIR}"
fi

"${PYTHON_BIN}" -m pip install --upgrade pip --quiet
"${PYTHON_BIN}" -m pip install -r "${REPO_ROOT}/apps/requirements.txt" --quiet
ok "Python dependencies installed."

# =========================================================================
# Step 3: Environment configuration (.env)
# =========================================================================
info "Step 3/7: Checking environment configuration..."

if [[ -f "${ENV_FILE}" ]]; then
  ok ".env already exists at ${ENV_FILE}"
else
  if [[ -f "${ENV_EXAMPLE}" ]]; then
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    warn "Created .env from env.example. Please edit it with your actual credentials:"
    echo ""
    echo "  ${ENV_FILE}"
    echo ""
    echo "  Required variables:"
    echo "    TUSHARE_TOKEN       — your TuShare API token"
    echo "    MYSQL_HOST          — MySQL host (default: 127.0.0.1)"
    echo "    MYSQL_PORT          — MySQL port (default: 3306)"
    echo "    MYSQL_USER          — MySQL user"
    echo "    MYSQL_PASSWORD      — MySQL password"
    echo "    TS_MYSQL_DATABASE   — TuShare database name"
    echo "    AK_MYSQL_DATABASE   — AkShare database name"
    echo ""
    read -rp "Press Enter after editing .env to continue (or Ctrl-C to abort)..."
  else
    fail "No env.example found at ${ENV_EXAMPLE}. Cannot create .env."
  fi
fi

# -- load .env for subsequent steps ----------------------------------------
# Use line-by-line parsing instead of `source` to avoid syntax errors
# from values containing shell-special characters (brackets, quotes, etc.)
while IFS= read -r line || [[ -n "${line}" ]]; do
  [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
  if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*) ]]; then
    key="${BASH_REMATCH[1]}"
    val="${BASH_REMATCH[2]}"
    val="${val#\"}" ; val="${val%\"}"
    val="${val#\'}" ; val="${val%\'}"
    export "${key}=${val}"
  fi
done < "${ENV_FILE}"

# =========================================================================
# Step 4: MySQL database creation
# =========================================================================
MYSQL_OK=false

if [[ "${SKIP_DB}" == "false" ]]; then
  info "Step 4/7: Checking MySQL databases..."

  MYSQL_CMD=""
  if command -v mysql >/dev/null 2>&1; then
    MYSQL_CMD="mysql"
  elif command -v mariadb >/dev/null 2>&1; then
    MYSQL_CMD="mariadb"
  fi

  if [[ -z "${MYSQL_CMD}" ]]; then
    warn "mysql/mariadb client not found."
    echo ""
    echo "  Install MySQL:"
    if [[ "${OS}" == "macos" ]]; then
      echo "    brew install mysql"
      echo "    brew services start mysql"
    else
      echo "    Debian/Ubuntu:              sudo apt install mysql-server mysql-client"
      echo "    CentOS/Fedora/AliCloud:     sudo dnf install mysql-server mysql"
      echo "    Then start:                 sudo systemctl start mysqld"
    fi
    echo ""
    echo "  After install, set the root password:"
    echo "    sudo mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD'; FLUSH PRIVILEGES;\""
    echo ""
    echo "  If 'sudo mysql' fails with Access Denied, reset password with:"
    echo "    sudo systemctl stop mysqld"
    echo "    sudo mysqld --skip-grant-tables --user=mysql &"
    echo "    mysql -u root -e \"FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';\""
    echo "    sudo pkill mysqld && sudo systemctl start mysqld"
    echo ""
    echo "  Steps 4 and 6 will be skipped."
    SKIP_INFRA=true
  else
    MYSQL_ARGS=(-h "${MYSQL_HOST:-127.0.0.1}" -P "${MYSQL_PORT:-3306}" -u "${MYSQL_USER:-root}")
    if [[ -n "${MYSQL_PASSWORD:-}" ]]; then
      MYSQL_ARGS+=(-p"${MYSQL_PASSWORD}")
    fi

    # -- connectivity check --------------------------------------------------
    if "${MYSQL_CMD}" "${MYSQL_ARGS[@]}" -e "SELECT 1" >/dev/null 2>&1; then
      MYSQL_OK=true
      ok "MySQL connection OK (${MYSQL_HOST:-127.0.0.1}:${MYSQL_PORT:-3306})"
    else
      warn "Cannot connect to MySQL at ${MYSQL_HOST:-127.0.0.1}:${MYSQL_PORT:-3306}"
      echo ""
      if [[ "${OS}" == "linux" ]]; then
        echo "  1. Check if MySQL is running:"
        echo "       sudo systemctl status mysqld       # CentOS/Fedora/AliCloud"
        echo "       sudo systemctl status mysql        # Debian/Ubuntu"
        echo "       sudo systemctl status mariadb      # MariaDB"
        echo ""
        echo "  2. Start MySQL:"
        echo "       sudo systemctl start mysqld"
        echo ""
        echo "  3. If Access Denied, reset root password:"
        echo "       sudo systemctl stop mysqld"
        echo "       sudo mysqld --skip-grant-tables --user=mysql &"
        echo "       mysql -u root -e \"FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';\""
        echo "       sudo pkill mysqld && sudo systemctl start mysqld"
      else
        echo "  1. Check if MySQL is running:"
        echo "       brew services list | grep mysql"
        echo ""
        echo "  2. Start MySQL:"
        echo "       brew services start mysql"
      fi
      echo ""
      echo "  4. Verify .env credentials (MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD)."
      echo "  Steps 4 and 6 (database creation & infrastructure sync) will be skipped."
      echo ""
      SKIP_INFRA=true
    fi

    # -- create databases if connected ---------------------------------------
    if [[ "${MYSQL_OK}" == "true" ]]; then
      for db_var in TS_MYSQL_DATABASE AK_MYSQL_DATABASE; do
        db_name="${!db_var:-}"
        if [[ -z "${db_name}" ]]; then
          warn "${db_var} not set in .env, skipping."
          continue
        fi
        if "${MYSQL_CMD}" "${MYSQL_ARGS[@]}" -e "USE \`${db_name}\`" 2>/dev/null; then
          ok "Database '${db_name}' exists."
        else
          info "Creating database '${db_name}'..."
          "${MYSQL_CMD}" "${MYSQL_ARGS[@]}" -e "CREATE DATABASE \`${db_name}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
          ok "Database '${db_name}' created."
        fi
      done
    fi
  fi
else
  info "Step 4/7: Skipped (--skip-db)."
fi

# =========================================================================
# Step 5: Frontend dependencies (npm install)
# =========================================================================
if [[ "${SKIP_FE}" == "false" ]]; then
  info "Step 5/7: Installing frontend dependencies..."
  if [[ -f "${FRONTEND_DIR}/package.json" ]]; then
    npm --prefix "${FRONTEND_DIR}" install --silent 2>/dev/null || npm --prefix "${FRONTEND_DIR}" install
    ok "Frontend dependencies installed."
  else
    warn "Frontend package.json not found at ${FRONTEND_DIR}."
  fi
else
  info "Step 5/7: Skipped (--skip-fe or no Node.js)."
fi

# =========================================================================
# Step 6: Sync infrastructure data
# =========================================================================
if [[ "${SKIP_INFRA}" == "false" ]]; then
  info "Step 6/7: Syncing infrastructure data (stock_basic, stock_company, trade_cal)..."
  INFRA_SCRIPT="${REPO_ROOT}/apps/data_hub/data_pipeline_ts/scripts/sync_infrastructure.sh"
  if [[ -x "${INFRA_SCRIPT}" ]] || [[ -f "${INFRA_SCRIPT}" ]]; then
    CURRENT_YEAR="$(date +%Y)"
    bash "${INFRA_SCRIPT}" \
      --targets stock_basic,stock_company,trade_cal \
      --start 20100101 \
      --end "${CURRENT_YEAR}1231"
    ok "Infrastructure data synced."
  else
    warn "Infrastructure script not found: ${INFRA_SCRIPT}"
  fi
else
  info "Step 6/7: Skipped (--skip-infra)."
fi

# =========================================================================
# Step 7: Install scheduled tasks (launchd / cron)
# =========================================================================
if [[ "${SKIP_CRON}" == "false" ]]; then
  info "Step 7/7: Installing scheduled tasks..."

  if [[ "${OS}" == "macos" ]]; then
    LAUNCHD_SCRIPT="${REPO_ROOT}/apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh"
    if [[ -f "${LAUNCHD_SCRIPT}" ]]; then
      bash "${LAUNCHD_SCRIPT}"
      ok "launchd agents installed."
    else
      warn "install_launchd.sh not found."
    fi
  elif [[ "${OS}" == "linux" ]]; then
    # Generate cron entries from profile specs
    CRON_ENTRIES="$("${PYTHON_BIN}" -c "
from apps.data_hub.data_pipeline_ts.jobs.profiles import PROFILE_SPECS

run_script = '${REPO_ROOT}/apps/data_hub/data_pipeline_ts/scripts/run_daily.sh'
log_dir = '${REPO_ROOT}/apps/data_hub/data_pipeline_ts/.logs'

for profile, spec in PROFILE_SPECS.items():
    if spec.cron is None:
        continue
    label = profile.value.replace('_', '-')
    print(f'{spec.cron}  bash {run_script} --profiles {profile.value} >> {log_dir}/{label}.log 2>&1')
" 2>/dev/null || true)"

    if [[ -n "${CRON_ENTRIES}" ]]; then
      LOG_DIR="${REPO_ROOT}/apps/data_hub/data_pipeline_ts/.logs"
      mkdir -p "${LOG_DIR}"

      # Merge with existing crontab, replacing old stockproject entries
      MARKER="# stockproject:data_pipeline_ts"
      EXISTING_CRON="$(crontab -l 2>/dev/null || true)"
      FILTERED_CRON="$(echo "${EXISTING_CRON}" | grep -v "${MARKER}" || true)"

      TAGGED_ENTRIES=""
      while IFS= read -r line; do
        if [[ -n "${line}" ]]; then
          TAGGED_ENTRIES="${TAGGED_ENTRIES}${line}  ${MARKER}
"
        fi
      done <<< "${CRON_ENTRIES}"

      NEW_CRON="${FILTERED_CRON}
${TAGGED_ENTRIES}"

      echo "${NEW_CRON}" | crontab -
      ok "cron jobs installed. Verify with: crontab -l"
    else
      warn "Could not generate cron entries from profile specs."
    fi
  fi
else
  info "Step 7/7: Skipped (--skip-cron)."
fi

# =========================================================================
# Done — summary
# =========================================================================
echo ""
echo "=========================================="
info "Setup complete!"
echo "=========================================="
echo ""
echo "  Step  What                              Status"
echo "  ────  ────────────────────────────────  ──────────────────────────"
echo "  1/7   System prerequisites (Python/Node) checked"
echo "  2/7   Python virtualenv & dependencies  $(  [[ -x "${PYTHON_BIN}" ]] && echo "ok" || echo "FAILED")"
echo "  3/7   Environment config (.env)         $(  [[ -f "${ENV_FILE}" ]]   && echo "ok" || echo "MISSING")"
echo "  4/7   MySQL databases                   $(  [[ "${SKIP_DB}" == "true" ]] && echo "skipped" || { [[ "${MYSQL_OK}" == "true" ]] && echo "ok" || echo "NO CONNECTION"; })"
echo "  5/7   Frontend dependencies (npm)       $(  [[ "${SKIP_FE}"    == "true" ]] && echo "skipped" || echo "done")"
echo "  6/7   Infrastructure data sync          $(  [[ "${SKIP_INFRA}" == "true" ]] && echo "skipped" || echo "done")"
echo "  7/7   Scheduled tasks ($(  [[ "${OS}" == "macos" ]] && echo "launchd" || echo "cron"))          $(  [[ "${SKIP_CRON}"  == "true" ]] && echo "skipped" || echo "done")"
echo ""
echo "Next steps:"
echo ""
echo "  Run pipeline manually:"
echo "    bash apps/data_hub/data_pipeline_ts/scripts/run_daily.sh --profiles trade_day_post_close_core"
echo ""
echo "  Backfill history:"
echo "    bash apps/data_hub/data_pipeline_ts/scripts/run_backfill.sh --profiles trade_day_post_close_core,trade_day_post_close_core,trade_day_post_close_extended,reference_trade_day_post_close,financial_calendar_nightly,reference_calendar_nightly --start 20250101 --end 20260101"
echo ""
echo "  Start data explorer (web UI):"
echo "    bash apps/data_hub/data_explorer/scripts/run.sh dev"
echo ""
echo "  Install scheduled tasks (auto-run daily pipelines):"
if [[ "${OS}" == "macos" ]]; then
  echo "    bash apps/data_hub/data_pipeline_ts/scripts/install_launchd.sh"
  echo "    # Verify: launchctl list | grep stockproject"
  echo "    # Unload: launchctl bootout gui/\$(id -u) ~/Library/LaunchAgents/com.stockproject.*.plist"
else
  echo "    bash apps/setup.sh --skip-db --skip-infra --skip-fe    # only install cron jobs"
  echo "    # Verify: crontab -l"
  echo "    # Remove: crontab -l | grep -v stockproject | crontab -"
fi
echo ""
echo "  Scheduled profiles and their times:"
echo "    09:25  trade_day_pre_open            (盘前: ST标记/涨跌停价/港通成分等)"
echo "    18:00  trade_day_post_close_core     (盘后主链路: 日行情/资金流/指数/龙虎榜)"
echo "    18:35  trade_day_post_close_extended  (盘后扩展: 融资融券/涨跌停统计/港通Top10)"
echo "    18:40  reference_trade_day_post_close (大宗交易)"
echo "    21:30  financial_calendar_nightly     (财务公告: 利润表/资产负债表/现金流等)"
echo "    21:45  reference_calendar_nightly     (参考数据: 股东/质押/回购/解禁等)"
echo ""
