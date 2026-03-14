from ...infrastructure.database import engine
from .application import (
    build_industry_stocks_payload,
    build_kline_rows,
    build_moneyflow_payload,
    build_ranking_enhanced_payload,
    build_search_results,
)
from .repository import RankingKlineRepository


repository = RankingKlineRepository(engine=engine)


def build_kline_response(repository: RankingKlineRepository, ts_code: str, limit: int) -> list:
    return build_kline_rows(repository.load_kline_rows(ts_code, limit))


def build_search_response(repository: RankingKlineRepository, keyword: str, limit: int) -> list:
    rows = repository.load_search_rows(keyword, limit)
    if not rows:
        rows = repository.load_fallback_search_rows(keyword, limit)
    return build_search_results(rows)


def build_ranking_enhanced_response(
    repository: RankingKlineRepository,
    trade_date: str,
    sort_by: str,
    order: str,
    market,
    industry,
    top: int,
) -> dict:
    rows = repository.load_ranking_enhanced_rows(trade_date, sort_by, order, market, industry, top)
    return build_ranking_enhanced_payload(
        trade_date,
        rows,
        sort_by=sort_by,
        order=order,
        market=market,
        industry=industry,
    )


def build_industry_stocks_response(
    repository: RankingKlineRepository,
    industry: str,
    trade_date: str,
    order: str,
    limit: int,
) -> dict:
    rows = repository.load_industry_stocks_rows(industry, trade_date, order, limit)
    return build_industry_stocks_payload(trade_date, industry, order, rows)


def build_moneyflow_response(repository: RankingKlineRepository, ts_code: str, trade_date: str) -> dict:
    row = repository.load_moneyflow_row(ts_code, trade_date)
    return build_moneyflow_payload(ts_code, trade_date, row)


def get_kline(ts_code: str, limit: int) -> list:
    return build_kline_response(repository, ts_code, limit)


def search_stocks(keyword: str, limit: int) -> list:
    return build_search_response(repository, keyword, limit)


def get_ranking_enhanced(trade_date: str, sort_by: str, order: str, market, industry, top: int) -> dict:
    return build_ranking_enhanced_response(repository, trade_date, sort_by, order, market, industry, top)


def get_industry_stocks(industry: str, trade_date: str, order: str, limit: int) -> dict:
    return build_industry_stocks_response(repository, industry, trade_date, order, limit)


def get_moneyflow(ts_code: str, trade_date: str) -> dict:
    return build_moneyflow_response(repository, ts_code, trade_date)
