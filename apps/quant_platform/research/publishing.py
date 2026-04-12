from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .strategy.portfolio_backtest import build_trade_constraints

ASSET_BASE_URL = "/research-assets"
SERVING_RELATIVE_DIR = Path("serving/latest")


def _timestamp() -> str:
    return datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _normalize_trade_dates(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values.astype(str), errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


def _safe_scalar(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def _jsonable_row(row: pd.Series) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column, value in row.items():
        serialized = _safe_scalar(value)
        if serialized is not None:
            payload[column] = serialized
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _asset_url(path: Path, output_root: Path) -> str | None:
    if not path.exists():
        return None
    return f"{ASSET_BASE_URL.rstrip('/')}/{path.relative_to(output_root).as_posix()}"


def _resolve_summary_source(output_root: Path, full_research_dir: Path) -> tuple[Path | None, str | None]:
    def _has_rows(path: Path) -> bool:
        if not path.exists():
            return False
        try:
            return not pd.read_csv(path, nrows=1).empty
        except Exception:
            return False

    candidates = [
        (full_research_dir / "qualified_factor_summary.csv", "qualified_factor_summary"),
        (output_root / "qualified_factor_summary.csv", "qualified_factor_summary"),
        (full_research_dir / "split_factor_summary.csv", "split_factor_summary"),
        (output_root / "split_factor_summary.csv", "split_factor_summary"),
        (output_root / "ic_reports" / "factor_ranking.csv", "factor_ranking"),
    ]
    for path, source_name in candidates:
        if _has_rows(path):
            return path, source_name
    for path, source_name in candidates:
        if path.exists():
            return path, source_name
    return None, None


def _pick_metric(row: pd.Series, candidates: tuple[str, ...]) -> float | None:
    for column in candidates:
        if column not in row:
            continue
        value = _safe_scalar(row[column])
        if value is not None:
            return float(value)
    return None


def _resolve_direction(row: pd.Series) -> tuple[int, str | None]:
    for column in ("validation_mean_ic", "train_mean_ic", "test_mean_ic", "mean_ic", "rank_ic"):
        if column not in row:
            continue
        value = _safe_scalar(row[column])
        if value is None or float(value) == 0.0:
            continue
        return (1 if float(value) > 0 else -1), column
    return 1, None


def _discover_factor_assets(output_root: Path, factor_name: str) -> dict[str, Any]:
    asset_patterns = {
        "detail_html": "{factor_name}_detail.html",
        "ic_plot": "{factor_name}_ic.png",
        "layered_plot": "{factor_name}_layered.png",
        "correlation_heatmap": "{factor_name}_correlation.png",
        "ic_series_csv": "{factor_name}_ic_series.csv",
        "group_returns_csv": "{factor_name}_group_returns.csv",
    }
    search_dirs = [
        ("validation", output_root / "full_research" / "validation"),
        ("train", output_root / "full_research" / "train"),
        ("test", output_root / "full_research" / "test"),
        ("ic_reports", output_root / "ic_reports"),
    ]

    assets: dict[str, Any] = {}
    scopes: dict[str, dict[str, str]] = {}
    for scope, directory in search_dirs:
        if not directory.exists():
            continue
        scoped_assets: dict[str, str] = {}
        for key, pattern in asset_patterns.items():
            path = directory / pattern.format(factor_name=factor_name)
            url = _asset_url(path, output_root)
            if url:
                scoped_assets[key] = url
                assets.setdefault(key, url)
        if scoped_assets:
            scopes[scope] = scoped_assets
    if scopes:
        assets["scopes"] = scopes
        assets["preferred_scope"] = next(iter(scopes))
    return assets


def _zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    std = float(numeric.std(ddof=0)) if len(numeric) else 0.0
    if std == 0.0 or np.isnan(std):
        return pd.Series(0.0, index=values.index, dtype=float)
    return ((numeric - numeric.mean()) / std).fillna(0.0)


def _normalize_factor_table(
    summary: pd.DataFrame,
    latest_trade_date: str | None,
    summary_source: str,
) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "factor_name",
                "direction_sign",
                "direction",
                "direction_source",
                "mean_ic",
                "ic_ir",
                "coverage",
                "positive_rate",
                "rolling_1y_valid_ratio",
                "passes_research_gate",
                "latest_trade_date",
                "summary_source",
                "raw_metrics",
            ]
        )

    rows: list[dict[str, Any]] = []
    for _, raw in summary.iterrows():
        factor_name = raw.get("factor_name")
        if not factor_name:
            continue
        direction_sign, direction_source = _resolve_direction(raw)
        normalized = {
            "factor_name": str(factor_name),
            "direction_sign": direction_sign,
            "direction": "long_high" if direction_sign > 0 else "long_low",
            "direction_source": direction_source,
            "mean_ic": _pick_metric(raw, ("validation_mean_ic", "train_mean_ic", "test_mean_ic", "mean_ic")),
            "ic_ir": _pick_metric(raw, ("validation_ic_ir", "train_ic_ir", "test_ic_ir", "ic_ir")),
            "coverage": _pick_metric(raw, ("validation_coverage", "train_coverage", "test_coverage", "coverage")),
            "positive_rate": _pick_metric(
                raw,
                ("validation_positive_rate", "train_positive_rate", "test_positive_rate", "positive_rate"),
            ),
            "rolling_1y_valid_ratio": _pick_metric(
                raw,
                (
                    "validation_rolling_1y_valid_ratio",
                    "train_rolling_1y_valid_ratio",
                    "test_rolling_1y_valid_ratio",
                    "rolling_1y_valid_ratio",
                ),
            ),
            "passes_research_gate": bool(
                raw.get("passes_research_gate", raw.get("train_validation_consistent", False))
            ),
            "latest_trade_date": latest_trade_date,
            "summary_source": summary_source,
            "raw_metrics": _jsonable_row(raw),
        }
        rows.append(normalized)

    normalized_frame = pd.DataFrame(rows)
    if normalized_frame.empty:
        return normalized_frame
    if "ic_ir" in normalized_frame.columns:
        normalized_frame = normalized_frame.sort_values(
            by=["passes_research_gate", "ic_ir"],
            ascending=[False, False],
            na_position="last",
        ).reset_index(drop=True)
    return normalized_frame


