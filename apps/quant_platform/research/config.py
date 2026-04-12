from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.stock_core.db import build_mysql_url


@dataclass(frozen=True)
class ResearchConfig:
    start_date: str = "2018-01-01"
    end_date: str | None = None
    database_env_name: str = "TS_MYSQL_DATABASE"
    panel_table: str = "stock_stk_factor_pro"
    output_dir: Path = Path("apps/quant_platform/research/output")


def build_tushare_db_url(database_env_name: str = "TS_MYSQL_DATABASE") -> str:
    return build_mysql_url(database_env_name)
