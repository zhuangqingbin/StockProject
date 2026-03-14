"""
配置文件 - 从 shared/stock_core 导入共享配置
"""
import os
import sys

# 添加仓库根目录到 path
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, REPO_ROOT)

# 从共享配置导入
from shared.stock_core.config import (
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE,
    MYSQL_CHARSET,
    TOKEN as TUSHARE_TOKEN
)
from shared.stock_core.db import build_mysql_url

# 数据库连接字符串
DATABASE_URL = build_mysql_url()

# OpenAI 配置（可选，用于 Chat 功能）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# API 配置
API_HOST = "0.0.0.0"
API_PORT = 8000
