from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from apps.quant_platform.research.publishing import SERVING_RELATIVE_DIR, publish_research_snapshot
from apps.quant_platform.research.strategy.portfolio_backtest import build_trade_constraints

from .research_service import OUTPUT_ROOT, RESEARCH_ROOT


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _serving_dir(research_root: Path) -> Path:
    return research_root / "output" / SERVING_RELATIVE_DIR


def _output_root(research_root: Path) -> Path:
    return research_root / "output"


def _full_panel_path(research_root: Path) -> Path:
    return _output_root(research_root) / "full_research" / "full_factor_panel.csv"


def _manifest_path(research_root: Path) -> Path:
    return _serving_dir(research_root) / "manifest.json"


def _candidate_source_paths(output_root: Path) -> list[Path]:
    return [
        output_root / "full_research" / "full_factor_panel.csv",
        output_root / "full_research" / "qualified_factor_summary.csv",
        output_root / "full_research" / "split_factor_summary.csv",
        output_root / "qualified_factor_summary.csv",
        output_root / "split_factor_summary.csv",
        output_root / "ic_reports" / "factor_ranking.csv",
    ]


def _needs_publish(research_root: Path) -> bool:
    output_root = _output_root(research_root)
    sources = [path for path in _candidate_source_paths(output_root) if path.exists()]
    if not sources:
        return False
    manifest = _manifest_path(research_root)
    if not manifest.exists():
        return True
    manifest_mtime = manifest.stat().st_mtime_ns
    return any(path.stat().st_mtime_ns > manifest_mtime for path in sources)


def ensure_research_snapshot(base_dir: Path | str | None = None) -> dict[str, Any]:
    research_root = Path(base_dir) if base_dir is not None else RESEARCH_ROOT
    if _needs_publish(research_root):
        publish_research_snapshot(output_root=_output_root(research_root))
    manifest = _read_json(_manifest_path(research_root))
    return manifest or {"available": False, "factor_count": 0, "supports_picks": False}


def get_research_snapshot_manifest(base_dir: Path | str | None = None) -> dict[str, Any]:
    return ensure_research_snapshot(base_dir=base_dir)


def list_research_factors(
    *,
    limit: int | None = None,
    qualified_only: bool = False,
    base_dir: Path | str | None = None,
) -> dict[str, Any]:
    research_root = Path(base_dir) if base_dir is not None else RESEARCH_ROOT
    manifest = ensure_research_snapshot(research_root)
    payload = _read_json(_serving_dir(research_root) / "factors.json")
    rows = list((payload or {}).get("rows", []))
    if qualified_only:
        rows = [row for row in rows if row.get("passes_research_gate")]
    if limit is not None:
        rows = rows[:limit]
    return {
        "available": bool(payload and payload.get("available")),
        "row_count": len(rows),
        "latest_trade_date": (payload or {}).get("latest_trade_date", manifest.get("latest_trade_date")),
        "supports_picks": manifest.get("supports_picks", False),
        "rows": rows,
    }


def get_research_factor_detail(
    factor_name: str,
    *,
    base_dir: Path | str | None = None,
) -> dict[str, Any] | None:
    research_root = Path(base_dir) if base_dir is not None else RESEARCH_ROOT
    ensure_research_snapshot(research_root)
    return _read_json(_serving_dir(research_root) / "factor_details" / f"{factor_name}.json")


def get_research_factor_picks(
    factor_name: str,
    *,
    limit: int = 20,
    base_dir: Path | str | None = None,
) -> dict[str, Any] | None:
    detail = get_research_factor_detail(factor_name, base_dir=base_dir)
    if detail is None:
        return None
    rows = list(detail.get("picks", []))[:limit]
    return {
        "factor_name": factor_name,
        "latest_trade_date": detail.get("latest_trade_date"),
        "row_count": len(rows),
        "rows": rows,
    }


