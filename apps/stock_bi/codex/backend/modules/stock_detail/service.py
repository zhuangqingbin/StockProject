from ...infrastructure.database import engine
from .application import (
    build_aggregate_industry_kline_rows,
    build_company_info_payload,
    build_industry_base_payload,
    build_industry_stats_payload,
    build_stock_detail_payload,
    build_sw_industry_kline_rows,
    build_sw_industry_today_payload,
)
from .repository import StockDetailRepository


repository = StockDetailRepository(engine=engine)


def build_stock_detail_response(repository: StockDetailRepository, ts_code: str, trade_date: str) -> dict:
    rows = repository.load_stock_detail_rows(ts_code, trade_date)
    return build_stock_detail_payload(
        ts_code,
        trade_date,
        rows.daily_row,
        rows.basic_row,
        rows.kline_rows,
        rows.company_row,
    )


def build_company_info_response(repository: StockDetailRepository, ts_code: str):
    rows = repository.load_company_info_rows(ts_code)
    if not rows.base_row:
        return None
    return build_company_info_payload(rows.base_row, rows.detail_row)


def build_industry_detail_response(
    repository: StockDetailRepository,
    industry: str,
    trade_date: str,
    kline_limit: int,
) -> dict:
    rows = repository.load_industry_detail_rows(industry, trade_date, kline_limit)
    result = build_industry_base_payload(industry, trade_date)

    if rows.index_row:
        result["index_code"] = rows.index_row[0]
        result["index_name"] = rows.index_row[1]

    if rows.sw_kline_rows:
        result["kline"] = build_sw_industry_kline_rows(rows.sw_kline_rows)
        result["today"] = build_sw_industry_today_payload(rows.sw_today_row)
    elif rows.aggregate_kline_rows:
        result["index_name"] = f"{industry}(聚合)"
        result["kline"] = build_aggregate_industry_kline_rows(rows.aggregate_kline_rows)

    result["stats"] = build_industry_stats_payload(rows.stats_row)
    return result


def get_stock_detail(ts_code: str, trade_date: str) -> dict:
    return build_stock_detail_response(repository, ts_code, trade_date)


def get_company_info(ts_code: str):
    return build_company_info_response(repository, ts_code)


def get_industry_detail(industry: str, trade_date: str, kline_limit: int) -> dict:
    return build_industry_detail_response(repository, industry, trade_date, kline_limit)
