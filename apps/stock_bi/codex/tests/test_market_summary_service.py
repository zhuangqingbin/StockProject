from apps.stock_bi.codex.backend.modules.market_summary.repository import MarketSummaryQueryRepository
from apps.stock_bi.codex.backend.modules.market_summary.service import (
    build_amount_trend_response,
    build_industries_enhanced_response,
    build_limit_trend_response,
    build_north_money_trend_response,
    build_sectors_enhanced_response,
    build_top_list_response,
)


class FakeRepository:
    def __init__(
        self,
        north_trend_rows=None,
        top_list_rows=None,
        amount_rows=None,
        limit_rows=None,
        sectors_rows=None,
        industries_rows=None,
    ):
        self.north_trend_rows = north_trend_rows or []
        self.top_list_rows = top_list_rows or []
        self.amount_rows = amount_rows or []
        self.limit_rows = limit_rows or []
        self.sectors_rows = sectors_rows or []
        self.industries_rows = industries_rows or []
        self.calls = []

    def load_north_money_trend_rows(self, days):
        self.calls.append(("north_trend", days))
        return self.north_trend_rows

    def load_top_list_rows(self, trade_date, limit):
        self.calls.append(("top_list", trade_date, limit))
        return self.top_list_rows

    def load_amount_trend_rows(self, days):
        self.calls.append(("amount_trend", days))
        return self.amount_rows

    def load_limit_trend_rows(self, days):
        self.calls.append(("limit_trend", days))
        return self.limit_rows

    def load_sectors_enhanced_rows(self, trade_date):
        self.calls.append(("sectors_enhanced", trade_date))
        return self.sectors_rows

    def load_industries_enhanced_rows(self, trade_date, top, order):
        self.calls.append(("industries_enhanced", trade_date, top, order))
        return self.industries_rows


class FakeResult:
    def __init__(self, many=None):
        self.many = many

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


def test_build_north_money_trend_response_uses_repository_rows():
    repository = FakeRepository(
        north_trend_rows=[("20250314", 10.1, 6.2, 3.9), ("20250313", 8.8, 5.1, 3.7)]
    )

    result = build_north_money_trend_response(repository, 30)

    assert repository.calls == [("north_trend", 30)]
    assert result[0]["trade_date"] == "2025-03-13"
    assert result[1]["north_total"] == 10.1


def test_build_top_list_response_uses_repository_rows():
    repository = FakeRepository(
        top_list_rows=[("000001.SZ", "平安银行", 1.2, 10.0, 8.0, 2.0, "日涨幅偏离值达7%")]
    )

    result = build_top_list_response(repository, "20250314", 20)

    assert repository.calls == [("top_list", "20250314", 20)]
    assert result[0]["name"] == "平安银行"
    assert result[0]["net"] == 2.0


def test_build_amount_and_limit_trend_responses_use_repository_rows():
    repository = FakeRepository(
        amount_rows=[("20250314", 8.8)],
        limit_rows=[("20250314", 10, 1)],
    )

    amount = build_amount_trend_response(repository, 30)
    limit = build_limit_trend_response(repository, 30)

    assert repository.calls == [("amount_trend", 30), ("limit_trend", 30)]
    assert amount[0]["total_amount"] == 8.8
    assert limit[0]["limit_up"] == 10


def test_build_sectors_and_industries_responses_use_repository_rows():
    repository = FakeRepository(
        sectors_rows=[("科创板", 1.2, 8.8, 4, 3, 1, 0, 1, 0)],
        industries_rows=[("半导体", 1.2, 10.1, 4, 3, 1)],
    )

    sectors = build_sectors_enhanced_response(repository, "20250314", 10, "all")
    industries = build_industries_enhanced_response(repository, "20250314", 15, "desc")

    assert repository.calls == [
        ("sectors_enhanced", "20250314"),
        ("industries_enhanced", "20250314", 15, "desc"),
    ]
    assert sectors["sectors"][0]["sector"] == "科创板"
    assert industries["industries"][0]["name"] == "半导体"


def test_repository_load_north_money_trend_rows_uses_days_limit():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = MarketSummaryQueryRepository(engine=FakeEngine(connection))

    rows = repository.load_north_money_trend_rows(30)

    assert rows == [("row",)]
    assert "FROM moneyflow_hsgt" in connection.executed[0][0]
    assert connection.executed[0][1] == {"days": 30}


def test_repository_load_top_list_rows_uses_trade_date_and_limit():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = MarketSummaryQueryRepository(engine=FakeEngine(connection))

    rows = repository.load_top_list_rows("20250314", 20)

    assert rows == [("row",)]
    assert "FROM top_list" in connection.executed[0][0]
    assert connection.executed[0][1] == {"trade_date": "20250314", "limit": 20}


def test_repository_load_industries_enhanced_rows_preserves_sort_direction():
    connection = FakeConnection([FakeResult(many=[("row",)])])
    repository = MarketSummaryQueryRepository(engine=FakeEngine(connection))

    repository.load_industries_enhanced_rows("20250314", 15, "asc")

    assert "ORDER BY avg_pct_chg ASC" in connection.executed[0][0]
    assert connection.executed[0][1] == {"trade_date": "20250314", "limit": 15}
