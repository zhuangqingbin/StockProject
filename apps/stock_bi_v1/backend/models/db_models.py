from sqlalchemy import Column, Float, Integer, JSON, String, Text

from apps.stock_bi_v1.backend.infrastructure.database import Base


class DailyKline(Base):
    __tablename__ = "daily_kline"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    open = Column(Float, default=0.0)
    high = Column(Float, default=0.0)
    low = Column(Float, default=0.0)
    close = Column(Float, default=0.0)
    pre_close = Column(Float, default=0.0)
    change = Column(Float, default=0.0)
    pct_chg = Column(Float, default=0.0)
    vol = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)


class DailyBasic(Base):
    __tablename__ = "daily_basic"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    turnover_rate = Column(Float, default=0.0)
    pe_ttm = Column(Float, default=0.0)
    pb = Column(Float, default=0.0)
    ps_ttm = Column(Float, default=0.0)
    total_mv = Column(Float, default=0.0)
    circ_mv = Column(Float, default=0.0)
    total_share = Column(Float, default=0.0)
    float_share = Column(Float, default=0.0)


class Moneyflow(Base):
    __tablename__ = "moneyflow"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    buy_elg_amount = Column(Float, default=0.0)
    sell_elg_amount = Column(Float, default=0.0)
    buy_lg_amount = Column(Float, default=0.0)
    sell_lg_amount = Column(Float, default=0.0)
    buy_md_amount = Column(Float, default=0.0)
    sell_md_amount = Column(Float, default=0.0)
    buy_sm_amount = Column(Float, default=0.0)
    sell_sm_amount = Column(Float, default=0.0)
    net_mf_amount = Column(Float, default=0.0)


class MoneyflowHsgt(Base):
    __tablename__ = "moneyflow_hsgt"

    trade_date = Column(String(8), primary_key=True)
    hgt = Column(Float, default=0.0)
    sgt = Column(Float, default=0.0)
    north_money = Column(Float, default=0.0)
    south_money = Column(Float, default=0.0)


class IndexDaily(Base):
    __tablename__ = "index_daily"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    close = Column(Float, default=0.0)
    pct_chg = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)


class TopList(Base):
    __tablename__ = "top_list"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    name = Column(String(64), default="")
    close = Column(Float, default=0.0)
    pct_chg = Column("pct_change", Float, default=0.0)
    turnover_rate = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    l_buy = Column(Float, default=0.0)
    l_sell = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    reason = Column(Text, default="")


class StockBasic(Base):
    __tablename__ = "stock_basic"

    ts_code = Column(String(12), primary_key=True)
    symbol = Column(String(12), default="")
    name = Column(String(64), default="")
    area = Column(String(64), default="")
    industry = Column(String(64), default="")
    market = Column(String(32), default="")
    exchange = Column(String(32), default="")
    is_hs = Column(String(8), default="")
    list_date = Column(String(8), default="")


class StockStkLimit(Base):
    __tablename__ = "stock_stk_limit"

    ts_code = Column(String(12), primary_key=True)
    trade_date = Column(String(8), primary_key=True)
    pre_close = Column(Float, default=0.0)
    up_limit = Column(Float, default=0.0)
    down_limit = Column(Float, default=0.0)


class PrecomputedMarket(Base):
    __tablename__ = "precomputed_market"

    trade_date = Column(String(8), primary_key=True)
    distribution = Column(JSON, default=dict)
    up_limit_count = Column(Integer, default=0)
    down_limit_count = Column(Integer, default=0)
    flat_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    top_gainers = Column(JSON, default=list)
    top_losers = Column(JSON, default=list)
    top_amount = Column(JSON, default=list)
    top_turnover = Column(JSON, default=list)


class PrecomputedIndustry(Base):
    __tablename__ = "precomputed_industry"

    trade_date = Column(String(8), primary_key=True)
    industry = Column(String(64), primary_key=True)
    avg_pct_chg = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    up_count = Column(Integer, default=0)
    down_count = Column(Integer, default=0)
    net_mf_amount = Column(Float, default=0.0)
    stock_count = Column(Integer, default=0)


class PrecomputedLimit(Base):
    __tablename__ = "precomputed_limit"

    trade_date = Column(String(8), primary_key=True)
    up_limit_stocks = Column(JSON, default=list)
    down_limit_stocks = Column(JSON, default=list)
    up_count = Column(Integer, default=0)
    down_count = Column(Integer, default=0)
    broken_count = Column(Integer, default=0)
    broken_rate = Column(Float, default=0.0)
    tier_stats = Column(JSON, default=dict)
