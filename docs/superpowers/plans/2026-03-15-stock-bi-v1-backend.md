# Stock BI V1 Backend Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend for stock_bi_v1 with 6 API modules, precompute pipeline, and TTL caching.

**Architecture:** Modular FastAPI backend following existing stock_bi patterns — raw SQL via `text()`, Pydantic response models, `cachetools.TTLCache`, router/service/repository per module. Reads from MySQL `stock_database` (read-only on existing tables, read-write on 3 new precomputed tables).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pandas, PyMySQL, Pydantic v2, cachetools

**Spec:** `docs/superpowers/specs/2026-03-15-stock-bi-v1-design.md`

**Existing patterns to follow:** `apps/stock_bi/codex/backend/` — same project structure, same shared config/db imports, same test style.

---

## Chunk 1: Backend Foundation

### Task 1: Project skeleton and infrastructure

**Files:**
- Create: `apps/stock_bi_v1/backend/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/__init__.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/settings.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/database.py`
- Create: `apps/stock_bi_v1/backend/infrastructure/cache.py`
- Create: `apps/stock_bi_v1/backend/models/__init__.py`
- Create: `apps/stock_bi_v1/backend/models/db_models.py`
- Create: `apps/stock_bi_v1/backend/models/api_models.py`
- Create: `apps/stock_bi_v1/backend/modules/__init__.py`
- Create: `apps/stock_bi_v1/backend/precompute/__init__.py`
- Reference: `shared/stock_core/config.py`
- Reference: `shared/stock_core/db.py`
- Reference: `apps/stock_bi/codex/backend/infrastructure/settings.py` (pattern to follow)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p apps/stock_bi_v1/backend/{infrastructure,models,modules/{market,industry,stock,flow,toplist,screener},precompute}
touch apps/stock_bi_v1/backend/__init__.py
touch apps/stock_bi_v1/backend/infrastructure/__init__.py
touch apps/stock_bi_v1/backend/models/__init__.py
touch apps/stock_bi_v1/backend/modules/__init__.py
touch apps/stock_bi_v1/backend/precompute/__init__.py
for mod in market industry stock flow toplist screener; do
  touch apps/stock_bi_v1/backend/modules/$mod/__init__.py
done
```

- [ ] **Step 2: Write infrastructure/settings.py**

```python
"""Application settings — ports, cache TTLs, database URL."""

from shared.stock_core.config import get_env, get_int
from shared.stock_core.db import build_mysql_url

DATABASE_URL = build_mysql_url()

API_HOST = get_env("STOCK_BI_V1_HOST", "0.0.0.0")
API_PORT = get_int("STOCK_BI_V1_PORT", 8100)

# Cache TTLs in seconds
CACHE_TTL_OVERVIEW = 300       # 5 min — dashboard overview
CACHE_TTL_KLINE_DAILY = 300    # 5 min — daily K-line
CACHE_TTL_KLINE_WEEKLY = 3600  # 1 hour — weekly/monthly K-line
CACHE_TTL_RANKING = 120        # 2 min — ranking lists
CACHE_TTL_SCREENER = 30        # 30 sec — screener results
CACHE_TTL_HEATMAP = 300        # 5 min — industry heatmap
CACHE_TTL_SEARCH = 600         # 10 min — stock search

__all__ = [
    "DATABASE_URL", "API_HOST", "API_PORT",
    "CACHE_TTL_OVERVIEW", "CACHE_TTL_KLINE_DAILY", "CACHE_TTL_KLINE_WEEKLY",
    "CACHE_TTL_RANKING", "CACHE_TTL_SCREENER", "CACHE_TTL_HEATMAP", "CACHE_TTL_SEARCH",
]
```

- [ ] **Step 3: Write infrastructure/database.py**

```python
"""Database engine and session factory."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base

from apps.stock_bi_v1.backend.infrastructure.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
Base = declarative_base()


def get_db() -> Session:
    """Yield a DB session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session


def execute_sql(sql: str, params: dict | None = None) -> list[dict]:
    """Execute raw SQL and return list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]


def execute_scalar(sql: str, params: dict | None = None):
    """Execute raw SQL and return single scalar value."""
    with engine.connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()
```

- [ ] **Step 4: Write infrastructure/cache.py**

```python
"""TTL cache utilities using cachetools."""

import functools
import hashlib
import json
from cachetools import TTLCache

# Global caches by TTL — each TTL gets its own cache instance
_caches: dict[int, TTLCache] = {}


def _get_cache(ttl: int, maxsize: int = 256) -> TTLCache:
    if ttl not in _caches:
        _caches[ttl] = TTLCache(maxsize=maxsize, ttl=ttl)
    return _caches[ttl]


def cached(ttl: int):
    """Decorator: cache function result with given TTL (seconds).

    Cache key is derived from function name + all arguments.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = _get_cache(ttl)
            key_data = f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"
            key = hashlib.md5(key_data.encode()).hexdigest()
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result
        return wrapper
    return decorator


def clear_all_caches():
    """Clear every TTL cache (used on precompute refresh)."""
    for c in _caches.values():
        c.clear()
```

- [ ] **Step 5: Commit foundation**

```bash
git add apps/stock_bi_v1/backend/
git commit -m "feat(stock_bi_v1): add backend infrastructure — settings, database, cache"
```

---

### Task 2: ORM models (existing tables + precomputed tables)

**Files:**
- Create: `apps/stock_bi_v1/backend/models/db_models.py`
- Reference: `apps/stock_bi/codex/backend/models.py` (pattern)
- Reference: spec section 4.4 (precomputed table schemas)

- [ ] **Step 1: Write db_models.py**

```python
"""SQLAlchemy ORM models for existing and precomputed tables."""

from sqlalchemy import Column, String, Float, Integer, Date, Text, DECIMAL, JSON, PrimaryKeyConstraint
from apps.stock_bi_v1.backend.infrastructure.database import Base


# --- Existing tables (read-only) ---

class DailyKline(Base):
    __tablename__ = "daily_kline"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)


class DailyBasic(Base):
    __tablename__ = "daily_basic"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    turnover_rate = Column(Float)
    turnover_rate_f = Column(Float)
    volume_ratio = Column(Float)
    pe_ttm = Column(Float)
    pb = Column(Float)
    ps_ttm = Column(Float)
    total_share = Column(Float)
    float_share = Column(Float)
    total_mv = Column(Float)
    circ_mv = Column(Float)


class Moneyflow(Base):
    __tablename__ = "moneyflow"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    buy_sm_amount = Column(Float)
    sell_sm_amount = Column(Float)
    buy_md_amount = Column(Float)
    sell_md_amount = Column(Float)
    buy_lg_amount = Column(Float)
    sell_lg_amount = Column(Float)
    buy_elg_amount = Column(Float)
    sell_elg_amount = Column(Float)
    net_mf_amount = Column(Float)


class MoneyflowHsgt(Base):
    __tablename__ = "moneyflow_hsgt"
    trade_date = Column(String(8), primary_key=True)
    ggt_ss = Column(Float)
    ggt_sz = Column(Float)
    hgt = Column(Float)
    sgt = Column(Float)
    north_money = Column(Float)
    south_money = Column(Float)


class IndexDaily(Base):
    __tablename__ = "index_daily"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    close = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)


class TopList(Base):
    __tablename__ = "top_list"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    name = Column(String(50))
    close = Column(Float)
    # NOTE: DB column is pct_change, aliased to pct_chg at ORM level
    pct_chg = Column("pct_change", Float)
    turnover_rate = Column(Float)
    amount = Column(Float)
    l_sell = Column(Float)
    l_buy = Column(Float)
    l_amount = Column(Float)
    net_amount = Column(Float)
    net_rate = Column(Float)
    amount_rate = Column(Float)
    float_values = Column(Float)
    reason = Column(String(200))


class StockBasic(Base):
    __tablename__ = "stock_basic"
    ts_code = Column(String(20), primary_key=True)
    symbol = Column(String(10))
    name = Column(String(50))
    area = Column(String(20))
    industry = Column(String(50))
    market = Column(String(20))
    exchange = Column(String(10))
    is_hs = Column(String(5))
    list_date = Column(String(8))


