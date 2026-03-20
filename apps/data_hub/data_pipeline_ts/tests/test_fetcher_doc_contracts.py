from __future__ import annotations

import inspect
import re
from pathlib import Path

from apps.data_hub.data_pipeline_ts.fetchers import FETCHER_REGISTRY
from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher
from apps.data_hub.data_pipeline_ts.fetchers.infrastructure import (
    StockBasicFetch,
    StockCompanyFetch,
    TradeCalFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.reference_data.stock_pledge_detail import PledgeDetailFetch
from apps.data_hub.data_pipeline_ts.fetchers.basic_data.stock_st import StockStFetch


TUSHARE_REFERENCE_ROOT = Path("/Users/qingbin.zhuang/.agents/skills/tushare/references")
DOC_API_ALIASES = {
    "balancesheet_vip": "balancesheet",
    "cashflow_vip": "cashflow",
    "express_vip": "express",
    "fina_indicator_vip": "fina_indicator",
    "forecast_vip": "forecast",
    "income_vip": "income",
}
QFQ_FETCHER_NAMES = {
    "StockDailyQfqFetch",
}
DOC_FIELD_SUFFIXES = {
    "HMListFetch": ("snapshot_date",),
    "PledgeDetailFetch": ("snapshot_date",),
}


def _normalize_doc_api(raw_value: str) -> str:
    return raw_value.split("，", 1)[0].split(",", 1)[0].strip().strip("`")


def _build_tushare_doc_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in TUSHARE_REFERENCE_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^接口：\s*([^\n]+)", text, re.M)
        if match is None:
            continue
        index[_normalize_doc_api(match.group(1))] = path
    return index


def _extract_output_fields(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    section_match = re.search(r"(?:\*\*输出参数\*\*|### 输出参数)\s*(.*?)(?:\n\s*(?:\*\*|### )|\Z)", text, re.S)
    assert section_match is not None, f"missing output parameter section in {path}"

    fields: list[str] = []
    in_table = False
    for raw_line in section_match.group(1).splitlines():
        line = raw_line.strip()
        if not line:
            if in_table and fields:
                break
            continue
        if line.startswith("名称 | 类型") or line.startswith("名称|类型"):
            in_table = True
            continue
        if not in_table:
            continue
        if set(line) <= {"-", "|", " "}:
            continue
        if "|" not in line:
            break
        field_name = raw_line.split("|", 1)[0].strip()
        if field_name and field_name not in {"名称", "---"}:
            fields.append(field_name)
    return fields


def _resolve_fetcher_doc_api(fetcher_cls: type[BaseFetcher]) -> str:
    if fetcher_cls is PledgeDetailFetch:
        return "pledge_detail"
    if fetcher_cls is StockStFetch:
        return "stock_st"
    if fetcher_cls.__name__ in QFQ_FETCHER_NAMES:
        return "daily"

    source = inspect.getsource(fetcher_cls)
    calls = re.findall(r'self\.client\.call\(\s*"([^"]+)"', source)
    assert calls, f"missing client.call endpoint in {fetcher_cls.__name__}"
    return DOC_API_ALIASES.get(calls[-1], calls[-1])


def _all_tushare_fetchers() -> list[type[BaseFetcher]]:
    return [*FETCHER_REGISTRY.values(), StockBasicFetch, StockCompanyFetch, TradeCalFetch]


def test_stock_st_fetch_matches_current_tushare_contract():
    assert StockStFetch.fields == [
        "ts_code",
        "name",
        "trade_date",
        "type",
        "type_name",
    ]


def test_new_financial_fetchers_are_covered_by_tushare_doc_contracts():
    assert "DividendFetch" in FETCHER_REGISTRY
    assert "FinaAuditFetch" in FETCHER_REGISTRY


def test_new_money_flow_fetcher_is_covered_by_tushare_doc_contracts():
    assert "MoneyFlowMktDCFetch" in FETCHER_REGISTRY


def test_new_stock_market_fetchers_are_covered_by_tushare_doc_contracts():
    assert "StockSuspendDFetch" in FETCHER_REGISTRY
    assert "StockDailyQfqFetch" in FETCHER_REGISTRY
    assert "StockWeeklyFetch" not in FETCHER_REGISTRY
    assert "StockMonthlyFetch" not in FETCHER_REGISTRY
    assert "StockWeeklyQfqFetch" not in FETCHER_REGISTRY
    assert "StockMonthlyQfqFetch" not in FETCHER_REGISTRY


def test_new_special_data_fetchers_are_covered_by_tushare_doc_contracts():
    for fetcher_name in [
        "ReportRCFetch",
        "CyqPerfFetch",
        "CyqChipsFetch",
        "StkFactorProFetch",
        "CcassHoldFetch",
        "HKHoldFetch",
        "StkAHComparisonFetch",
        "StkSurvFetch",
    ]:
        assert fetcher_name in FETCHER_REGISTRY

    assert "StkAuctionOFetch" not in FETCHER_REGISTRY
    assert "StkAuctionCFetch" not in FETCHER_REGISTRY


def test_all_fetcher_fields_match_tushare_reference_outputs():
    doc_index = _build_tushare_doc_index()

    for fetcher_cls in _all_tushare_fetchers():
        doc_api = _resolve_fetcher_doc_api(fetcher_cls)
        assert doc_api in doc_index, f"missing Tushare reference for {fetcher_cls.__name__}: {doc_api}"

        expected_fields = _extract_output_fields(doc_index[doc_api])
        expected_fields.extend(DOC_FIELD_SUFFIXES.get(fetcher_cls.__name__, ()))

        assert fetcher_cls.fields == expected_fields
