import sys
from pathlib import Path

# Ensure project root is on sys.path so shared.stock_core is importable
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from shared.stock_core.config import get_env, get_int, require_env

TUSHARE_TOKEN = require_env("TUSHARE_TOKEN")

QV_MYSQL_DATABASE = get_env("QV_MYSQL_DATABASE", "quantviz_database")
MYSQL_USER = require_env("MYSQL_USER")
MYSQL_PASSWORD = require_env("MYSQL_PASSWORD")
MYSQL_HOST = require_env("MYSQL_HOST")
MYSQL_PORT = get_int("MYSQL_PORT", 3306)
MYSQL_CHARSET = get_env("MYSQL_CHARSET", "utf8")

API_HOST = get_env("QV_API_HOST", "0.0.0.0")
API_PORT = get_int("QV_API_PORT", 8202)
DEBUG = get_env("QV_DEBUG", "false").lower() == "true"

DATABASE_URL = (
    f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
    f"{QV_MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
)