def _latest_panel_slice(panel: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    if panel.empty or "trade_date" not in panel.columns:
        return panel.copy(), None
    working = panel.copy()
    working["trade_date"] = _normalize_trade_dates(working["trade_date"])
    working = working.dropna(subset=["trade_date"])
    if working.empty:
        return working, None
    latest_trade_date = working["trade_date"].max()
    latest = working.loc[working["trade_date"] == latest_trade_date].copy()
    return latest, latest_trade_date


def _load_latest_panel_slice_from_csv(panel_path: Path, chunksize: int = 50000) -> tuple[pd.DataFrame, str | None]:
    if not panel_path.exists():
        return pd.DataFrame(), None

    latest_trade_date: str | None = None
    for chunk in pd.read_csv(panel_path, usecols=["trade_date"], chunksize=chunksize):
        normalized = _normalize_trade_dates(chunk["trade_date"])
        chunk_latest = normalized.dropna().max()
        if chunk_latest is not None and (latest_trade_date is None or chunk_latest > latest_trade_date):
            latest_trade_date = str(chunk_latest)

    if latest_trade_date is None:
        return pd.DataFrame(), None

    latest_chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(panel_path, chunksize=chunksize):
        normalized = _normalize_trade_dates(chunk["trade_date"])
        filtered = chunk.loc[normalized == latest_trade_date].copy()
        if not filtered.empty:
            filtered["trade_date"] = latest_trade_date
            latest_chunks.append(filtered)

    if not latest_chunks:
        return pd.DataFrame(), latest_trade_date
    return pd.concat(latest_chunks, ignore_index=True), latest_trade_date


def _build_factor_detail(
    factor_row: pd.Series,
    latest_panel: pd.DataFrame,
    latest_trade_date: str | None,
    output_root: Path,
    picks_limit: int,
) -> dict[str, Any]:
    factor_name = factor_row["factor_name"]
    detail = {
        "factor_name": factor_name,
        "summary": _jsonable_row(factor_row.drop(labels=["raw_metrics"])),
        "raw_metrics": factor_row.get("raw_metrics", {}),
        "latest_trade_date": latest_trade_date,
        "assets": _discover_factor_assets(output_root, factor_name),
        "distribution": {
            "universe_size": 0,
            "tradable_count": 0,
        },
        "industry_breakdown": [],
        "picks": [],
    }
    if latest_panel.empty or factor_name not in latest_panel.columns:
        return detail

    scored = latest_panel.loc[:, [column for column in latest_panel.columns if column != "raw_metrics"]].copy()
    scored = scored.loc[scored[factor_name].notna()].copy()
    if scored.empty:
        return detail

    scored["zscore"] = _zscore(scored[factor_name])
    scored["signal_score"] = scored["zscore"] * int(factor_row["direction_sign"])
    scored["signal_rank_pct"] = scored["signal_score"].rank(method="average", pct=True)
    scored["tradable"] = (
        scored.get("can_buy", pd.Series(True, index=scored.index)).fillna(False).astype(bool)
        & ~scored.get("is_suspended", pd.Series(False, index=scored.index)).fillna(False).astype(bool)
    )
    ranked = scored.sort_values(["tradable", "signal_score"], ascending=[False, False]).reset_index(drop=True)

    tradable = ranked.loc[ranked["tradable"]].copy()
    picks = tradable.head(picks_limit).copy()
    picks["rank"] = range(1, len(picks) + 1)
    picks["factor_value"] = pd.to_numeric(picks[factor_name], errors="coerce")
    picks["confidence"] = picks["signal_rank_pct"].clip(lower=0.0, upper=1.0)
    picks["signal_hint"] = "高值更优" if int(factor_row["direction_sign"]) > 0 else "低值更优"

    detail["distribution"] = {
        "universe_size": int(len(ranked)),
        "tradable_count": int(len(tradable)),
        "mean": _safe_scalar(ranked["signal_score"].mean()),
        "std": _safe_scalar(ranked["signal_score"].std(ddof=0)),
        "min": _safe_scalar(ranked["signal_score"].min()),
        "median": _safe_scalar(ranked["signal_score"].median()),
        "max": _safe_scalar(ranked["signal_score"].max()),
    }
    if "industry" in ranked.columns:
        industry_summary = (
            ranked.assign(industry=ranked["industry"].fillna("未知"))
            .groupby("industry", dropna=False)
            .agg(
                stock_count=("ts_code", "size"),
                tradable_count=("tradable", "sum"),
                avg_signal_score=("signal_score", "mean"),
                avg_factor_value=(factor_name, "mean"),
            )
            .sort_values(["stock_count", "avg_signal_score"], ascending=[False, False])
            .head(10)
            .reset_index()
        )
        detail["industry_breakdown"] = json.loads(industry_summary.to_json(orient="records", force_ascii=False))

    pick_columns = [
        "rank",
        "trade_date",
        "ts_code",
        "industry",
        "close",
        "pct_chg",
        "factor_value",
        "zscore",
        "signal_score",
        "signal_rank_pct",
        "confidence",
        "signal_hint",
        "can_buy",
        "can_sell",
        "is_suspended",
        "tradable",
    ]
    pick_payload = picks.loc[:, [column for column in pick_columns if column in picks.columns]].copy()
    detail["picks"] = json.loads(pick_payload.to_json(orient="records", force_ascii=False))
    return detail


def publish_research_snapshot(
    *,
    output_root: str | Path,
    full_research_dir: str | Path | None = None,
    publish_dir: str | Path | None = None,
    picks_limit: int = 20,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root)
    resolved_full_research_dir = Path(full_research_dir) if full_research_dir is not None else resolved_output_root / "full_research"
    resolved_publish_dir = Path(publish_dir) if publish_dir is not None else resolved_output_root / SERVING_RELATIVE_DIR

    summary_path, summary_source = _resolve_summary_source(resolved_output_root, resolved_full_research_dir)
    panel_path = resolved_full_research_dir / "full_factor_panel.csv"
    latest_panel, latest_trade_date = _load_latest_panel_slice_from_csv(panel_path)
    if not latest_panel.empty:
        latest_panel = latest_panel.merge(
            build_trade_constraints(latest_panel),
            on=["trade_date", "ts_code"],
            how="left",
        )

    summary = pd.read_csv(summary_path) if summary_path is not None and summary_path.exists() else pd.DataFrame()
    factor_table = _normalize_factor_table(summary, latest_trade_date, summary_source or "unknown")
    factor_details: list[dict[str, Any]] = []

    for _, row in factor_table.iterrows():
        detail = _build_factor_detail(
            row,
            latest_panel=latest_panel,
            latest_trade_date=latest_trade_date,
            output_root=resolved_output_root,
            picks_limit=picks_limit,
        )
        factor_details.append(detail)
        _write_json(resolved_publish_dir / "factor_details" / f"{row['factor_name']}.json", detail)

    factors_payload = {
        "available": not factor_table.empty,
        "row_count": int(len(factor_table)),
        "latest_trade_date": latest_trade_date,
        "supports_picks": bool(panel_path.exists()),
        "rows": json.loads(
            factor_table.drop(columns=["raw_metrics"], errors="ignore").to_json(orient="records", force_ascii=False)
        ) if not factor_table.empty else [],
    }
    manifest = {
        "available": not factor_table.empty,
        "published_at": _timestamp(),
        "latest_trade_date": latest_trade_date,
        "factor_count": int(len(factor_table)),
        "qualified_factor_count": int(factor_table["passes_research_gate"].fillna(False).sum()) if not factor_table.empty else 0,
        "supports_picks": bool(panel_path.exists()),
        "summary_source": summary_source,
        "paths": {
            "summary_path": summary_path.relative_to(resolved_output_root).as_posix() if summary_path is not None and summary_path.exists() else None,
            "panel_path": panel_path.relative_to(resolved_output_root).as_posix() if panel_path.exists() else None,
            "factors_path": (resolved_publish_dir / "factors.json").relative_to(resolved_output_root).as_posix(),
        },
    }

    _write_json(resolved_publish_dir / "manifest.json", manifest)
    _write_json(resolved_publish_dir / "factors.json", factors_payload)
    return manifest
