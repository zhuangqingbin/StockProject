"""Database connection helper for analysis scripts."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.data_hub.data_pipeline_ts.execution.persistence import get_engine

import pandas as pd
from sqlalchemy import text


def query_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run SQL and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), con=conn, params=params)