class StockStkLimit(Base):
    __tablename__ = "stock_stk_limit"
    ts_code = Column(String(20), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    pre_close = Column(Float)
    up_limit = Column(Float)
    down_limit = Column(Float)


# --- Precomputed tables (read-write) ---

class PrecomputedMarket(Base):
    __tablename__ = "precomputed_market"
    trade_date = Column(Date, primary_key=True)
    distribution = Column(JSON)
    up_limit_count = Column(Integer)
    down_limit_count = Column(Integer)
    flat_count = Column(Integer)
    total_amount = Column(DECIMAL(20, 2))
    top_gainers = Column(JSON)
    top_losers = Column(JSON)
    top_volume = Column(JSON)
    top_turnover = Column(JSON)


class PrecomputedIndustry(Base):
    __tablename__ = "precomputed_industry"
    trade_date = Column(Date, nullable=False)
    industry = Column(String(50), nullable=False)
    avg_pct_chg = Column(DECIMAL(8, 4))
    total_amount = Column(DECIMAL(20, 2))
    up_count = Column(Integer)
    down_count = Column(Integer)
    net_mf_amount = Column(DECIMAL(20, 2))
    stock_count = Column(Integer)
    __table_args__ = (
        PrimaryKeyConstraint("trade_date", "industry"),
    )


class PrecomputedLimit(Base):
    __tablename__ = "precomputed_limit"
    trade_date = Column(Date, primary_key=True)
    up_limit_stocks = Column(JSON)
    down_limit_stocks = Column(JSON)
    up_count = Column(Integer)
    down_count = Column(Integer)
    broken_count = Column(Integer)
    broken_rate = Column(DECIMAL(5, 2))
    tier_stats = Column(JSON)
```

- [ ] **Step 2: Write api_models.py (Pydantic response schemas)**

```python
"""Pydantic response models for API endpoints."""

from pydantic import BaseModel
from typing import Optional


# --- Market ---

class IndexItem(BaseModel):
    ts_code: str
    name: str
    close: float
    pct_chg: float
    amount: Optional[float] = None

class RankingItem(BaseModel):
    ts_code: str
    name: str
    pct_chg: float
    close: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None

class MarketOverviewResponse(BaseModel):
    trade_date: str
    indices: list[IndexItem]
    distribution: dict
    top_gainers: list[RankingItem]
    top_losers: list[RankingItem]
    top_volume: list[RankingItem]
    top_turnover: list[RankingItem]
    up_limit_count: int
    down_limit_count: int
    flat_count: int
    total_amount: float

class LimitStatsResponse(BaseModel):
    trade_date: str
    up_count: int
    down_count: int
    broken_count: int
    broken_rate: float
    tier_stats: dict

class LimitStockItem(BaseModel):
    ts_code: str
    name: str
    pct_chg: float
    close: float
    amount: float
    consecutive_days: Optional[int] = None
    industry: Optional[str] = None


# --- Industry ---

class IndustryHeatmapItem(BaseModel):
    industry: str
    avg_pct_chg: float
    total_amount: float
    up_count: int
    down_count: int
    stock_count: int

class IndustryDetailResponse(BaseModel):
    industry: str
    trade_date: str
    avg_pct_chg: float
    total_amount: float
    up_count: int
    down_count: int
    net_mf_amount: float
    stock_count: int

class IndustryStockItem(BaseModel):
    ts_code: str
    name: str
    pct_chg: float
    close: float
    amount: float
    turnover_rate: Optional[float] = None
    pe_ttm: Optional[float] = None
    net_mf_amount: Optional[float] = None


# --- Stock ---

class StockProfileResponse(BaseModel):
    ts_code: str
    name: str
    industry: str
    market: str
    exchange: str
    list_date: str
    close: float
    pct_chg: float
    open: float
    high: float
    low: float
    pre_close: float
    vol: float
    amount: float
    turnover_rate: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps_ttm: Optional[float] = None
    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None
    total_share: Optional[float] = None
    float_share: Optional[float] = None

class KlineItem(BaseModel):
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    vol: float
    amount: float
    pct_chg: Optional[float] = None

class ValuationItem(BaseModel):
    trade_date: str
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps_ttm: Optional[float] = None

class PeerItem(BaseModel):
    ts_code: str
    name: str
    pct_chg: float
    close: float
    pe_ttm: Optional[float] = None
    total_mv: Optional[float] = None

class SearchResult(BaseModel):
    ts_code: str
    name: str
    industry: Optional[str] = None


# --- Flow ---

class NorthMoneyItem(BaseModel):
    trade_date: str
    hgt: Optional[float] = None
    sgt: Optional[float] = None
    north_money: Optional[float] = None

class StockFlowItem(BaseModel):
    trade_date: str
    buy_elg_amount: Optional[float] = None
    sell_elg_amount: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    sell_lg_amount: Optional[float] = None
    buy_md_amount: Optional[float] = None
    sell_md_amount: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    sell_sm_amount: Optional[float] = None
    net_mf_amount: Optional[float] = None

class FlowDetailResponse(BaseModel):
    trade_date: str
    ts_code: str
    buy_elg_amount: Optional[float] = None
    sell_elg_amount: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    sell_lg_amount: Optional[float] = None
    buy_md_amount: Optional[float] = None
    sell_md_amount: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    sell_sm_amount: Optional[float] = None
    net_mf_amount: Optional[float] = None


# --- TopList ---

class TopListItem(BaseModel):
    ts_code: str
    name: str
    close: float
    pct_chg: float
    turnover_rate: Optional[float] = None
    amount: Optional[float] = None
    l_buy: Optional[float] = None
    l_sell: Optional[float] = None
    net_amount: Optional[float] = None
    reason: Optional[str] = None

class TopListHistoryItem(BaseModel):
    trade_date: str
    close: float
    pct_chg: float
    l_buy: Optional[float] = None
    l_sell: Optional[float] = None
    net_amount: Optional[float] = None
    reason: Optional[str] = None


# --- Screener ---

class ScreenerCondition(BaseModel):
    field: str
    operator: str  # "gt", "lt", "eq", "between"
    value: float | list[float]  # single value or [min, max] for between

class ScreenerRequest(BaseModel):
    conditions: list[ScreenerCondition]
    sort_by: str = "pct_chg"
    order: str = "desc"
    page: int = 0
    size: int = 50

class ScreenerResultItem(BaseModel):
    ts_code: str
    name: str
    industry: Optional[str] = None
    pct_chg: Optional[float] = None
    close: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    total_mv: Optional[float] = None
    turnover_rate: Optional[float] = None
    net_mf_amount: Optional[float] = None
    amount: Optional[float] = None

class ScreenerResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ScreenerResultItem]

class FilterMeta(BaseModel):
    field: str
    label: str
    category: str  # "行情", "估值", "资金+分类"
    operators: list[str]
```

- [ ] **Step 3: Commit models**

```bash
git add apps/stock_bi_v1/backend/models/
git commit -m "feat(stock_bi_v1): add ORM models and Pydantic API schemas"
```

---

### Task 3: Main app entry point and run scripts

**Files:**
- Create: `apps/stock_bi_v1/backend/main.py`
- Create: `apps/stock_bi_v1/run.py`
- Create: `apps/stock_bi_v1/run.sh`
- Create: `apps/stock_bi_v1/requirements.txt`
- Modify: `pyproject.toml` (add test path)
- Reference: `apps/stock_bi/codex/backend/main.py` (pattern)
- Reference: `apps/stock_bi/codex/run.py` (pattern)

- [ ] **Step 1: Write main.py**

```python
"""FastAPI application entry point for Stock BI V1."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.stock_bi_v1.backend.infrastructure.database import engine, Base
from apps.stock_bi_v1.backend.infrastructure.cache import clear_all_caches


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create precomputed tables if not exist
    Base.metadata.create_all(engine)
    # Ensure indexes exist
    _ensure_indexes()
    yield
    # Shutdown
    clear_all_caches()


app = FastAPI(title="Stock BI V1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers (after app is created)
from apps.stock_bi_v1.backend.modules.market.router import router as market_router
from apps.stock_bi_v1.backend.modules.industry.router import router as industry_router
from apps.stock_bi_v1.backend.modules.stock.router import router as stock_router
from apps.stock_bi_v1.backend.modules.flow.router import router as flow_router
from apps.stock_bi_v1.backend.modules.toplist.router import router as toplist_router
from apps.stock_bi_v1.backend.modules.screener.router import router as screener_router

app.include_router(market_router, prefix="/api/market", tags=["market"])
app.include_router(industry_router, prefix="/api/industry", tags=["industry"])
app.include_router(stock_router, prefix="/api/stock", tags=["stock"])
app.include_router(flow_router, prefix="/api/flow", tags=["flow"])
app.include_router(toplist_router, prefix="/api/toplist", tags=["toplist"])
app.include_router(screener_router, prefix="/api/screener", tags=["screener"])


@app.get("/health")
def health():
    return {"status": "ok"}


def _ensure_indexes():
    """Create indexes if they don't already exist."""
    from sqlalchemy import text as sql_text
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_dk_date_pctchg ON daily_kline(trade_date, pct_chg)",
        "CREATE INDEX IF NOT EXISTS idx_dk_date_amount ON daily_kline(trade_date, amount)",
        "CREATE INDEX IF NOT EXISTS idx_db_date_pe ON daily_basic(trade_date, pe_ttm)",
        "CREATE INDEX IF NOT EXISTS idx_db_date_pb ON daily_basic(trade_date, pb)",
        "CREATE INDEX IF NOT EXISTS idx_db_date_mv ON daily_basic(trade_date, total_mv)",
        "CREATE INDEX IF NOT EXISTS idx_db_date_turnover ON daily_basic(trade_date, turnover_rate)",
        "CREATE INDEX IF NOT EXISTS idx_mf_date_net ON moneyflow(trade_date, net_mf_amount)",
        "CREATE INDEX IF NOT EXISTS idx_sb_industry ON stock_basic(industry)",
    ]
    with engine.connect() as conn:
        for stmt in index_statements:
            try:
                conn.execute(sql_text(stmt))
            except Exception:
                pass  # Index may already exist or DB doesn't support IF NOT EXISTS
        conn.commit()
```

- [ ] **Step 2: Write run.py**

```python
"""Launch script for Stock BI V1 backend."""

import os
import sys

# Ensure repo root is in path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import uvicorn
from apps.stock_bi_v1.backend.infrastructure.settings import API_HOST, API_PORT


def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting Stock BI V1 on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "apps.stock_bi_v1.backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        reload_dirs=[app_dir],
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write run.sh**

```bash
#!/bin/bash
cd "$(dirname "$0")/../.." || exit 1
exec python3 -m apps.stock_bi_v1.run
```

- [ ] **Step 4: Write requirements.txt**

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0
pymysql
pydantic>=2.0
cachetools>=5.3
pandas>=2.0
```

- [ ] **Step 5: Add test path to pyproject.toml**

Add `"apps/stock_bi_v1/tests"` to the `testpaths` list in `pyproject.toml`.

- [ ] **Step 6: Commit**

```bash
git add apps/stock_bi_v1/run.py apps/stock_bi_v1/run.sh apps/stock_bi_v1/requirements.txt apps/stock_bi_v1/backend/main.py pyproject.toml
git commit -m "feat(stock_bi_v1): add main app entry, run scripts, requirements"
```

---

### Task 4: Tests for infrastructure

**Files:**
- Create: `apps/stock_bi_v1/tests/__init__.py`
- Create: `apps/stock_bi_v1/tests/test_infrastructure.py`
- Reference: `apps/stock_bi/codex/tests/test_backend_infrastructure.py`

- [ ] **Step 1: Write test_infrastructure.py**

```python
"""Tests for infrastructure: settings, cache, database helpers."""

import time
from apps.stock_bi_v1.backend.infrastructure.cache import cached, clear_all_caches, _caches


def test_settings_loads():
    from apps.stock_bi_v1.backend.infrastructure.settings import (
        DATABASE_URL, API_PORT, CACHE_TTL_OVERVIEW,
    )
    assert DATABASE_URL.startswith("mysql+pymysql://")
    assert isinstance(API_PORT, int)
    assert CACHE_TTL_OVERVIEW == 300