def _normalize_trade_dates(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values.astype(str), errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


@lru_cache(maxsize=2)
def _load_panel_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(path_str)


def _load_panel(research_root: Path) -> pd.DataFrame:
    panel_path = _full_panel_path(research_root)
    if not panel_path.exists():
        return pd.DataFrame()
    return _load_panel_cached(str(panel_path), panel_path.stat().st_mtime_ns).copy()


def _group_zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    std = float(numeric.std(ddof=0)) if len(numeric) else 0.0
    if std == 0.0 or np.isnan(std):
        return pd.Series(0.0, index=values.index, dtype=float)
    return ((numeric - numeric.mean()) / std).fillna(0.0)


def get_research_factor_stock_detail(
    factor_name: str,
    ts_code: str,
    *,
    history_window: int = 120,
    base_dir: Path | str | None = None,
) -> dict[str, Any] | None:
    research_root = Path(base_dir) if base_dir is not None else RESEARCH_ROOT
    detail = get_research_factor_detail(factor_name, base_dir=research_root)
    if detail is None:
        return None

    panel = _load_panel(research_root)
    if panel.empty or factor_name not in panel.columns or "ts_code" not in panel.columns:
        return None

    panel["trade_date"] = _normalize_trade_dates(panel["trade_date"])
    panel = panel.dropna(subset=["trade_date"])
    stock_history = panel.loc[panel["ts_code"] == ts_code].copy()
    if stock_history.empty:
        return None

    stock_history = stock_history.sort_values("trade_date").tail(history_window).copy()
    relevant_dates = stock_history["trade_date"].unique().tolist()
    cross_section = panel.loc[panel["trade_date"].isin(relevant_dates), ["trade_date", "ts_code", factor_name]].copy()
    cross_section = cross_section.loc[cross_section[factor_name].notna()].copy()
    if cross_section.empty:
        return None

    cross_section["factor_zscore"] = cross_section.groupby("trade_date", sort=False)[factor_name].transform(_group_zscore)
    cross_section["factor_rank_pct"] = cross_section.groupby("trade_date", sort=False)[factor_name].rank(method="average", pct=True)
    direction_sign = int(detail.get("summary", {}).get("direction_sign", 1))
    cross_section["signal_rank_pct"] = (
        cross_section["factor_rank_pct"]
        if direction_sign > 0
        else 1.0 - cross_section["factor_rank_pct"]
    )

    stock_history = stock_history.merge(
        cross_section.loc[:, ["trade_date", "ts_code", factor_name, "factor_zscore", "factor_rank_pct", "signal_rank_pct"]],
        on=["trade_date", "ts_code", factor_name],
        how="left",
    )
    stock_history = stock_history.merge(
        build_trade_constraints(stock_history),
        on=["trade_date", "ts_code"],
        how="left",
    )
    stock_history["tradable"] = (
        stock_history.get("can_buy", pd.Series(True, index=stock_history.index)).fillna(False).astype(bool)
        & ~stock_history.get("is_suspended", pd.Series(False, index=stock_history.index)).fillna(False).astype(bool)
    )
    stock_history["factor_value"] = pd.to_numeric(stock_history[factor_name], errors="coerce")
    records = json.loads(
        stock_history.loc[
            :,
            [
                column
                for column in [
                    "trade_date",
                    "ts_code",
                    "industry",
                    "close",
                    "pct_chg",
                    "factor_value",
                    "factor_zscore",
                    "factor_rank_pct",
                    "signal_rank_pct",
                    "can_buy",
                    "can_sell",
                    "is_suspended",
                    "tradable",
                ]
                if column in stock_history.columns
            ],
        ].to_json(orient="records", force_ascii=False)
    )
    latest_pick = next((pick for pick in detail.get("picks", []) if pick.get("ts_code") == ts_code), None)
    latest_record = records[-1] if records else {}

    return {
        "factor_name": factor_name,
        "ts_code": ts_code,
        "latest_trade_date": detail.get("latest_trade_date"),
        "latest_pick": latest_pick,
        "history_window": len(records),
        "direction": detail.get("summary", {}).get("direction"),
        "history": records,
        "latest_metrics": {
            "factor_value": latest_record.get("factor_value"),
            "factor_zscore": latest_record.get("factor_zscore"),
            "signal_rank_pct": latest_record.get("signal_rank_pct"),
            "tradable": latest_record.get("tradable"),
        },
    }
