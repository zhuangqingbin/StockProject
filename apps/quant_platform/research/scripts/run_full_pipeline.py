"""
Full overnight-return prediction pipeline.

Loads all available data, builds 100+ factors, ranks them by IC/ICIR,
constructs composite factors with multiple methods, runs portfolio backtests,
and outputs a strategy comparison report.

Usage:
    python -m apps.quant_platform.research.scripts.run_full_pipeline \
        --start-date 2020-01-01 --end-date 2025-12-31
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from apps.quant_platform.research.config import ResearchConfig
from apps.quant_platform.research.data_loader import ResearchDataLoader, build_forward_overnight_returns
from apps.quant_platform.research.factor_engine.base import (
    generate_time_series_features,
    run_standard_factor_pipeline,
)
from apps.quant_platform.research.factor_engine.technical import TechnicalFactorBuilder
from apps.quant_platform.research.factor_engine.money_flow import MoneyFlowFactorBuilder
from apps.quant_platform.research.factor_engine.northbound import NorthboundFactorBuilder
from apps.quant_platform.research.factor_engine.margin import MarginFactorBuilder
from apps.quant_platform.research.factor_engine.chip import ChipFactorBuilder
from apps.quant_platform.research.factor_engine.fundamental import FundamentalFactorBuilder
from apps.quant_platform.research.factor_engine.event import EventFactorBuilder
from apps.quant_platform.research.factor_engine.dragon import DragonFactorBuilder
from apps.quant_platform.research.factor_engine.ownership import OwnershipFactorBuilder
from apps.quant_platform.research.factor_engine.industry import IndustryFactorBuilder
from apps.quant_platform.research.factor_engine.market import MarketFactorBuilder
from apps.quant_platform.research.factor_engine.cross_feature import CrossFeatureBuilder
from apps.quant_platform.research.factor_engine.composite import CompositeFactorBuilder
from apps.quant_platform.research.analyzer.report import ResearchReportBuilder
from apps.quant_platform.research.analyzer.ic_analysis import analyze_factor_ic, apply_fdr_correction
from apps.quant_platform.research.analyzer.layered_backtest import analyze_layered_returns
from apps.quant_platform.research.strategy.signal_generator import TopPercentSignalGenerator
from apps.quant_platform.research.strategy.portfolio_backtest import PortfolioBacktestEngine, PortfolioBacktestConfig
from apps.quant_platform.research.strategy.exit_rules import ExitRuleEngine, ExitRuleConfig
from apps.quant_platform.research.strategy.factor_strategy import FactorStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── columns to load from the main panel ──────────────────────────────────────
PANEL_COLUMNS = [
    "ts_code", "trade_date",
    "open", "open_qfq", "high_qfq", "low_qfq", "close", "close_qfq",
    "pre_close", "pct_chg", "vol", "amount",
    "turnover_rate", "turnover_rate_f", "volume_ratio",
    "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm",
    "total_share", "float_share", "free_share", "total_mv", "circ_mv",
    # MAs
    "ma_qfq_5", "ma_qfq_10", "ma_qfq_20", "ma_qfq_30", "ma_qfq_60", "ma_qfq_90", "ma_qfq_250",
    "ema_qfq_5", "ema_qfq_10", "ema_qfq_20", "ema_qfq_30", "ema_qfq_60", "ema_qfq_90",
    # technical indicators (qfq only)
    "macd_qfq", "macd_dif_qfq", "macd_dea_qfq",
    "kdj_k_qfq", "kdj_d_qfq", "kdj_qfq",
    "rsi_qfq_6", "rsi_qfq_12", "rsi_qfq_24",
    "boll_upper_qfq", "boll_mid_qfq", "boll_lower_qfq",
    "atr_qfq", "cci_qfq", "mfi_qfq", "obv_qfq",
    "wr_qfq", "wr1_qfq",
    "bias1_qfq", "bias2_qfq", "bias3_qfq",
    "psy_qfq", "psyma_qfq",
    "roc_qfq", "maroc_qfq",
    "trix_qfq", "trma_qfq",
    "dmi_pdi_qfq", "dmi_mdi_qfq", "dmi_adx_qfq", "dmi_adxr_qfq",
    "cr_qfq", "vr_qfq", "emv_qfq",
    "updays", "downdays", "topdays", "lowdays",
]

# ── auxiliary source columns ─────────────────────────────────────────────────
MONEY_FLOW_COLS = [
    "ts_code", "trade_date",
    "buy_sm_amount", "sell_sm_amount",
    "buy_md_amount", "sell_md_amount",
    "buy_lg_amount", "sell_lg_amount",
    "buy_elg_amount", "sell_elg_amount",
    "net_mf_amount",
]
MONEY_FLOW_DC_COLS = [
    "ts_code", "trade_date",
    "buy_sm_amount_rate", "buy_elg_amount_rate",
    "net_amount", "net_amount_rate",
]
HK_HOLD_COLS = ["ts_code", "trade_date", "ratio", "vol"]
CCASS_HOLD_COLS = ["ts_code", "trade_date", "hold_ratio", "hold_nums"]
MARGIN_DETAIL_COLS = ["ts_code", "trade_date", "rzye", "rqye", "rzmre"]


def _step(label: str) -> float:
    log.info("▸ %s", label)
    return time.time()


def _done(t0: float) -> None:
    log.info("  done (%.1fs)", time.time() - t0)


# ── 1. LOAD DATA ─────────────────────────────────────────────────────────────

def load_all_data(loader: ResearchDataLoader, start_date: str, end_date: str | None) -> dict[str, pd.DataFrame]:
    t = _step("Loading panel data (stock_stk_factor_pro)")
    panel = loader.load_panel(start_date=start_date, end_date=end_date, columns=PANEL_COLUMNS)
    log.info("  panel: %d rows, %d stocks, %d dates", len(panel), panel["ts_code"].nunique(), panel["trade_date"].nunique())
    _done(t)

    sources: dict[str, pd.DataFrame] = {"panel": panel}

    for name, cols in [
        ("money_flow", MONEY_FLOW_COLS),
        ("money_flow_dc", MONEY_FLOW_DC_COLS),
        ("hk_hold", HK_HOLD_COLS),
        ("ccass_hold", CCASS_HOLD_COLS),
        ("margin_detail", MARGIN_DETAIL_COLS),
    ]:
        t = _step(f"Loading {name}")
        try:
            sources[name] = loader.load_named_source(name, start_date=start_date, end_date=end_date, columns=cols)
            log.info("  %s: %d rows", name, len(sources[name]))
        except Exception as exc:
            log.warning("  %s unavailable: %s", name, exc)
            sources[name] = pd.DataFrame()
        _done(t)

    return sources


# ── 2. BUILD ALL FACTORS ─────────────────────────────────────────────────────

def build_all_factors(sources: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[str]]:
    panel = sources["panel"].copy()

    # prepare overnight return target
    t = _step("Building forward overnight returns")
    panel = build_forward_overnight_returns(panel, open_col="open", close_col="close")
    _done(t)

    # track which columns are factors (everything added beyond the original panel)
    base_cols = set(panel.columns)

    # Technical factors
    t = _step("Building technical factors")
    try:
        panel = TechnicalFactorBuilder().build(panel)
    except ValueError as exc:
        log.warning("  TechnicalFactorBuilder skipped: %s", exc)
    _done(t)

    # Derived technical factors from raw indicators
    t = _step("Building derived technical factors")
    panel["boll_bandwidth"] = (panel.get("boll_upper_qfq", 0) - panel.get("boll_lower_qfq", 0)) / panel.get("boll_mid_qfq", pd.Series(dtype=float)).replace(0, np.nan)
    panel["boll_position"] = (panel["close_qfq"] - panel.get("boll_lower_qfq", 0)) / (panel.get("boll_upper_qfq", 0) - panel.get("boll_lower_qfq", 0)).replace(0, np.nan)
    panel["kdj_cross"] = panel.get("kdj_k_qfq", 0) - panel.get("kdj_d_qfq", 0)
    panel["dmi_trend_strength"] = panel.get("dmi_pdi_qfq", 0) - panel.get("dmi_mdi_qfq", 0)
    panel["macd_histogram_accel"] = panel.groupby("ts_code", sort=False)["macd_qfq"].diff()
    panel["close_to_ma5"] = panel["close_qfq"] / panel.get("ma_qfq_5", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["close_to_ma10"] = panel["close_qfq"] / panel.get("ma_qfq_10", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["close_to_ma60"] = panel["close_qfq"] / panel.get("ma_qfq_60", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["close_to_ma250"] = panel["close_qfq"] / panel.get("ma_qfq_250", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["ma5_ma20_cross"] = panel.get("ma_qfq_5", 0) / panel.get("ma_qfq_20", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["ma20_ma60_cross"] = panel.get("ma_qfq_20", 0) / panel.get("ma_qfq_60", pd.Series(dtype=float)).replace(0, np.nan) - 1
    panel["rsi_divergence"] = panel.get("rsi_qfq_6", 50) - panel.get("rsi_qfq_24", 50)
    panel["intraday_amplitude"] = (panel["high_qfq"] - panel["low_qfq"]) / panel["close_qfq"].replace(0, np.nan)
    panel["upper_shadow"] = (panel["high_qfq"] - panel[["open_qfq", "close_qfq"]].max(axis=1)) / panel["close_qfq"].replace(0, np.nan)
    panel["lower_shadow"] = (panel[["open_qfq", "close_qfq"]].min(axis=1) - panel["low_qfq"]) / panel["close_qfq"].replace(0, np.nan)
    panel["body_ratio"] = (panel["close_qfq"] - panel["open_qfq"]).abs() / (panel["high_qfq"] - panel["low_qfq"]).replace(0, np.nan)
    panel["gap_open"] = (panel["open_qfq"] - panel["pre_close"]) / panel["pre_close"].replace(0, np.nan)
    # Volume/price divergence
    panel["vol_price_corr_sign"] = np.sign(panel["pct_chg"]) * np.sign(panel["vol"] - panel.groupby("ts_code", sort=False)["vol"].shift(1))
    # Valuation factors
    panel["ep_ratio"] = 1 / panel["pe_ttm"].replace(0, np.nan)
    panel["bp_ratio"] = 1 / panel["pb"].replace(0, np.nan)
    panel["sp_ratio"] = 1 / panel["ps_ttm"].replace(0, np.nan)
    panel["dv_yield_premium"] = panel.get("dv_ttm", 0)
    panel["size_log"] = np.log(panel["total_mv"].replace(0, np.nan))
    panel["free_float_ratio"] = panel.get("free_share", 0) / panel.get("total_share", pd.Series(dtype=float)).replace(0, np.nan)
    _done(t)

    # Each factor builder is wrapped to prevent one failure from aborting the run
    def _safe_build(label, fn):
        t = _step(label)
        try:
            result = fn()
            _done(t)
            return result
        except Exception as exc:
            log.warning("  %s failed: %s", label, exc)
            _done(t)
            return panel

    panel = _safe_build("Building money flow factors", lambda: MoneyFlowFactorBuilder().build(
        panel, money_flow=sources.get("money_flow"), money_flow_dc=sources.get("money_flow_dc"),
    ))

    panel = _safe_build("Building northbound factors", lambda: NorthboundFactorBuilder().build(
        panel, hk_hold=sources.get("hk_hold"), ccass_hold=sources.get("ccass_hold"),
    ))

    panel = _safe_build("Building margin factors", lambda: MarginFactorBuilder().build(
        panel, margin_detail=sources.get("margin_detail"),
    ))

    panel = _safe_build("Building chip factors", lambda: ChipFactorBuilder().build(panel))

    panel = _safe_build("Building cross-feature factors", lambda: CrossFeatureBuilder().build(panel))

    # Collect factor columns (everything new beyond base)
    factor_cols = sorted(set(panel.columns) - base_cols - {"overnight_return"})
    log.info("  Total raw factors: %d", len(factor_cols))

    # Time-series features on the most important raw factors
    t = _step("Generating time-series features")
    ts_factor_cols = [
        c for c in [
            "pct_chg", "turnover_rate_f", "volume_ratio",
            "net_mf_rate", "elg_net_ratio",
            "hk_hold_chg", "rzmre_intensity",
            "atr_pct", "ma_spread_5_20",
        ] if c in panel.columns
    ]
    if ts_factor_cols:
        panel = generate_time_series_features(panel, factor_cols=ts_factor_cols, windows=[3, 5, 10, 20])
    _done(t)

    # Final factor list
    all_factor_cols = sorted(set(panel.columns) - base_cols - {"overnight_return"})
    log.info("  Total factors (incl. time-series): %d", len(all_factor_cols))

    return panel, all_factor_cols


# ── 3. SCREEN FACTORS BY IC ─────────────────────────────────────────────────

def screen_factors(
    panel: pd.DataFrame,
    factor_cols: list[str],
    target_col: str = "overnight_return",
    min_abs_ic: float = 0.01,
    max_factors: int = 80,
) -> tuple[pd.DataFrame, list[str]]:
    t = _step(f"Screening {len(factor_cols)} factors by IC")
    records: list[dict] = []
    for factor in factor_cols:
        valid_count = panel[factor].notna().sum()
        if valid_count < 100:
            continue
        ic_result = analyze_factor_ic(panel, factor_col=factor, target_col=target_col, include_decay=False)
        layered = analyze_layered_returns(panel, factor_col=factor, target_col=target_col, n_groups=5)
        records.append({
            "factor": factor,
            "mean_ic": ic_result["mean_ic"],
            "rank_ic": ic_result["rank_ic"],
            "ic_ir": ic_result["ic_ir"],
            "positive_rate": ic_result["positive_rate"],
            "t_stat": ic_result["t_stat"],
            "p_value": ic_result["p_value"],
            "long_short_mean": layered.get("long_short_returns", pd.Series(dtype=float)).mean(),
            "monotonicity": layered.get("monotonicity", 0.0),
            "coverage": valid_count / len(panel),
        })

    ranking = pd.DataFrame(records).sort_values("ic_ir", key=abs, ascending=False).reset_index(drop=True)
    ranking = apply_fdr_correction(ranking)

    # Filter: significant IC, reasonable coverage
    significant = ranking[
        (ranking["ic_ir"].abs() >= min_abs_ic) &
        (ranking["coverage"] >= 0.3)
    ].head(max_factors)

    selected_factors = significant["factor"].tolist()
    log.info("  Kept %d / %d factors (top by |IC_IR|)", len(selected_factors), len(records))
    _done(t)

    return ranking, selected_factors


# ── 4. BUILD STRATEGIES ─────────────────────────────────────────────────────

STRATEGY_CONFIGS = [
    # (name, composite_method, top_pct, hold_pct, max_holdings, weighting, exit_config)
    ("equal_top5pct_20hold", "equal_weight", 0.05, 0.15, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("equal_top10pct_20hold", "equal_weight", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("equal_top10pct_50hold", "equal_weight", 0.10, 0.30, 50, "equal", ExitRuleConfig(max_holding_days=15)),
    ("icw_top5pct_20hold", "ic_weighted", 0.05, 0.15, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("icw_top10pct_20hold", "ic_weighted", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("icirw_top5pct_20hold", "icir_weighted", 0.05, 0.15, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("icirw_top10pct_20hold", "icir_weighted", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("pca_top10pct_20hold", "pca", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("ml_top5pct_20hold", "ml", 0.05, 0.15, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("ml_top10pct_20hold", "ml", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=10)),
    ("ml_top10pct_50hold", "ml", 0.10, 0.30, 50, "equal", ExitRuleConfig(max_holding_days=15)),
    # Factor-weighted portfolio allocation
    ("icw_top10pct_fw_20hold", "ic_weighted", 0.10, 0.30, 20, "factor_weighted", ExitRuleConfig(max_holding_days=10)),
    ("ml_top10pct_fw_20hold", "ml", 0.10, 0.30, 20, "factor_weighted", ExitRuleConfig(max_holding_days=10)),
    # No exit rule variants
    ("ml_top10pct_nomax", "ml", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=None)),
    ("icirw_top10pct_nomax", "icir_weighted", 0.10, 0.30, 20, "equal", ExitRuleConfig(max_holding_days=None)),
    # Aggressive short-term
    ("ml_top3pct_10hold_aggressive", "ml", 0.03, 0.10, 10, "factor_weighted", ExitRuleConfig(max_holding_days=5, stop_loss=-0.05)),
]


def run_strategies(
    panel: pd.DataFrame,
    selected_factors: list[str],
    target_col: str = "overnight_return",
    output_dir: Path = Path("apps/quant_platform/research/output"),
) -> pd.DataFrame:
    results: list[dict] = []

    for name, method, top_pct, hold_pct, max_h, weighting, exit_cfg in STRATEGY_CONFIGS:
        t = _step(f"Strategy: {name} (method={method})")
        try:
            composite = CompositeFactorBuilder().build(
                panel, factor_cols=selected_factors, target_col=target_col, method=method,
            )
            signal_gen = TopPercentSignalGenerator(
                top_pct=top_pct, hold_pct=hold_pct, max_holdings=max_h, weighting=weighting,
            )
            backtest_cfg = PortfolioBacktestConfig(
                commission_rate=0.0003, stamp_tax=0.001, slippage=0.002,
            )
            strategy = FactorStrategy(
                signal_generator=signal_gen,
                backtest_engine=PortfolioBacktestEngine(backtest_cfg),
                exit_rule_engine=ExitRuleEngine(exit_cfg),
            )
            result = strategy.run(composite, factor_col="composite_factor", return_col=target_col)
            summary = result["summary"]
            summary["strategy_name"] = name
            summary["composite_method"] = method
            summary["top_pct"] = top_pct
            summary["max_holdings"] = max_h
            summary["weighting"] = weighting
            summary["exit_max_days"] = exit_cfg.max_holding_days

            # Save daily nav for this strategy
            daily: pd.DataFrame = result["daily_results"]
            daily_path = output_dir / "strategy_navs" / f"{name}_daily.csv"
            daily_path.parent.mkdir(parents=True, exist_ok=True)
            daily.to_csv(daily_path)

            results.append(summary)
            log.info("  %s => sharpe=%.3f, annual=%.2f%%, maxdd=%.2f%%",
                      name, summary["sharpe_ratio"], summary["annual_return"] * 100, summary["max_drawdown"] * 100)
        except Exception as exc:
            log.error("  %s failed: %s", name, exc)
        _done(t)

    comparison = pd.DataFrame(results).sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)
    return comparison


# ── 5. MAIN ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Full overnight-return prediction pipeline")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--output-dir", default="apps/quant_platform/research/output")
    parser.add_argument("--max-factors", type=int, default=60, help="Max factors to keep after screening")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = ResearchConfig(start_date=args.start_date, end_date=args.end_date, output_dir=output_dir)
    loader = ResearchDataLoader(config)

    # 1. Load data
    sources = load_all_data(loader, start_date=args.start_date, end_date=args.end_date)

    # 2. Build all factors
    panel, all_factor_cols = build_all_factors(sources)

    # 3. Standardize factors
    t = _step("Running standard factor pipeline (winsorize + zscore)")
    panel = run_standard_factor_pipeline(panel, factor_cols=all_factor_cols)
    _done(t)

    # 4. Screen factors by IC
    ranking, selected_factors = screen_factors(
        panel, all_factor_cols, max_factors=args.max_factors,
    )
    ranking_path = output_dir / "factor_ranking_full.csv"
    ranking.to_csv(ranking_path, index=False)
    report_builder = ResearchReportBuilder(output_dir)
    report_builder.build_ranking_report(
        ranking.rename(columns={"factor": "factor_name"}),
        report_name="factor_ranking_full",
        title="Full Pipeline Factor Ranking",
    )
    log.info("Factor ranking saved to %s", ranking_path)

    # Print top 30 factors
    log.info("\n%s", "=" * 80)
    log.info("TOP 30 FACTORS BY |IC_IR|:")
    log.info("%-45s %8s %8s %8s %8s %8s", "Factor", "MeanIC", "RankIC", "IC_IR", "IC>0%", "L-S Mean")
    log.info("-" * 80)
    for _, row in ranking.head(30).iterrows():
        log.info("%-45s %8.4f %8.4f %8.4f %7.1f%% %8.5f",
                  row["factor"], row["mean_ic"], row["rank_ic"], row["ic_ir"],
                  row["positive_rate"] * 100, row["long_short_mean"])
    log.info("=" * 80)

    if not selected_factors:
        log.error("No significant factors found. Aborting.")
        return

    # 5. Run all strategies
    comparison = run_strategies(panel, selected_factors, output_dir=output_dir)
    comparison_path = output_dir / "strategy_comparison.csv"
    comparison.to_csv(comparison_path, index=False)
    report_builder.build_strategy_comparison_report(comparison, report_name="strategy_comparison")

    # Print strategy comparison
    log.info("\n%s", "=" * 100)
    log.info("STRATEGY COMPARISON (sorted by Sharpe):")
    log.info("%-40s %8s %10s %8s %8s %8s %8s",
              "Strategy", "Sharpe", "AnnReturn", "MaxDD", "Calmar", "Turnover", "FinalNAV")
    log.info("-" * 100)
    for _, row in comparison.iterrows():
        log.info("%-40s %8.3f %9.2f%% %7.2f%% %8.3f %8.4f %10.0f",
                  row["strategy_name"], row["sharpe_ratio"],
                  row["annual_return"] * 100, row["max_drawdown"] * 100,
                  row["calmar_ratio"], row["average_turnover"],
                  row["final_nav"])
    log.info("=" * 100)

    # Save best strategy summary
    best = comparison.iloc[0].to_dict() if not comparison.empty else {}
    best_path = output_dir / "best_strategy.json"
    with best_path.open("w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2, default=str)

    log.info("\nBest strategy: %s (Sharpe=%.3f, Annual=%.2f%%, MaxDD=%.2f%%)",
              best.get("strategy_name", "N/A"),
              best.get("sharpe_ratio", 0),
              best.get("annual_return", 0) * 100,
              best.get("max_drawdown", 0) * 100)
    log.info("\nOutputs saved to: %s", output_dir)
    log.info("  - factor_ranking_full.csv: all factors ranked by IC_IR")
    log.info("  - strategy_comparison.csv: all strategy backtests compared")
    log.info("  - strategy_navs/: daily NAV for each strategy")
    log.info("  - best_strategy.json: best strategy summary")


if __name__ == "__main__":
    main()