def test_cached_returns_same_result():
    call_count = 0

    @cached(ttl=60)
    def expensive(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    assert expensive(5) == 10
    assert expensive(5) == 10
    assert call_count == 1  # Only called once


def test_cached_different_args():
    @cached(ttl=60)
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    assert add(3, 4) == 7


def test_clear_all_caches():
    @cached(ttl=60)
    def fn():
        return "value"

    fn()
    assert len(_caches) > 0
    clear_all_caches()
    for c in _caches.values():
        assert len(c) == 0


def test_cached_ttl_expiry():
    call_count = 0

    @cached(ttl=1)
    def expiring():
        nonlocal call_count
        call_count += 1
        return "data"

    expiring()
    assert call_count == 1
    time.sleep(1.1)
    expiring()
    assert call_count == 2
```

- [ ] **Step 2: Run tests**

```bash
pytest apps/stock_bi_v1/tests/test_infrastructure.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/stock_bi_v1/tests/
git commit -m "test(stock_bi_v1): add infrastructure tests"
```

---

## Chunk 2: Market & Industry Modules

### Task 5: Market module — repository + service

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/market/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/market/service.py`

- [ ] **Step 1: Write market/repository.py**

```python
"""Market data repository — raw SQL queries."""

from apps.stock_bi_v1.backend.infrastructure.database import execute_sql, execute_scalar


def get_latest_trade_date() -> str | None:
    """Get the most recent trade_date from daily_kline."""
    return execute_scalar("SELECT MAX(trade_date) FROM daily_kline")


def get_index_daily(trade_date: str) -> list[dict]:
    """Get major index data for a given date."""
    indices = ("000001.SH", "399001.SZ", "399006.SZ", "000688.SH", "399005.SZ")
    placeholders = ", ".join(f":idx{i}" for i in range(len(indices)))
    params = {f"idx{i}": v for i, v in enumerate(indices)}
    params["td"] = trade_date
    return execute_sql(
        f"SELECT ts_code, close, open, high, low, pre_close, pct_chg, vol, amount "
        f"FROM index_daily WHERE trade_date = :td AND ts_code IN ({placeholders})",
        params,
    )


def get_precomputed_market(trade_date: str) -> dict | None:
    """Get precomputed market summary for a date."""
    rows = execute_sql(
        "SELECT * FROM precomputed_market WHERE trade_date = :td",
        {"td": trade_date},
    )
    return rows[0] if rows else None


def get_precomputed_limit(trade_date: str) -> dict | None:
    """Get precomputed limit analysis for a date."""
    rows = execute_sql(
        "SELECT * FROM precomputed_limit WHERE trade_date = :td",
        {"td": trade_date},
    )
    return rows[0] if rows else None


def get_distribution(trade_date: str) -> list[dict]:
    """Get price change distribution from daily_kline."""
    return execute_sql(
        "SELECT pct_chg FROM daily_kline WHERE trade_date = :td",
        {"td": trade_date},
    )


def get_ranking(trade_date: str, sort_by: str, order: str, limit: int) -> list[dict]:
    """Get ranking data by joining daily_kline + stock_basic + daily_basic.

    sort_by must be whitelisted to prevent SQL injection.
    """
    allowed_sort = {
        "pct_chg": "dk.pct_chg",
        "amount": "dk.amount",
        "turnover_rate": "db.turnover_rate",
    }
    sort_col = allowed_sort.get(sort_by, "dk.pct_chg")
    order_dir = "DESC" if order == "desc" else "ASC"

    return execute_sql(
        f"""SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount,
                   db.turnover_rate
            FROM daily_kline dk
            JOIN stock_basic sb ON dk.ts_code = sb.ts_code
            LEFT JOIN daily_basic db ON dk.ts_code = db.ts_code AND dk.trade_date = db.trade_date
            WHERE dk.trade_date = :td
            ORDER BY {sort_col} {order_dir}
            LIMIT :lim""",
        {"td": trade_date, "lim": limit},
    )
```

- [ ] **Step 2: Write market/service.py**

```python
"""Market module business logic."""

import json
from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import (
    CACHE_TTL_OVERVIEW, CACHE_TTL_RANKING,
)
from apps.stock_bi_v1.backend.modules.market import repository


INDEX_NAMES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
    "000688.SH": "科创50",
    "399005.SZ": "中小100",
}


def _convert(obj):
    """Convert Decimal/date types to JSON-friendly types."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(i) for i in obj]
    return obj


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_overview(trade_date: str | None = None) -> dict:
    """Build full dashboard overview data."""
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    if not trade_date:
        return {}

    # Index data
    raw_indices = repository.get_index_daily(trade_date)
    indices = [
        {**row, "name": INDEX_NAMES.get(row["ts_code"], row["ts_code"])}
        for row in raw_indices
    ]

    # Precomputed market data
    market = repository.get_precomputed_market(trade_date)
    if market:
        market = _convert(market)
        # Parse JSON fields if stored as strings
        for field in ("distribution", "top_gainers", "top_losers", "top_volume", "top_turnover"):
            if isinstance(market.get(field), str):
                market[field] = json.loads(market[field])

        return {
            "trade_date": trade_date,
            "indices": indices,
            "distribution": market.get("distribution", {}),
            "top_gainers": market.get("top_gainers", [])[:5],
            "top_losers": market.get("top_losers", [])[:5],
            "top_volume": market.get("top_volume", [])[:5],
            "top_turnover": market.get("top_turnover", [])[:5],
            "up_limit_count": market.get("up_limit_count", 0),
            "down_limit_count": market.get("down_limit_count", 0),
            "flat_count": market.get("flat_count", 0),
            "total_amount": market.get("total_amount", 0),
        }

    # Fallback: compute on-the-fly (slower)
    return {"trade_date": trade_date, "indices": indices, "distribution": {}, "top_gainers": [], "top_losers": [], "top_volume": [], "top_turnover": [], "up_limit_count": 0, "down_limit_count": 0, "flat_count": 0, "total_amount": 0}


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_indices(trade_date: str | None = None) -> list[dict]:
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    raw = repository.get_index_daily(trade_date)
    return [{**row, "name": INDEX_NAMES.get(row["ts_code"], row["ts_code"])} for row in raw]


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_distribution(trade_date: str | None = None) -> dict:
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    rows = repository.get_distribution(trade_date)
    bins = {"-10~-7": 0, "-7~-5": 0, "-5~-3": 0, "-3~0": 0, "0": 0, "0~3": 0, "3~5": 0, "5~7": 0, "7~10": 0}
    for row in rows:
        pct = row.get("pct_chg") or 0
        if pct <= -7: bins["-10~-7"] += 1
        elif pct <= -5: bins["-7~-5"] += 1
        elif pct <= -3: bins["-5~-3"] += 1
        elif pct < 0: bins["-3~0"] += 1
        elif pct == 0: bins["0"] += 1
        elif pct <= 3: bins["0~3"] += 1
        elif pct <= 5: bins["3~5"] += 1
        elif pct <= 7: bins["5~7"] += 1
        else: bins["7~10"] += 1
    return {"trade_date": trade_date, "distribution": bins}


@cached(ttl=CACHE_TTL_RANKING)
def get_ranking(trade_date: str | None = None, sort_by: str = "pct_chg", order: str = "desc", limit: int = 20) -> list[dict]:
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    return repository.get_ranking(trade_date, sort_by, order, limit)


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_limit_stats(trade_date: str | None = None) -> dict:
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    data = repository.get_precomputed_limit(trade_date)
    if not data:
        return {"trade_date": trade_date, "up_count": 0, "down_count": 0, "broken_count": 0, "broken_rate": 0, "tier_stats": {}}
    data = _convert(data)
    if isinstance(data.get("tier_stats"), str):
        data["tier_stats"] = json.loads(data["tier_stats"])
    return data


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_limit_list(trade_date: str | None = None, limit_type: str = "up") -> list[dict]:
    if not trade_date:
        trade_date = repository.get_latest_trade_date()
    data = repository.get_precomputed_limit(trade_date)
    if not data:
        return []
    data = _convert(data)
    field = "up_limit_stocks" if limit_type == "up" else "down_limit_stocks"
    stocks = data.get(field, [])
    if isinstance(stocks, str):
        stocks = json.loads(stocks)
    return stocks
```

- [ ] **Step 3: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/market/
git commit -m "feat(stock_bi_v1): add market module — repository and service"
```

---

### Task 6: Market module — router

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/market/router.py`

- [ ] **Step 1: Write market/router.py**

```python
"""Market API router — dashboard overview, indices, distribution, rankings, limit analysis."""

from fastapi import APIRouter, Query
from apps.stock_bi_v1.backend.modules.market import service

router = APIRouter()


@router.get("/overview")
def overview(date: str | None = Query(None)):
    return service.get_overview(date)


@router.get("/indices")
def indices(date: str | None = Query(None)):
    return service.get_indices(date)


@router.get("/distribution")
def distribution(date: str | None = Query(None)):
    return service.get_distribution(date)


@router.get("/ranking")
def ranking(
    sort_by: str = Query("pct_chg"),
    order: str = Query("desc"),
    limit: int = Query(20),
    date: str | None = Query(None),
):
    return service.get_ranking(date, sort_by, order, limit)


@router.get("/limit-stats")
def limit_stats(date: str | None = Query(None)):
    return service.get_limit_stats(date)


@router.get("/limit-list")
def limit_list(type: str = Query("up"), date: str | None = Query(None)):
    return service.get_limit_list(date, type)
```

- [ ] **Step 2: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/market/router.py
git commit -m "feat(stock_bi_v1): add market router"
```

---

### Task 7: Industry module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/industry/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/industry/service.py`
- Create: `apps/stock_bi_v1/backend/modules/industry/router.py`

- [ ] **Step 1: Write industry/repository.py**

```python
"""Industry data repository."""

from apps.stock_bi_v1.backend.infrastructure.database import execute_sql


def get_precomputed_industries(trade_date: str) -> list[dict]:
    """Get all industry stats for a date (heatmap data)."""
    return execute_sql(
        """SELECT industry, avg_pct_chg, total_amount, up_count, down_count,
                  net_mf_amount, stock_count
           FROM precomputed_industry
           WHERE trade_date = :td
           ORDER BY avg_pct_chg DESC""",
        {"td": trade_date},
    )


def get_industry_detail(industry: str, trade_date: str) -> dict | None:
    rows = execute_sql(
        """SELECT * FROM precomputed_industry
           WHERE trade_date = :td AND industry = :ind""",
        {"td": trade_date, "ind": industry},
    )
    return rows[0] if rows else None


def get_industry_stocks(industry: str, trade_date: str, sort_by: str, order: str) -> list[dict]:
    allowed_sort = {
        "pct_chg": "dk.pct_chg",
        "amount": "dk.amount",
        "turnover_rate": "db.turnover_rate",
        "pe_ttm": "db.pe_ttm",
        "net_mf_amount": "mf.net_mf_amount",
    }
    sort_col = allowed_sort.get(sort_by, "dk.pct_chg")
    order_dir = "DESC" if order == "desc" else "ASC"

    return execute_sql(
        f"""SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount,
                   db.turnover_rate, db.pe_ttm, mf.net_mf_amount
            FROM daily_kline dk
            JOIN stock_basic sb ON dk.ts_code = sb.ts_code
            LEFT JOIN daily_basic db ON dk.ts_code = db.ts_code AND dk.trade_date = db.trade_date
            LEFT JOIN moneyflow mf ON dk.ts_code = mf.ts_code AND dk.trade_date = mf.trade_date
            WHERE dk.trade_date = :td AND sb.industry = :ind
            ORDER BY {sort_col} {order_dir}""",
        {"td": trade_date, "ind": industry},
    )
```

- [ ] **Step 2: Write industry/service.py**

```python
"""Industry module business logic."""

from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import CACHE_TTL_HEATMAP
from apps.stock_bi_v1.backend.modules.market.repository import get_latest_trade_date
from apps.stock_bi_v1.backend.modules.industry import repository


def _convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _convert_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimal(i) for i in obj]
    return obj


@cached(ttl=CACHE_TTL_HEATMAP)
def get_heatmap(trade_date: str | None = None) -> list[dict]:
    if not trade_date:
        trade_date = get_latest_trade_date()
    rows = repository.get_precomputed_industries(trade_date)
    return _convert_decimal(rows)


@cached(ttl=CACHE_TTL_HEATMAP)
def get_detail(industry: str, trade_date: str | None = None) -> dict:
    if not trade_date:
        trade_date = get_latest_trade_date()
    row = repository.get_industry_detail(industry, trade_date)
    if not row:
        return {"industry": industry, "trade_date": trade_date}
    return _convert_decimal({**row, "trade_date": trade_date})


def get_stocks(industry: str, trade_date: str | None = None, sort_by: str = "pct_chg", order: str = "desc") -> list[dict]:
    if not trade_date:
        trade_date = get_latest_trade_date()
    rows = repository.get_industry_stocks(industry, trade_date, sort_by, order)
    return _convert_decimal(rows)
```

- [ ] **Step 3: Write industry/router.py**

```python
"""Industry API router."""

from fastapi import APIRouter, Query
from apps.stock_bi_v1.backend.modules.industry import service

router = APIRouter()


@router.get("/heatmap")
def heatmap(date: str | None = Query(None)):
    return service.get_heatmap(date)


@router.get("/detail")
def detail(name: str = Query(...), date: str | None = Query(None)):
    return service.get_detail(name, date)


@router.get("/stocks")
def stocks(
    name: str = Query(...),
    sort_by: str = Query("pct_chg"),
    order: str = Query("desc"),
    date: str | None = Query(None),
):
    return service.get_stocks(name, date, sort_by, order)
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/industry/
git commit -m "feat(stock_bi_v1): add industry module — heatmap, detail, stock ranking"
```

---

### Task 8: Tests for market and industry services

**Files:**
- Create: `apps/stock_bi_v1/tests/test_market_service.py`
- Create: `apps/stock_bi_v1/tests/test_industry_service.py`

- [ ] **Step 1: Write test_market_service.py**

```python
"""Unit tests for market service — test business logic with mocked repository."""

from unittest.mock import patch
from apps.stock_bi_v1.backend.infrastructure.cache import clear_all_caches


def setup_function():
    clear_all_caches()


@patch("apps.stock_bi_v1.backend.modules.market.repository.get_latest_trade_date", return_value="20260315")
@patch("apps.stock_bi_v1.backend.modules.market.repository.get_index_daily", return_value=[
    {"ts_code": "000001.SH", "close": 3200.0, "pct_chg": 1.5, "open": 3180.0, "high": 3210.0, "low": 3170.0, "pre_close": 3150.0, "vol": 100000.0, "amount": 500000.0},
])
@patch("apps.stock_bi_v1.backend.modules.market.repository.get_precomputed_market", return_value=None)
def test_overview_fallback_when_no_precomputed(mock_pc, mock_idx, mock_td):
    from apps.stock_bi_v1.backend.modules.market.service import get_overview
    result = get_overview()
    assert result["trade_date"] == "20260315"
    assert len(result["indices"]) == 1
    assert result["indices"][0]["name"] == "上证指数"
    assert result["top_gainers"] == []


@patch("apps.stock_bi_v1.backend.modules.market.repository.get_latest_trade_date", return_value="20260315")
@patch("apps.stock_bi_v1.backend.modules.market.repository.get_distribution", return_value=[
    {"pct_chg": 5.0}, {"pct_chg": -2.0}, {"pct_chg": 0.0}, {"pct_chg": 10.0},
])
def test_distribution_bins(mock_dist, mock_td):
    from apps.stock_bi_v1.backend.modules.market.service import get_distribution
    result = get_distribution()
    assert result["distribution"]["3~5"] == 1
    assert result["distribution"]["-3~0"] == 1
    assert result["distribution"]["0"] == 1
    assert result["distribution"]["7~10"] == 1


@patch("apps.stock_bi_v1.backend.modules.market.repository.get_latest_trade_date", return_value="20260315")
@patch("apps.stock_bi_v1.backend.modules.market.repository.get_ranking", return_value=[
    {"ts_code": "000001.SZ", "name": "平安银行", "pct_chg": 10.0, "close": 15.0, "amount": 50000.0, "turnover_rate": 5.0},
])
def test_ranking(mock_rank, mock_td):
    from apps.stock_bi_v1.backend.modules.market.service import get_ranking
    result = get_ranking(sort_by="pct_chg", order="desc", limit=5)
    assert len(result) == 1
    assert result[0]["name"] == "平安银行"
```

- [ ] **Step 2: Write test_industry_service.py**

```python
"""Unit tests for industry service."""

from unittest.mock import patch
from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.cache import clear_all_caches


def setup_function():
    clear_all_caches()


@patch("apps.stock_bi_v1.backend.modules.market.repository.get_latest_trade_date", return_value="20260315")
@patch("apps.stock_bi_v1.backend.modules.industry.repository.get_precomputed_industries", return_value=[
    {"industry": "银行", "avg_pct_chg": Decimal("1.5000"), "total_amount": Decimal("10000000.00"), "up_count": 20, "down_count": 5, "net_mf_amount": Decimal("500000.00"), "stock_count": 25},
])
def test_heatmap_converts_decimals(mock_ind, mock_td):
    from apps.stock_bi_v1.backend.modules.industry.service import get_heatmap
    result = get_heatmap()
    assert isinstance(result[0]["avg_pct_chg"], float)
    assert result[0]["industry"] == "银行"


@patch("apps.stock_bi_v1.backend.modules.market.repository.get_latest_trade_date", return_value="20260315")
@patch("apps.stock_bi_v1.backend.modules.industry.repository.get_industry_stocks", return_value=[
    {"ts_code": "601398.SH", "name": "工商银行", "pct_chg": 2.0, "close": 6.5, "amount": 100000.0, "turnover_rate": 0.5, "pe_ttm": 5.0, "net_mf_amount": 50000.0},
])
def test_get_stocks(mock_stocks, mock_td):
    from apps.stock_bi_v1.backend.modules.industry.service import get_stocks
    result = get_stocks("银行")
    assert len(result) == 1
    assert result[0]["ts_code"] == "601398.SH"
```

- [ ] **Step 3: Run tests**

```bash
pytest apps/stock_bi_v1/tests/test_market_service.py apps/stock_bi_v1/tests/test_industry_service.py -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/tests/
git commit -m "test(stock_bi_v1): add market and industry service tests"
```

---

## Chunk 3: Stock, Flow, TopList Modules

### Task 9: Stock module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/stock/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/stock/service.py`
- Create: `apps/stock_bi_v1/backend/modules/stock/router.py`

- [ ] **Step 1: Write stock/repository.py**

```python
"""Stock data repository."""

from apps.stock_bi_v1.backend.infrastructure.database import execute_sql


def search_stocks(query: str, limit: int = 20) -> list[dict]:
    return execute_sql(
        """SELECT ts_code, name, industry
           FROM stock_basic
           WHERE ts_code LIKE :q OR name LIKE :q
           LIMIT :lim""",
        {"q": f"%{query}%", "lim": limit},
    )


def get_stock_profile(ts_code: str) -> dict | None:
    from apps.stock_bi_v1.backend.modules.market.repository import get_latest_trade_date
    trade_date = get_latest_trade_date()
    rows = execute_sql(
        """SELECT sb.ts_code, sb.name, sb.industry, sb.market, sb.exchange, sb.list_date,
                  dk.close, dk.pct_chg, dk.open, dk.high, dk.low, dk.pre_close, dk.vol, dk.amount,
                  db.turnover_rate, db.pe_ttm, db.pb, db.ps_ttm,
                  db.total_mv, db.circ_mv, db.total_share, db.float_share
           FROM stock_basic sb
           LEFT JOIN daily_kline dk ON sb.ts_code = dk.ts_code AND dk.trade_date = :td
           LEFT JOIN daily_basic db ON sb.ts_code = db.ts_code AND db.trade_date = :td
           WHERE sb.ts_code = :code""",
        {"code": ts_code, "td": trade_date},
    )
    return rows[0] if rows else None


def get_kline(ts_code: str, start: str | None, end: str | None) -> list[dict]:
    conditions = ["ts_code = :code"]
    params = {"code": ts_code}
    if start:
        conditions.append("trade_date >= :start")
        params["start"] = start
    if end:
        conditions.append("trade_date <= :end")
        params["end"] = end
    where = " AND ".join(conditions)
    return execute_sql(
        f"""SELECT trade_date, open, high, low, close, vol, amount, pct_chg
            FROM daily_kline WHERE {where} ORDER BY trade_date""",
        params,
    )


def get_valuation_history(ts_code: str, start: str | None, end: str | None) -> list[dict]:
    conditions = ["ts_code = :code"]
    params = {"code": ts_code}
    if start:
        conditions.append("trade_date >= :start")
        params["start"] = start
    if end:
        conditions.append("trade_date <= :end")
        params["end"] = end
    where = " AND ".join(conditions)
    return execute_sql(
        f"""SELECT trade_date, pe_ttm, pb, ps_ttm
            FROM daily_basic WHERE {where} ORDER BY trade_date""",
        params,
    )


def get_peers(ts_code: str, trade_date: str) -> list[dict]:
    """Get same-industry stocks ranked by market cap."""
    return execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, db.pe_ttm, db.total_mv
           FROM stock_basic sb
           JOIN daily_kline dk ON sb.ts_code = dk.ts_code AND dk.trade_date = :td
           LEFT JOIN daily_basic db ON sb.ts_code = db.ts_code AND db.trade_date = :td
           WHERE sb.industry = (SELECT industry FROM stock_basic WHERE ts_code = :code)
           ORDER BY db.total_mv DESC
           LIMIT 20""",
        {"code": ts_code, "td": trade_date},
    )


def get_history(ts_code: str, start: str | None, end: str | None, page: int, size: int) -> tuple[list[dict], int]:
    conditions = ["ts_code = :code"]
    params: dict = {"code": ts_code}
    if start:
        conditions.append("trade_date >= :start")
        params["start"] = start
    if end:
        conditions.append("trade_date <= :end")
        params["end"] = end
    where = " AND ".join(conditions)

    from apps.stock_bi_v1.backend.infrastructure.database import execute_scalar
    total = execute_scalar(f"SELECT COUNT(*) FROM daily_kline WHERE {where}", params)

    params["offset"] = page * size
    params["size"] = size
    rows = execute_sql(
        f"""SELECT trade_date, open, high, low, close, vol, amount, pct_chg
            FROM daily_kline WHERE {where}
            ORDER BY trade_date DESC
            LIMIT :size OFFSET :offset""",
        params,
    )
    return rows, total or 0
```

- [ ] **Step 2: Write stock/service.py**

```python
"""Stock module business logic."""

import pandas as pd
from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import (
    CACHE_TTL_KLINE_DAILY, CACHE_TTL_KLINE_WEEKLY, CACHE_TTL_SEARCH,
)
from apps.stock_bi_v1.backend.modules.market.repository import get_latest_trade_date
from apps.stock_bi_v1.backend.modules.stock import repository


@cached(ttl=CACHE_TTL_SEARCH)
def search(query: str) -> list[dict]:
    return repository.search_stocks(query)


def get_profile(ts_code: str) -> dict | None:
    return repository.get_stock_profile(ts_code)


@cached(ttl=CACHE_TTL_KLINE_DAILY)
def get_kline(ts_code: str, period: str = "daily", start: str | None = None, end: str | None = None) -> list[dict]:
    rows = repository.get_kline(ts_code, start, end)
    if period == "daily":
        return rows
    return _resample_kline(rows, period)


def _resample_kline(rows: list[dict], period: str) -> list[dict]:
    """Convert daily K-line to weekly or monthly."""
    if not rows:
        return []
    df = pd.DataFrame(rows)
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    df = df.set_index("trade_date").sort_index()
    freq = "W" if period == "weekly" else "ME"
    resampled = df.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "vol": "sum",
        "amount": "sum",
        "pct_chg": lambda x: ((1 + x / 100).prod() - 1) * 100 if len(x) > 0 else 0,
    }).dropna(subset=["open"])
    resampled = resampled.reset_index()
    resampled["trade_date"] = resampled["trade_date"].dt.strftime("%Y%m%d")
    return resampled.to_dict("records")


def get_valuation_history(ts_code: str, start: str | None = None, end: str | None = None) -> list[dict]:
    return repository.get_valuation_history(ts_code, start, end)


def get_peers(ts_code: str) -> list[dict]:
    trade_date = get_latest_trade_date()
    return repository.get_peers(ts_code, trade_date)


def get_history(ts_code: str, start: str | None, end: str | None, page: int, size: int) -> dict:
    rows, total = repository.get_history(ts_code, start, end, page, size)
    return {"items": rows, "total": total, "page": page, "size": size}
```

- [ ] **Step 3: Write stock/router.py**

```python
"""Stock API router — search MUST be registered before {code} routes."""

from fastapi import APIRouter, Query
from apps.stock_bi_v1.backend.modules.stock import service

router = APIRouter()


# search must come before {code} to avoid path conflict
@router.get("/search")
def search(q: str = Query(...)):
    return service.search(q)


@router.get("/{code}/profile")
def profile(code: str):
    return service.get_profile(code)


@router.get("/{code}/kline")
def kline(
    code: str,
    period: str = Query("daily"),
    start: str | None = Query(None),
    end: str | None = Query(None),
):
    return service.get_kline(code, period, start, end)


@router.get("/{code}/valuation-history")
def valuation_history(
    code: str,
    start: str | None = Query(None),
    end: str | None = Query(None),
):
    return service.get_valuation_history(code, start, end)


@router.get("/{code}/peers")
def peers(code: str):
    return service.get_peers(code)


@router.get("/{code}/history")
def history(
    code: str,
    start: str | None = Query(None),
    end: str | None = Query(None),
    page: int = Query(0),
    size: int = Query(50),
):
    return service.get_history(code, start, end, page, size)
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/stock/
git commit -m "feat(stock_bi_v1): add stock module — profile, kline, valuation, peers, search"
```

---

### Task 10: Flow module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/flow/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/flow/service.py`
- Create: `apps/stock_bi_v1/backend/modules/flow/router.py`

- [ ] **Step 1: Write flow/repository.py**

```python
"""Flow data repository — north money and individual stock money flow."""

from apps.stock_bi_v1.backend.infrastructure.database import execute_sql


def get_north_money(days: int) -> list[dict]:
    return execute_sql(
        """SELECT trade_date, hgt, sgt, north_money
           FROM moneyflow_hsgt
           ORDER BY trade_date DESC
           LIMIT :days""",
        {"days": days},
    )


def get_stock_flow(ts_code: str, days: int) -> list[dict]:
    return execute_sql(
        """SELECT trade_date, buy_elg_amount, sell_elg_amount,
                  buy_lg_amount, sell_lg_amount,
                  buy_md_amount, sell_md_amount,
                  buy_sm_amount, sell_sm_amount,
                  net_mf_amount
           FROM moneyflow
           WHERE ts_code = :code
           ORDER BY trade_date DESC
           LIMIT :days""",
        {"code": ts_code, "days": days},
    )


def get_stock_flow_detail(ts_code: str, trade_date: str) -> dict | None:
    rows = execute_sql(
        """SELECT trade_date, ts_code,
                  buy_elg_amount, sell_elg_amount,
                  buy_lg_amount, sell_lg_amount,
                  buy_md_amount, sell_md_amount,
                  buy_sm_amount, sell_sm_amount,
                  net_mf_amount
           FROM moneyflow
           WHERE ts_code = :code AND trade_date = :td""",
        {"code": ts_code, "td": trade_date},
    )
    return rows[0] if rows else None
```

- [ ] **Step 2: Write flow/service.py**

```python
"""Flow module business logic."""

from apps.stock_bi_v1.backend.modules.flow import repository


def get_north_money(days: int = 30) -> list[dict]:
    rows = repository.get_north_money(days)
    rows.reverse()  # chronological order
    return rows


def get_stock_flow(ts_code: str, days: int = 30) -> list[dict]:
    rows = repository.get_stock_flow(ts_code, days)
    rows.reverse()
    return rows


def get_stock_flow_detail(ts_code: str, trade_date: str) -> dict | None:
    return repository.get_stock_flow_detail(ts_code, trade_date)
```

- [ ] **Step 3: Write flow/router.py**

```python
"""Flow API router — north money and stock-level money flow."""

from fastapi import APIRouter, Query
from apps.stock_bi_v1.backend.modules.flow import service

router = APIRouter()


@router.get("/north")
def north_money(days: int = Query(30)):
    return service.get_north_money(days)


@router.get("/stock/{code}")
def stock_flow(code: str, days: int = Query(30)):
    return service.get_stock_flow(code, days)


@router.get("/stock/{code}/detail")
def stock_flow_detail(code: str, date: str = Query(...)):
    return service.get_stock_flow_detail(code, date)
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/flow/
git commit -m "feat(stock_bi_v1): add flow module — north money, stock flow"
```

---

### Task 11: TopList module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/toplist/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/toplist/service.py`
- Create: `apps/stock_bi_v1/backend/modules/toplist/router.py`

- [ ] **Step 1: Write toplist/repository.py**

```python
"""TopList data repository."""

from apps.stock_bi_v1.backend.infrastructure.database import execute_sql


def get_daily_toplist(trade_date: str) -> list[dict]:
    return execute_sql(
        """SELECT ts_code, name, close, pct_change AS pct_chg,
                  turnover_rate, amount, l_buy, l_sell, net_amount, reason
           FROM top_list
           WHERE trade_date = :td
           ORDER BY pct_change DESC""",
        {"td": trade_date},
    )


def get_stock_toplist_history(ts_code: str) -> list[dict]:
    return execute_sql(
        """SELECT trade_date, close, pct_change AS pct_chg,
                  l_buy, l_sell, net_amount, reason
           FROM top_list
           WHERE ts_code = :code
           ORDER BY trade_date DESC""",
        {"code": ts_code},
    )
```

- [ ] **Step 2: Write toplist/service.py**

```python
"""TopList module business logic."""

from apps.stock_bi_v1.backend.modules.market.repository import get_latest_trade_date
from apps.stock_bi_v1.backend.modules.toplist import repository


def get_daily(trade_date: str | None = None) -> list[dict]:
    if not trade_date:
        trade_date = get_latest_trade_date()
    return repository.get_daily_toplist(trade_date)


def get_stock_history(ts_code: str) -> list[dict]:
    return repository.get_stock_toplist_history(ts_code)
```

- [ ] **Step 3: Write toplist/router.py**

```python
"""TopList API router."""

from fastapi import APIRouter, Query
from apps.stock_bi_v1.backend.modules.toplist import service

router = APIRouter()


@router.get("/daily")
def daily(date: str | None = Query(None)):
    return service.get_daily(date)


@router.get("/stock/{code}")
def stock_history(code: str):
    return service.get_stock_history(code)
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/toplist/
git commit -m "feat(stock_bi_v1): add toplist module"
```

---

## Chunk 4: Screener & Precompute

### Task 12: Screener module

**Files:**
- Create: `apps/stock_bi_v1/backend/modules/screener/repository.py`
- Create: `apps/stock_bi_v1/backend/modules/screener/service.py`
- Create: `apps/stock_bi_v1/backend/modules/screener/router.py`

- [ ] **Step 1: Write screener/service.py (core dynamic SQL logic)**

```python
"""Screener module — dynamic SQL construction with whitelist validation."""

import csv
import io
from apps.stock_bi_v1.backend.infrastructure.database import execute_sql, execute_scalar
from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import CACHE_TTL_SCREENER
from apps.stock_bi_v1.backend.modules.market.repository import get_latest_trade_date

# Whitelist: field_name -> (sql_expression, table_alias_needed)
FIELD_MAP = {
    # 行情维度
    "pct_chg": "dk.pct_chg",
    "close": "dk.close",
    "amount": "dk.amount",
    "vol": "dk.vol",
    "turnover_rate": "db.turnover_rate",
    # 估值维度
    "pe_ttm": "db.pe_ttm",
    "pb": "db.pb",
    "ps_ttm": "db.ps_ttm",
    "total_mv": "db.total_mv",
    "circ_mv": "db.circ_mv",
    "total_share": "db.total_share",
    "float_share": "db.float_share",
    # 资金维度
    "net_mf_amount": "mf.net_mf_amount",
    "net_elg_amount": "(mf.buy_elg_amount - mf.sell_elg_amount)",
    "net_lg_amount": "(mf.buy_lg_amount - mf.sell_lg_amount)",
    # 分类维度
    "industry": "sb.industry",
    "market": "sb.market",
}

FILTER_META = [
    {"field": "pct_chg", "label": "涨跌幅(%)", "category": "行情", "operators": ["gt", "lt", "between"]},
    {"field": "close", "label": "现价", "category": "行情", "operators": ["gt", "lt", "between"]},
    {"field": "amount", "label": "成交额", "category": "行情", "operators": ["gt", "lt", "between"]},
    {"field": "vol", "label": "成交量", "category": "行情", "operators": ["gt", "lt", "between"]},
    {"field": "turnover_rate", "label": "换手率(%)", "category": "行情", "operators": ["gt", "lt", "between"]},
    {"field": "pe_ttm", "label": "PE(TTM)", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "pb", "label": "PB", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "ps_ttm", "label": "PS(TTM)", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "total_mv", "label": "总市值", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "circ_mv", "label": "流通市值", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "total_share", "label": "总股本", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "float_share", "label": "流通股本", "category": "估值", "operators": ["gt", "lt", "between"]},
    {"field": "net_mf_amount", "label": "主力净流入", "category": "资金+分类", "operators": ["gt", "lt", "between"]},
    {"field": "net_elg_amount", "label": "特大单净流入", "category": "资金+分类", "operators": ["gt", "lt", "between"]},
    {"field": "net_lg_amount", "label": "大单净流入", "category": "资金+分类", "operators": ["gt", "lt", "between"]},
    {"field": "industry", "label": "行业", "category": "资金+分类", "operators": ["eq"]},
    {"field": "market", "label": "市场", "category": "资金+分类", "operators": ["eq"]},
    {"field": "is_st", "label": "是否ST", "category": "资金+分类", "operators": ["eq"]},
    # NOTE: 振幅(amplitude) and 连涨/连跌天数(consecutive_up/down) are deferred —
    # daily_kline does not contain these columns. They can be added when
    # stock_data_platform fetches additional fields from TuShare's daily API.
]


def get_filters() -> list[dict]:
    return FILTER_META


def _build_query(conditions: list[dict], sort_by: str, order: str, trade_date: str) -> tuple[str, dict, str, str]:
    """Build the WHERE clause from validated conditions.

    Returns (base_sql, params, sort_col, order_dir).
    """
    where_parts = ["dk.trade_date = :td"]
    params: dict = {"td": trade_date}

    # Track whether user explicitly set an ST filter
    has_st_filter = any(c["field"] == "is_st" for c in conditions)

    for i, cond in enumerate(conditions):
        field = cond["field"]
        op = cond["operator"]
        val = cond["value"]

        # Handle is_st specially (name-based detection)
        if field == "is_st":
            if val == 1:  # include only ST
                where_parts.append("(sb.name LIKE 'ST%' OR sb.name LIKE '*ST%')")
            else:  # exclude ST
                where_parts.append("sb.name NOT LIKE 'ST%' AND sb.name NOT LIKE '*ST%'")
            continue

        if field not in FIELD_MAP:
            continue  # skip unknown fields
        col = FIELD_MAP[field]

        if op == "gt":
            where_parts.append(f"{col} > :v{i}")
            params[f"v{i}"] = val
        elif op == "lt":
            where_parts.append(f"{col} < :v{i}")
            params[f"v{i}"] = val
        elif op == "eq":
            where_parts.append(f"{col} = :v{i}")
            params[f"v{i}"] = val
        elif op == "between" and isinstance(val, list) and len(val) == 2:
            where_parts.append(f"{col} BETWEEN :v{i}a AND :v{i}b")
            params[f"v{i}a"] = val[0]
            params[f"v{i}b"] = val[1]

    # Default: exclude ST stocks unless user explicitly included them
    if not has_st_filter:
        where_parts.append("sb.name NOT LIKE 'ST%' AND sb.name NOT LIKE '*ST%'")

    sort_col = FIELD_MAP.get(sort_by, "dk.pct_chg")
    order_dir = "DESC" if order == "desc" else "ASC"
    where = " AND ".join(where_parts)

    base_sql = f"""
        FROM daily_kline dk
        JOIN stock_basic sb ON dk.ts_code = sb.ts_code
        LEFT JOIN daily_basic db ON dk.ts_code = db.ts_code AND dk.trade_date = db.trade_date
        LEFT JOIN moneyflow mf ON dk.ts_code = mf.ts_code AND dk.trade_date = mf.trade_date
        WHERE {where}
    """
    return base_sql, params, sort_col, order_dir


def query(conditions: list[dict], sort_by: str = "pct_chg", order: str = "desc", page: int = 0, size: int = 50) -> dict:
    trade_date = get_latest_trade_date()
    base_sql, params, sort_col, order_dir = _build_query(conditions, sort_by, order, trade_date)

    total = execute_scalar(f"SELECT COUNT(*) {base_sql}", params) or 0

    params["lim"] = size
    params["off"] = page * size
    rows = execute_sql(
        f"""SELECT dk.ts_code, sb.name, sb.industry, dk.pct_chg, dk.close, dk.amount,
                   db.pe_ttm, db.pb, db.total_mv, db.turnover_rate, mf.net_mf_amount
            {base_sql}
            ORDER BY {sort_col} {order_dir}
            LIMIT :lim OFFSET :off""",
        params,
    )
    return {"total": total, "page": page, "size": size, "items": rows}


def export_csv(conditions: list[dict], sort_by: str = "pct_chg", order: str = "desc") -> str:
    """Export screener results as CSV string (max 5000 rows)."""
    trade_date = get_latest_trade_date()
    base_sql, params, sort_col, order_dir = _build_query(conditions, sort_by, order, trade_date)

    rows = execute_sql(
        f"""SELECT dk.ts_code, sb.name, sb.industry, dk.pct_chg, dk.close, dk.amount,
                   db.pe_ttm, db.pb, db.total_mv, db.turnover_rate, mf.net_mf_amount
            {base_sql}
            ORDER BY {sort_col} {order_dir}
            LIMIT 5000""",
        params,
    )

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return output.getvalue()
```

- [ ] **Step 2: Write screener/router.py**

```python
"""Screener API router."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from apps.stock_bi_v1.backend.models.api_models import ScreenerRequest
from apps.stock_bi_v1.backend.modules.screener import service

router = APIRouter()


@router.get("/filters")
def filters():
    return service.get_filters()


@router.post("/query")
def query(req: ScreenerRequest):
    return service.query(
        conditions=[c.model_dump() for c in req.conditions],
        sort_by=req.sort_by,
        order=req.order,
        page=req.page,
        size=req.size,
    )


@router.post("/export")
def export(req: ScreenerRequest):
    csv_data = service.export_csv(
        conditions=[c.model_dump() for c in req.conditions],
        sort_by=req.sort_by,
        order=req.order,
    )
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=screener_export.csv"},
    )
```

- [ ] **Step 3: Write screener/repository.py (empty — all logic in service)**

```python
"""Screener repository — queries are built dynamically in service.py."""
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/backend/modules/screener/
git commit -m "feat(stock_bi_v1): add screener module — dynamic SQL, whitelist, CSV export"
```

---

### Task 13: Precompute pipeline

**Files:**
- Create: `apps/stock_bi_v1/backend/precompute/runner.py`
- Create: `apps/stock_bi_v1/backend/precompute/market_summary.py`
- Create: `apps/stock_bi_v1/backend/precompute/industry_stats.py`
- Create: `apps/stock_bi_v1/backend/precompute/limit_analysis.py`

- [ ] **Step 1: Write precompute/market_summary.py**

```python
"""Precompute market daily summary."""

import json
from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.database import execute_sql, engine
from sqlalchemy import text


def _to_float(v):
    return float(v) if isinstance(v, Decimal) else v


def compute_market_summary(trade_date: str) -> dict:
    """Compute full market summary for a single trade date."""

    # Distribution
    rows = execute_sql(
        "SELECT pct_chg FROM daily_kline WHERE trade_date = :td",
        {"td": trade_date},
    )
    bins = {"-10~-7": 0, "-7~-5": 0, "-5~-3": 0, "-3~0": 0, "0": 0, "0~3": 0, "3~5": 0, "5~7": 0, "7~10": 0}
    flat = 0
    for r in rows:
        pct = r.get("pct_chg") or 0
        if pct == 0: flat += 1
        if pct <= -7: bins["-10~-7"] += 1
        elif pct <= -5: bins["-7~-5"] += 1
        elif pct <= -3: bins["-5~-3"] += 1
        elif pct < 0: bins["-3~0"] += 1
        elif pct == 0: bins["0"] += 1
        elif pct <= 3: bins["0~3"] += 1
        elif pct <= 5: bins["3~5"] += 1
        elif pct <= 7: bins["5~7"] += 1
        else: bins["7~10"] += 1

    # Limit counts from stock_stk_limit (accurate for all board types: ST ±5%, KCB ±20%, etc.)
    limit_counts = execute_sql(
        """SELECT
             SUM(CASE WHEN dk.close >= sl.up_limit AND sl.up_limit > 0 THEN 1 ELSE 0 END) AS up_limit,
             SUM(CASE WHEN dk.close <= sl.down_limit AND sl.down_limit > 0 THEN 1 ELSE 0 END) AS down_limit
           FROM daily_kline dk
           JOIN stock_stk_limit sl ON dk.ts_code = sl.ts_code AND dk.trade_date = sl.trade_date
           WHERE dk.trade_date = :td""",
        {"td": trade_date},
    )
    up_limit = int(limit_counts[0]["up_limit"] or 0) if limit_counts else 0
    down_limit = int(limit_counts[0]["down_limit"] or 0) if limit_counts else 0

    # Total amount
    amount_rows = execute_sql(
        "SELECT SUM(amount) AS total FROM daily_kline WHERE trade_date = :td",
        {"td": trade_date},
    )
    total_amount = _to_float(amount_rows[0]["total"]) if amount_rows else 0

    # Top gainers/losers/volume
    top_gainers = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount
           FROM daily_kline dk JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           WHERE dk.trade_date = :td ORDER BY dk.pct_chg DESC LIMIT 20""",
        {"td": trade_date},
    )
    top_losers = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount
           FROM daily_kline dk JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           WHERE dk.trade_date = :td ORDER BY dk.pct_chg ASC LIMIT 20""",
        {"td": trade_date},
    )
    top_volume = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount
           FROM daily_kline dk JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           WHERE dk.trade_date = :td ORDER BY dk.amount DESC LIMIT 20""",
        {"td": trade_date},
    )
    top_turnover = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, db.turnover_rate
           FROM daily_kline dk
           JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           JOIN daily_basic db ON dk.ts_code = db.ts_code AND dk.trade_date = db.trade_date
           WHERE dk.trade_date = :td ORDER BY db.turnover_rate DESC LIMIT 20""",
        {"td": trade_date},
    )

    return {
        "trade_date": trade_date,
        "distribution": bins,
        "up_limit_count": up_limit,
        "down_limit_count": down_limit,
        "flat_count": flat,
        "total_amount": total_amount,
        "top_gainers": [{k: _to_float(v) for k, v in r.items()} for r in top_gainers],
        "top_losers": [{k: _to_float(v) for k, v in r.items()} for r in top_losers],
        "top_volume": [{k: _to_float(v) for k, v in r.items()} for r in top_volume],
        "top_turnover": [{k: _to_float(v) for k, v in r.items()} for r in top_turnover],
    }


def save_market_summary(data: dict):
    td = data["trade_date"]
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM precomputed_market WHERE trade_date = :td"), {"td": td})
        conn.execute(
            text("""INSERT INTO precomputed_market
                    (trade_date, distribution, up_limit_count, down_limit_count, flat_count,
                     total_amount, top_gainers, top_losers, top_volume, top_turnover)
                    VALUES (:td, :dist, :up, :down, :flat, :amt, :tg, :tl, :tv, :tt)"""),
            {
                "td": td,
                "dist": json.dumps(data["distribution"]),
                "up": data["up_limit_count"],
                "down": data["down_limit_count"],
                "flat": data["flat_count"],
                "amt": data["total_amount"],
                "tg": json.dumps(data["top_gainers"]),
                "tl": json.dumps(data["top_losers"]),
                "tv": json.dumps(data["top_volume"]),
                "tt": json.dumps(data["top_turnover"]),
            },
        )
        conn.commit()
```

- [ ] **Step 2: Write precompute/industry_stats.py**

```python
"""Precompute industry statistics."""

import json
from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.database import execute_sql, engine
from sqlalchemy import text


def _f(v):
    return float(v) if isinstance(v, Decimal) else v


def compute_industry_stats(trade_date: str) -> list[dict]:
    rows = execute_sql(
        """SELECT sb.industry,
                  AVG(dk.pct_chg) AS avg_pct_chg,
                  SUM(dk.amount) AS total_amount,
                  SUM(CASE WHEN dk.pct_chg > 0 THEN 1 ELSE 0 END) AS up_count,
                  SUM(CASE WHEN dk.pct_chg < 0 THEN 1 ELSE 0 END) AS down_count,
                  COALESCE(SUM(mf.net_mf_amount), 0) AS net_mf_amount,
                  COUNT(*) AS stock_count
           FROM daily_kline dk
           JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           LEFT JOIN moneyflow mf ON dk.ts_code = mf.ts_code AND dk.trade_date = mf.trade_date
           WHERE dk.trade_date = :td AND sb.industry IS NOT NULL AND sb.industry != ''
           GROUP BY sb.industry""",
        {"td": trade_date},
    )
    return [{k: _f(v) for k, v in r.items()} for r in rows]


def save_industry_stats(trade_date: str, stats: list[dict]):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM precomputed_industry WHERE trade_date = :td"), {"td": trade_date})
        for s in stats:
            conn.execute(
                text("""INSERT INTO precomputed_industry
                        (trade_date, industry, avg_pct_chg, total_amount, up_count, down_count, net_mf_amount, stock_count)
                        VALUES (:td, :ind, :avg, :amt, :up, :down, :net, :cnt)"""),
                {
                    "td": trade_date,
                    "ind": s["industry"],
                    "avg": s["avg_pct_chg"],
                    "amt": s["total_amount"],
                    "up": int(s["up_count"]),
                    "down": int(s["down_count"]),
                    "net": s["net_mf_amount"],
                    "cnt": int(s["stock_count"]),
                },
            )
        conn.commit()
```

- [ ] **Step 3: Write precompute/limit_analysis.py**

```python
"""Precompute limit-up/limit-down analysis.

Data source: stock_stk_limit (up_limit, down_limit) + daily_kline (close, high, pct_chg, amount).
"""

import json
from decimal import Decimal
from apps.stock_bi_v1.backend.infrastructure.database import execute_sql, engine
from sqlalchemy import text


def _f(v):
    return float(v) if isinstance(v, Decimal) else v


def compute_limit_analysis(trade_date: str) -> dict:
    # Find stocks that hit up limit: close >= up_limit
    up_stocks = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount, sb.industry
           FROM daily_kline dk
           JOIN stock_stk_limit sl ON dk.ts_code = sl.ts_code AND dk.trade_date = sl.trade_date
           JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           WHERE dk.trade_date = :td AND dk.close >= sl.up_limit AND sl.up_limit > 0""",
        {"td": trade_date},
    )

    # Find stocks that hit down limit
    down_stocks = execute_sql(
        """SELECT dk.ts_code, sb.name, dk.pct_chg, dk.close, dk.amount, sb.industry
           FROM daily_kline dk
           JOIN stock_stk_limit sl ON dk.ts_code = sl.ts_code AND dk.trade_date = sl.trade_date
           JOIN stock_basic sb ON dk.ts_code = sb.ts_code
           WHERE dk.trade_date = :td AND dk.close <= sl.down_limit AND sl.down_limit > 0""",
        {"td": trade_date},
    )

    # Broken board: high >= up_limit but close < up_limit
    broken_rows = execute_sql(
        """SELECT COUNT(*) AS cnt
           FROM daily_kline dk
           JOIN stock_stk_limit sl ON dk.ts_code = sl.ts_code AND dk.trade_date = sl.trade_date
           WHERE dk.trade_date = :td AND dk.high >= sl.up_limit AND dk.close < sl.up_limit AND sl.up_limit > 0""",
        {"td": trade_date},
    )
    broken_count = broken_rows[0]["cnt"] if broken_rows else 0

    # Batch-fetch consecutive day data for all up-limit stocks (avoids N+1 queries)
    consec_map = _batch_count_consecutive_limit_days(
        [s["ts_code"] for s in up_stocks], trade_date
    )

    up_limit_stocks = []
    for s in up_stocks:
        up_limit_stocks.append({
            "ts_code": s["ts_code"],
            "name": s["name"],
            "pct_chg": _f(s["pct_chg"]),
            "close": _f(s["close"]),
            "amount": _f(s["amount"]),
            "consecutive_days": consec_map.get(s["ts_code"], 1),
            "industry": s["industry"],
        })

    down_limit_stocks = [{
        "ts_code": s["ts_code"],
        "name": s["name"],
        "pct_chg": _f(s["pct_chg"]),
        "close": _f(s["close"]),
        "amount": _f(s["amount"]),
        "industry": s["industry"],
    } for s in down_stocks]

    up_count = len(up_limit_stocks)
    down_count = len(down_limit_stocks)
    total_touched = up_count + broken_count
    broken_rate = round(broken_count / total_touched * 100, 2) if total_touched > 0 else 0

    # Tier stats
    tier_stats = {}
    for s in up_limit_stocks:
        d = str(s["consecutive_days"])
        tier_stats[d] = tier_stats.get(d, 0) + 1

    return {
        "trade_date": trade_date,
        "up_limit_stocks": up_limit_stocks,
        "down_limit_stocks": down_limit_stocks,
        "up_count": up_count,
        "down_count": down_count,
        "broken_count": broken_count,
        "broken_rate": broken_rate,
        "tier_stats": tier_stats,
    }


def _batch_count_consecutive_limit_days(ts_codes: list[str], trade_date: str) -> dict[str, int]:
    """Batch-count consecutive limit-up days for multiple stocks in a single query.

    Returns {ts_code: consecutive_days}.
    """
    if not ts_codes:
        return {}

    placeholders = ", ".join(f":c{i}" for i in range(len(ts_codes)))
    params = {f"c{i}": code for i, code in enumerate(ts_codes)}
    params["td"] = trade_date

    rows = execute_sql(
        f"""SELECT dk.ts_code, dk.trade_date, dk.close, sl.up_limit
            FROM daily_kline dk
            JOIN stock_stk_limit sl ON dk.ts_code = sl.ts_code AND dk.trade_date = sl.trade_date
            WHERE dk.ts_code IN ({placeholders}) AND dk.trade_date <= :td AND sl.up_limit > 0
            ORDER BY dk.ts_code, dk.trade_date DESC""",
        params,
    )

    # Group by ts_code and count streak from most recent date
    from collections import defaultdict
    by_code = defaultdict(list)
    for r in rows:
        by_code[r["ts_code"]].append(r)

    result = {}
    for code, code_rows in by_code.items():
        count = 0
        for r in code_rows[:30]:  # max 30 days lookback
            if r["close"] >= r["up_limit"]:
                count += 1
            else:
                break
        result[code] = count
    return result


def save_limit_analysis(data: dict):
    td = data["trade_date"]
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM precomputed_limit WHERE trade_date = :td"), {"td": td})
        conn.execute(
            text("""INSERT INTO precomputed_limit
                    (trade_date, up_limit_stocks, down_limit_stocks, up_count, down_count,
                     broken_count, broken_rate, tier_stats)
                    VALUES (:td, :up, :down, :uc, :dc, :bc, :br, :ts)"""),
            {
                "td": td,
                "up": json.dumps(data["up_limit_stocks"]),
                "down": json.dumps(data["down_limit_stocks"]),
                "uc": data["up_count"],
                "dc": data["down_count"],
                "bc": data["broken_count"],
                "br": data["broken_rate"],
                "ts": json.dumps(data["tier_stats"]),
            },
        )
        conn.commit()
```

- [ ] **Step 4: Write precompute/runner.py**

```python
"""Precompute runner — orchestrates all precompute tasks for a given trade date."""

from apps.stock_bi_v1.backend.precompute.market_summary import compute_market_summary, save_market_summary
from apps.stock_bi_v1.backend.precompute.industry_stats import compute_industry_stats, save_industry_stats
from apps.stock_bi_v1.backend.precompute.limit_analysis import compute_limit_analysis, save_limit_analysis
from apps.stock_bi_v1.backend.infrastructure.cache import clear_all_caches


def run_precompute(trade_date: str):
    """Run all precompute tasks for a given trade date."""
    print(f"[precompute] Starting for {trade_date}")

    # 1. Market summary
    market_data = compute_market_summary(trade_date)
    save_market_summary(market_data)
    print(f"[precompute] Market summary done")

    # 2. Industry stats
    industry_data = compute_industry_stats(trade_date)
    save_industry_stats(trade_date, industry_data)
    print(f"[precompute] Industry stats done ({len(industry_data)} industries)")

    # 3. Limit analysis
    limit_data = compute_limit_analysis(trade_date)
    save_limit_analysis(limit_data)
    print(f"[precompute] Limit analysis done (up={limit_data['up_count']}, down={limit_data['down_count']})")

    # Clear caches so next request gets fresh data
    clear_all_caches()
    print(f"[precompute] All done for {trade_date}")
```

- [ ] **Step 5: Add precompute trigger endpoint to main.py**

Add to `main.py` after router registrations:

```python
from fastapi import BackgroundTasks

@app.post("/api/precompute/{trade_date}")
def trigger_precompute(trade_date: str, background_tasks: BackgroundTasks):
    from apps.stock_bi_v1.backend.precompute.runner import run_precompute
    background_tasks.add_task(run_precompute, trade_date)
    return {"status": "started", "trade_date": trade_date}
```

- [ ] **Step 6: Commit**

```bash
git add apps/stock_bi_v1/backend/precompute/ apps/stock_bi_v1/backend/main.py
git commit -m "feat(stock_bi_v1): add precompute pipeline — market, industry, limit analysis"
```

---

### Task 14: Tests for screener and precompute

**Files:**
- Create: `apps/stock_bi_v1/tests/test_screener.py`
- Create: `apps/stock_bi_v1/tests/test_precompute.py`

- [ ] **Step 1: Write test_screener.py**

```python
"""Unit tests for screener — whitelist validation and query construction."""

from apps.stock_bi_v1.backend.modules.screener.service import FIELD_MAP, get_filters, _build_query


def test_filters_returns_metadata():
    filters = get_filters()
    assert len(filters) >= 15
    fields = {f["field"] for f in filters}
    assert "pct_chg" in fields
    assert "pe_ttm" in fields
    assert "net_mf_amount" in fields


def test_field_map_all_whitelisted():
    """Every filter field must be in the FIELD_MAP whitelist."""
    filters = get_filters()
    for f in filters:
        assert f["field"] in FIELD_MAP, f"Filter {f['field']} not in FIELD_MAP"


def test_build_query_ignores_unknown_fields():
    conditions = [{"field": "UNKNOWN_FIELD", "operator": "gt", "value": 5}]
    sql, params, _, _ = _build_query(conditions, "pct_chg", "desc", "20260315")
    # Should not crash, just skip the unknown field
    assert "UNKNOWN_FIELD" not in sql


def test_build_query_between():
    conditions = [{"field": "pe_ttm", "operator": "between", "value": [5.0, 30.0]}]
    sql, params, _, _ = _build_query(conditions, "pct_chg", "desc", "20260315")
    assert "BETWEEN" in sql
    assert params["v0a"] == 5.0
    assert params["v0b"] == 30.0


def test_build_query_excludes_st_by_default():
    conditions = []
    sql, params, _, _ = _build_query(conditions, "pct_chg", "desc", "20260315")
    assert "NOT LIKE" in sql


def test_build_query_includes_st_when_requested():
    conditions = [{"field": "is_st", "operator": "eq", "value": 1}]
    sql, params, _, _ = _build_query(conditions, "pct_chg", "desc", "20260315")
    assert "NOT LIKE" not in sql
    assert "LIKE 'ST%'" in sql
```

- [ ] **Step 2: Write test_precompute.py**

```python
"""Unit tests for precompute logic — test computation without DB."""

from unittest.mock import patch


@patch("apps.stock_bi_v1.backend.precompute.market_summary.execute_sql")
def test_distribution_bins(mock_sql):
    # Side effects for sequential calls: distribution, limit_counts, total_amount, gainers, losers, volume, turnover
    mock_sql.side_effect = [
        [{"pct_chg": 5.0}, {"pct_chg": -2.0}, {"pct_chg": 0.0}, {"pct_chg": 10.0}, {"pct_chg": -8.0}],
        [{"up_limit": 1, "down_limit": 0}],  # limit counts from stock_stk_limit
        [{"total": 1000000}],  # total amount
        [{"ts_code": "000001.SZ", "name": "平安银行", "pct_chg": 10.0, "close": 15.0, "amount": 50000}],
        [{"ts_code": "000002.SZ", "name": "万科A", "pct_chg": -5.0, "close": 10.0, "amount": 30000}],
        [{"ts_code": "000001.SZ", "name": "平安银行", "pct_chg": 10.0, "close": 15.0, "amount": 50000}],
        [{"ts_code": "000001.SZ", "name": "平安银行", "pct_chg": 10.0, "close": 15.0, "turnover_rate": 20.0}],
    ]
    from apps.stock_bi_v1.backend.precompute.market_summary import compute_market_summary
    result = compute_market_summary("20260315")
    assert result["distribution"]["3~5"] == 1
    assert result["distribution"]["-10~-7"] == 1
    assert result["up_limit_count"] == 1
    assert len(result["top_gainers"]) == 1
```

- [ ] **Step 3: Run tests**

```bash
pytest apps/stock_bi_v1/tests/test_screener.py apps/stock_bi_v1/tests/test_precompute.py -v
```

- [ ] **Step 4: Commit**

```bash
git add apps/stock_bi_v1/tests/
git commit -m "test(stock_bi_v1): add screener and precompute unit tests"
```

---

## Chunk 5: Integration & Smoke Tests

### Task 15: API smoke test (all routers respond)

**Files:**
- Create: `apps/stock_bi_v1/tests/test_api_smoke.py`

- [ ] **Step 1: Write test_api_smoke.py**

```python
"""Smoke tests — verify all API routes are registered and respond (no DB required for route check)."""

from fastapi.testclient import TestClient
from apps.stock_bi_v1.backend.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_market_routes_registered():
    """Verify market routes return 200 or 500 (not 404)."""
    routes = [
        "/api/market/overview",
        "/api/market/indices",
        "/api/market/distribution",
        "/api/market/ranking",
        "/api/market/limit-stats",
        "/api/market/limit-list",
    ]
    for route in routes:
        r = client.get(route)
        assert r.status_code != 404, f"Route {route} not registered (got 404)"


def test_industry_routes_registered():
    routes = ["/api/industry/heatmap"]
    for route in routes:
        r = client.get(route)
        assert r.status_code != 404, f"Route {route} not registered"


def test_stock_routes_registered():
    r = client.get("/api/stock/search?q=test")
    assert r.status_code != 404


def test_flow_routes_registered():
    r = client.get("/api/flow/north")
    assert r.status_code != 404


def test_toplist_routes_registered():
    r = client.get("/api/toplist/daily")
    assert r.status_code != 404


def test_screener_routes_registered():
    r = client.get("/api/screener/filters")
    assert r.status_code != 404


def test_precompute_route_registered():
    r = client.post("/api/precompute/20260315")
    assert r.status_code != 404
```

- [ ] **Step 2: Run smoke tests**

```bash
pytest apps/stock_bi_v1/tests/test_api_smoke.py -v
```

Note: Some tests may return 500 (no DB) — that's expected. The key is they don't return 404.

- [ ] **Step 3: Commit**

```bash
git add apps/stock_bi_v1/tests/test_api_smoke.py
git commit -m "test(stock_bi_v1): add API smoke tests for route registration"
```

---

### Task 16: Run all backend tests

- [ ] **Step 1: Run full test suite**

```bash
pytest apps/stock_bi_v1/tests/ -v
```

Expected: All tests PASS (infrastructure, market, industry, screener, precompute, smoke).

- [ ] **Step 2: Verify backend starts (manual check)**

```bash
cd apps/stock_bi_v1 && bash run.sh
# Verify: "Starting Stock BI V1 on 0.0.0.0:8100"
# Verify: http://localhost:8100/health returns {"status": "ok"}
# Ctrl+C to stop
```

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A apps/stock_bi_v1/
git commit -m "fix(stock_bi_v1): address test/startup issues"
```

---

## Summary

| Chunk | Tasks | What it delivers |
|-------|-------|-----------------|
| 1: Foundation | 1-4 | Infrastructure, ORM models, Pydantic schemas, main app, run scripts, infra tests |
| 2: Market & Industry | 5-8 | Market module (overview, ranking, limit), Industry module (heatmap, detail, stocks), tests |
| 3: Stock, Flow, TopList | 9-11 | Stock module (profile, kline, valuation, peers, search), Flow module, TopList module |
| 4: Screener & Precompute | 12-14 | Screener (dynamic SQL, export), Precompute pipeline (3 tasks), tests |
| 5: Integration | 15-16 | API smoke tests, full suite run, startup verification |

**Total: 16 tasks, ~80 steps**

**Frontend plan:** Will be written as a separate plan (`2026-03-15-stock-bi-v1-frontend.md`) after backend is implemented and API endpoints are verified.
