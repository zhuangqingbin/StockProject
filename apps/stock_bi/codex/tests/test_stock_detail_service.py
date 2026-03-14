from apps.stock_bi.codex.backend.modules.stock_detail.repository import (
    CompanyInfoRows,
    IndustryDetailRows,
    StockDetailRows,
    StockDetailRepository,
)
from apps.stock_bi.codex.backend.modules.stock_detail.service import (
    build_company_info_response,
    build_industry_detail_response,
    build_stock_detail_response,
)


class FakeRepository:
    def __init__(self, stock_rows=None, company_rows=None, industry_rows=None):
        self.stock_rows = stock_rows
        self.company_rows = company_rows
        self.industry_rows = industry_rows
        self.calls = []

    def load_stock_detail_rows(self, ts_code, trade_date):
        self.calls.append(("stock", ts_code, trade_date))
        return self.stock_rows

    def load_company_info_rows(self, ts_code):
        self.calls.append(("company", ts_code))
        return self.company_rows

    def load_industry_detail_rows(self, industry, trade_date, kline_limit):
        self.calls.append(("industry", industry, trade_date, kline_limit))
        return self.industry_rows


class FakeResult:
    def __init__(self, one=None, many=None, error=None):
        self.one = one
        self.many = many
        self.error = error

    def fetchone(self):
        if self.error:
            raise self.error
        return self.one

    def fetchall(self):
        if self.error:
            raise self.error
        return self.many or []


class FakeConnection:
    def __init__(self, results):
        self.results = iter(results)
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((str(sql), params))
        return next(self.results)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection
        self.connect_calls = 0

    def connect(self):
        self.connect_calls += 1
        return self.connection


def test_build_stock_detail_response_uses_repository_rows():
    repository = FakeRepository(
        stock_rows=StockDetailRows(
            daily_row=("000001.SZ", "20250314", 10, 11, 9, 10.5, 9.8, 2.1, 1000, 2000, "平安银行"),
            basic_row=("000001.SZ", "20250314", 3.2, 8.1, 8.0, 0.9, 100000, 80000, 1.5),
            kline_rows=[("20250314", 10, 11, 9, 10.5, 1000, 2000, 2.1)],
            company_row=("000001.SZ", "平安银行", "深圳", "银行", "主板", "19910403"),
        )
    )

    result = build_stock_detail_response(repository, "000001.SZ", "20250314")

    assert repository.calls == [("stock", "000001.SZ", "20250314")]
    assert result["daily"]["name"] == "平安银行"
    assert result["basic"]["total_mv"] == 10.0


def test_build_company_info_response_returns_none_when_stock_missing():
    repository = FakeRepository(company_rows=CompanyInfoRows(base_row=None, detail_row=None))

    result = build_company_info_response(repository, "000001.SZ")

    assert repository.calls == [("company", "000001.SZ")]
    assert result is None


def test_build_industry_detail_response_uses_sw_index_then_stats():
    repository = FakeRepository(
        industry_rows=IndustryDetailRows(
            index_row=("801010.SI", "半导体I"),
            sw_kline_rows=[("20250314", 10, 11, 9, 10.5, 2000, 50000, 1.2)],
            sw_today_row=(10, 11, 9, 10.5, 1.2, 2000, 50000, 15, 2),
            aggregate_kline_rows=[],
            stats_row=(20, 12, 6, 1.23, 88.8),
        )
    )

    result = build_industry_detail_response(repository, "半导体", "20250314", 60)

    assert repository.calls == [("industry", "半导体", "20250314", 60)]
    assert result["index_code"] == "801010.SI"
    assert result["index_name"] == "半导体I"
    assert result["today"]["pe"] == 15.0
    assert result["stats"]["stock_count"] == 20


def test_build_industry_detail_response_falls_back_to_aggregate_kline():
    repository = FakeRepository(
        industry_rows=IndustryDetailRows(
            index_row=("801010.SI", "半导体I"),
            sw_kline_rows=[],
            sw_today_row=None,
            aggregate_kline_rows=[("20250314", 10, 11, 9, 10.5, 200000, 500000000, 1.2)],
            stats_row=(20, 12, 6, 1.23, 88.8),
        )
    )

    result = build_industry_detail_response(repository, "半导体", "20250314", 60)

    assert result["index_code"] == "801010.SI"
    assert result["index_name"] == "半导体(聚合)"
    assert result["kline"][0]["amount"] == 5.0
    assert result["today"] is None


def test_repository_load_stock_detail_rows_reuses_one_connection():
    connection = FakeConnection(
        [
            FakeResult(one=("daily",)),
            FakeResult(one=("basic",)),
            FakeResult(many=[("kline",)]),
            FakeResult(one=("company",)),
        ]
    )
    repository = StockDetailRepository(engine=FakeEngine(connection))

    rows = repository.load_stock_detail_rows("000001.SZ", "20250314")

    assert rows.daily_row == ("daily",)
    assert rows.basic_row == ("basic",)
    assert rows.kline_rows == [("kline",)]
    assert rows.company_row == ("company",)
    assert len(connection.executed) == 4
    assert connection.executed[0][1] == {"ts_code": "000001.SZ", "trade_date": "20250314"}


def test_repository_load_company_info_rows_queries_base_then_detail():
    connection = FakeConnection(
        [
            FakeResult(one=("base",)),
            FakeResult(one=("detail",)),
        ]
    )
    repository = StockDetailRepository(engine=FakeEngine(connection))

    rows = repository.load_company_info_rows("000001.SZ")

    assert rows.base_row == ("base",)
    assert rows.detail_row == ("detail",)
    assert len(connection.executed) == 2
    assert "FROM stock_basic" in connection.executed[0][0]
    assert "FROM stock_company" in connection.executed[1][0]


def test_repository_load_industry_detail_rows_falls_back_after_sw_lookup_failure():
    connection = FakeConnection(
        [
            FakeResult(error=RuntimeError("sw failed")),
            FakeResult(many=[("agg",)]),
            FakeResult(one=("stats",)),
        ]
    )
    repository = StockDetailRepository(engine=FakeEngine(connection))

    rows = repository.load_industry_detail_rows("半导体", "20250314", 60)

    assert rows.index_row is None
    assert rows.sw_kline_rows == []
    assert rows.aggregate_kline_rows == [("agg",)]
    assert rows.stats_row == ("stats",)
    assert len(connection.executed) == 3
