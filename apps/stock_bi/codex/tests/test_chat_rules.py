import asyncio

from apps.stock_bi.codex.backend.modules.chat_query.application import resolve_intent
from apps.stock_bi.codex.backend.modules.chat_query.llm_service import LLMService


def test_rule_based_parser_handles_overview_query():
    service = LLMService()

    result = service._rule_based_parse("今天市场怎么样")

    assert result["action"] == "overview"
    assert result["params"] == {}


def test_rule_based_parser_extracts_market_and_limit():
    service = LLMService()

    result = service._rule_based_parse("显示科创板涨幅前10的股票")

    assert result["action"] == "ranking"
    assert result["params"]["market"] == "科创板"
    assert result["params"]["limit"] == 10


def test_rule_based_parser_keeps_kline_suffix_and_default_reply():
    service = LLMService()

    kline = service._rule_based_parse("查看 600000 K线")
    fallback = service._rule_based_parse("随便聊聊")

    assert kline["params"]["ts_code"] == "600000.SH"
    assert "您可以尝试以下指令" in fallback["reply"]


def test_chat_application_delegates_to_llm_service():
    result = asyncio.run(resolve_intent("成交额趋势"))

    assert result["action"] == "amount_trend"
