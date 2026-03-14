from apps.stock_bi.codex.backend.modules.ranking_kline.repository import RankingKlineRepository
from apps.stock_bi.codex.backend.modules.ranking_kline.service import (
    build_kline_response,
    build_ranking_enhanced_response,
    build_search_response,
    build_industry_stocks_response,
    build_moneyflow_response,
)


class FakeRepository:
    def __init__(
        self,
        kline_rows=None,
        search_rows=None,
        fallback_search_rows=None,
        ranking_rows=None,
        industry_rows=None,
        moneyflow_row=None,
    ):
        self.kline_rows = kline_rows or []
        self.search_rows = search_rows or []
        self.fallback_search_rows = fallback_search_rows or []
        self.ranking_rows = ranking_rows or []
        self.industry_rows = industry_rows or []
        self.moneyflow_row = moneyflow_row
        self.calls = []

    def load_kline_rows(self, ts_code, limit):
        self.calls.append(("kline", ts_code, limit))
        return self.kline_rows

    def load_search_rows(self, keyword, limit):
        self.calls.append(("search", keyword, limit))
        return self.search_rows

    def load_fallback_search_rows(self, keyword, limit):
        self.calls.append(("search_fallback", keyword, limit))
        return self.fallback_search_rows

    def load_ranking_enhanced_rows(self, trade_date, sort_by, order, market, industry, top):
        self.calls.append(("ranking_enhanced", trade_date, sort_by, order, market, industry, top))
        return self.ranking_rows

    def load_industry_stocks_rows(self, industry, trade_date, order, limit):
        self.calls.append(("industry_stocks", industry, trade_date, order, limit))
        return self.industry_rows

    def load_moneyflow_row(self, ts_code, trade_date):
        self.calls.append(("moneyflow", ts_code, trade_date))
        return self.moneyflow_row


class FakeResult:
    def __init__(self, one=None, many=None):
        self.one = one
        self.many = many

    def fetchone(self):
        return self.one

    def fetchall(self):
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

    def connect(self):
        return self.connection


def test_build_industry_stocks_response_uses_repository_rows():
    repository = FakeRepository(
        industry_rows=[
            ("000001.SZ", None, 1.2, 10.5, 10.0, 10.8, 9.8, 12.3, 88.8, 3.1, 8.1, 0.9, 100.0)
        ]
    )

    result = build_industry_stocks_response(repository, "银行", "20250314", "desc", 100)

    assert repository.calls == [("industry_stocks", "银行", "20250314", "desc", 100)]
    assert result["industry"] == "银行"
    assert result["up_count"] == 1
    assert result["stocks"][0]["name"] == "000001"


def test_build_kline_response_uses_repository_rows():
    repository = FakeRepository(
        kline_rows=[
            ("000001.SZ", "20250314", 10, 11, 9, 10.5, 1.2, 1000, 2000),
            ("000001.SZ", "20250313", 9, 10, 8.5, 9.8, -0.1, 900, 1800),
        ]
    )

    result = build_kline_response(repository, "000001.SZ", 60)

    assert repository.calls == [("kline", "000001.SZ", 60)]
    assert result[0]["date"] == "2025-03-13"
    assert result[1]["close"] == 10.5


def test_build_search_response_falls_back_when_primary_search_returns_no_rows():
    repository = FakeRepository(
        search_rows=[],
        fallback_search_rows=[("000001.SZ", "000001.SZ")],
    )

    result = build_search_response(repository, "000001", 20)

    assert repository.calls == [("search", "000001", 20), ("search_fallback", "000001", 20)]
    assert result == [{"ts_code": "000001.SZ", "name": "000001.SZ"}]


def test_build_ranking_enhanced_response_uses_repository_rows():
    repository = FakeRepository(
        ranking_rows=[("000001.SZ", None, 1.2, 10.5, 88.8, 120000, 3.1, "银行", 8.1, 0.9)]
    )

    result = build_ranking_enhanced_response(repository, "20250314", "pct_chg", "desc", "科创板", "银行", 20)

    assert repository.calls == [("ranking_enhanced", "20250314", "pct_chg", "desc", "科创板", "银行", 20)]
    assert result["sort_by"] == "pct_chg"
    assert result["stocks"][0]["name"] == "000001"


def test_build_moneyflow_response_uses_repository_row():
    repository = FakeRepository(
        moneyflow_row=(
            "000001.SZ", "20250314",
            1, 10, 2, 5,
            3, 20, 4, 6,
            5, 30, 6, 7,
            7, 40, 8, 8,
            9, 99,
        )
    )

    result = build_moneyflow_response(repository, "000001.SZ", "20250314")

    assert repository.calls == [("moneyflow", "000001.SZ", "20250314")]
    assert result["trade_date"] == "2025-03-14"
    assert result["small"]["net_amount"] == 5.0


def test_repository_load_industry_stocks_rows_preserves_desc_sorting():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    rows = repository.load_industry_stocks_rows("银行", "20250314", "desc", 20)

    assert rows == [("row",)]
    assert "ORDER BY k.pct_chg DESC" in connection.executed[0][0]
    assert connection.executed[0][1] == {"trade_date": "20250314", "industry": "银行", "limit": 20}


def test_repository_load_industry_stocks_rows_uses_asc_for_non_desc_orders():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    repository.load_industry_stocks_rows("银行", "20250314", "asc", 20)

    assert "ORDER BY k.pct_chg ASC" in connection.executed[0][0]


def test_repository_load_moneyflow_row_fetches_single_row():
    connection = FakeConnection([FakeResult(one=("row",))])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    row = repository.load_moneyflow_row("000001.SZ", "20250314")

    assert row == ("row",)
    assert "FROM moneyflow" in connection.executed[0][0]
    assert connection.executed[0][1] == {"ts_code": "000001.SZ", "trade_date": "20250314"}


def test_repository_load_kline_rows_applies_ts_code_and_limit():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    rows = repository.load_kline_rows("000001.SZ", 60)

    assert rows == [("row",)]
    assert "FROM daily_kline" in connection.executed[0][0]
    assert connection.executed[0][1] == {"ts_code": "000001.SZ", "limit": 60}


def test_repository_load_search_rows_and_fallback_rows_use_keyword_limit():
    connection = FakeConnection([FakeResult(many=[("row1",)]), FakeResult(many=[("row2",)])])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    primary = repository.load_search_rows("000001", 20)
    fallback = repository.load_fallback_search_rows("000001", 20)

    assert primary == [("row1",)]
    assert fallback == [("row2",)]
    assert "FROM stock_basic" in connection.executed[0][0]
    assert "FROM daily_kline" in connection.executed[1][0]
    assert connection.executed[0][1] == {"keyword": "%000001%", "limit": 20}
    assert connection.executed[1][1] == {"keyword": "%000001%", "limit": 20}


def test_repository_load_ranking_enhanced_rows_uses_sort_and_filters():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = RankingKlineRepository(engine=FakeEngine(connection))

    rows = repository.load_ranking_enhanced_rows("20250314", "turnover", "asc", "科创板", "银行", 20)

    assert rows == [("row",)]
    sql, params = connection.executed[0]
    assert "ORDER BY db.turnover_rate ASC" in sql
    assert "k.ts_code LIKE '68%'" in sql
    assert "b.industry = :industry" in sql
    assert params == {"trade_date": "20250314", "limit": 20, "industry": "银行"}
