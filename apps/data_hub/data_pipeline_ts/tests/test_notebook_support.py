from __future__ import annotations

import json
from pathlib import Path


def test_data_pipeline_ts_notebooks_contains_single_demo_notebook():
    notebooks_dir = Path(__file__).resolve().parents[1] / "notebooks"

    assert notebooks_dir.exists()
    assert sorted(path.name for path in notebooks_dir.glob("*.ipynb")) == [
        "01_db_tushare_demo.ipynb",
    ]


def test_db_tushare_demo_notebook_contains_editable_database_and_tushare_examples():
    notebook_path = (
        Path(__file__).resolve().parents[1]
        / "notebooks"
        / "01_db_tushare_demo.ipynb"
    )

    notebook = json.loads(notebook_path.read_text())
    sources = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    kernelspec = notebook.get("metadata", {}).get("kernelspec", {})

    assert kernelspec.get("name") == "python3"
    assert "DB_URL = " in sources
    assert "mysql+pymysql://" in sources
    assert "create_engine(DB_URL, pool_pre_ping=True)" in sources
    assert "SELECT DATABASE()" in sources
    assert "QUERY_SQL = " in sources
    assert 'pd.read_sql_query(QUERY_SQL, con=engine)' in sources
    assert "import tushare as ts" in sources
    assert 'pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))' in sources
    assert "pro.stock_basic(" in sources
