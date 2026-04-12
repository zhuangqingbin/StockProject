import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.quant_platform.app.api import research as research_api
from apps.quant_platform.app.services import research_snapshot_service


def _seed_research_sources(research_root: Path) -> None:
    full_research = research_root / "output" / "full_research"
    full_research.mkdir(parents=True)

    panel = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "ts_code": "000001.SZ",
                "industry": "Bank",
                "open": 10.0,
                "close": 10.2,
                "pct_chg": 1.0,
                "alpha_quality": 0.8,
                "beta_reversal": -0.4,
                "limit_up_price": 11.0,
                "limit_down_price": 9.0,
            },
            {
                "trade_date": "2026-01-02",
                "ts_code": "000002.SZ",
                "industry": "Broker",
                "open": 12.0,
                "close": 11.8,
                "pct_chg": -1.2,
                "alpha_quality": 0.2,
                "beta_reversal": -1.0,
                "limit_up_price": 13.2,
                "limit_down_price": 10.8,
            },
            {
                "trade_date": "2026-01-03",
                "ts_code": "000001.SZ",
                "industry": "Bank",
                "open": 10.2,
                "close": 10.5,
                "pct_chg": 2.1,
                "alpha_quality": 0.9,
                "beta_reversal": -0.2,
                "limit_up_price": 11.5,
                "limit_down_price": 9.5,
            },
            {
                "trade_date": "2026-01-03",
                "ts_code": "000002.SZ",
                "industry": "Broker",
                "open": 12.1,
                "close": 12.1,
                "pct_chg": 2.5,
                "alpha_quality": 0.1,
                "beta_reversal": -1.5,
                "limit_up_price": 12.1,
                "limit_down_price": 10.9,
            },
        ]
    )
    panel.to_csv(full_research / "full_factor_panel.csv", index=False)

    pd.DataFrame(
        [
            {
                "factor_name": "alpha_quality",
                "train_mean_ic": 0.03,
                "validation_mean_ic": 0.02,
                "train_ic_ir": 0.8,
                "validation_ic_ir": 0.6,
                "train_coverage": 0.92,
                "validation_coverage": 0.88,
                "validation_positive_rate": 0.61,
                "validation_rolling_1y_valid_ratio": 0.83,
                "passes_research_gate": True,
            },
            {
                "factor_name": "beta_reversal",
                "train_mean_ic": -0.04,
                "validation_mean_ic": -0.03,
                "train_ic_ir": 0.72,
                "validation_ic_ir": 0.51,
                "train_coverage": 0.9,
                "validation_coverage": 0.85,
                "validation_positive_rate": 0.42,
                "validation_rolling_1y_valid_ratio": 0.79,
                "passes_research_gate": True,
            },
        ]
    ).to_csv(full_research / "qualified_factor_summary.csv", index=False)

    validation_dir = full_research / "validation"
    validation_dir.mkdir(parents=True)
    (validation_dir / "alpha_quality_detail.html").write_text("<html>alpha</html>", encoding="utf-8")
    (validation_dir / "alpha_quality_ic.png").write_bytes(b"png")


def test_research_snapshot_service_publishes_and_exposes_factor_picks(tmp_path):
    research_root = tmp_path / "research"
    _seed_research_sources(research_root)

    manifest = research_snapshot_service.get_research_snapshot_manifest(base_dir=research_root)
    factors = research_snapshot_service.list_research_factors(base_dir=research_root, qualified_only=True)
    detail = research_snapshot_service.get_research_factor_detail("alpha_quality", base_dir=research_root)
    stock_detail = research_snapshot_service.get_research_factor_stock_detail(
        "alpha_quality",
        "000001.SZ",
        base_dir=research_root,
        history_window=5,
    )

    assert manifest["available"] is True
    assert manifest["factor_count"] == 2
    assert factors["row_count"] == 2
    assert factors["rows"][0]["factor_name"] == "alpha_quality"
    assert detail["picks"][0]["ts_code"] == "000001.SZ"
    assert detail["picks"][0]["tradable"] is True
    assert detail["assets"]["detail_html"] == "/research-assets/full_research/validation/alpha_quality_detail.html"
    assert stock_detail["history_window"] == 2
    assert stock_detail["history"][-1]["signal_rank_pct"] >= 0.5


def test_research_factor_routes_return_snapshot_payloads(tmp_path, monkeypatch):
    research_root = tmp_path / "research"
    _seed_research_sources(research_root)
    monkeypatch.setattr(research_snapshot_service, "RESEARCH_ROOT", research_root)

    async def fake_stock_profiles(ts_codes):
        return {
            code: {
                "stock_name": f"name-{code}",
                "industry": "Bank" if code == "000001.SZ" else "Broker",
                "market": "SZ",
                "symbol": code.split(".")[0],
            }
            for code in ts_codes
        }

    monkeypatch.setattr(research_api, "_stock_profile_map", fake_stock_profiles)

    app = FastAPI()
    app.include_router(research_api.router)
    client = TestClient(app)

    factors_response = client.get("/api/research/factors", params={"qualified_only": True})
    detail_response = client.get("/api/research/factors/alpha_quality")
    stock_response = client.get("/api/research/factors/alpha_quality/stocks/000001.SZ")

    assert factors_response.status_code == 200
    assert factors_response.json()["data"]["rows"][0]["factor_name"] == "alpha_quality"

    detail_payload = detail_response.json()["data"]
    assert detail_payload["picks"][0]["stock_name"] == "name-000001.SZ"
    assert detail_payload["picks"][0]["ts_code"] == "000001.SZ"

    stock_payload = stock_response.json()["data"]
    assert stock_payload["stock_profile"]["stock_name"] == "name-000001.SZ"
    assert stock_payload["history"][-1]["trade_date"] == "2026-01-03"
