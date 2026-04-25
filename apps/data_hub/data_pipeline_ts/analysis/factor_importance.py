"""
Factor importance analysis for predicting next-day opening price.

Target: next_open_return = (open_qfq[t+1] / close_qfq[t]) - 1
Sources:
  - stock_stk_factor_pro  (technical factors, valuations, OHLCV)
  - stock_money_flow       (institutional/retail fund flows)
  - stock_cyq_perf         (chip distribution & winner rate)
  - stock_margin_detail    (margin trading activity)

Methods:
  1. Spearman rank correlation (linear monotonic)
  2. Mutual information (non-linear)
  3. Random Forest feature importance
  4. Gradient Boosting feature importance
  5. Permutation importance (model-agnostic)
  6. Multi-factor interaction screening

Usage:
  python -m apps.data_hub.data_pipeline_ts.analysis.factor_importance
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from shared.stock_core.db import build_mysql_url

warnings.filterwarnings("ignore", category=FutureWarning)

RECENT_MONTHS = 3
STOCK_SAMPLE_SIZE = 500
MIN_ROWS_PER_STOCK = 20
MAX_NAN_RATIO = 0.5

QFQ_TECHNICAL_FACTORS = [
    "asi_qfq", "asit_qfq", "atr_qfq", "bbi_qfq",
    "bias1_qfq", "bias2_qfq", "bias3_qfq",
    "boll_lower_qfq", "boll_mid_qfq", "boll_upper_qfq",
    "brar_ar_qfq", "brar_br_qfq",
    "cci_qfq", "cr_qfq",
    "dfma_dif_qfq", "dfma_difma_qfq",
    "dmi_adx_qfq", "dmi_adxr_qfq", "dmi_mdi_qfq", "dmi_pdi_qfq",
    "dpo_qfq", "madpo_qfq",
    "ema_qfq_5", "ema_qfq_10", "ema_qfq_20", "ema_qfq_30", "ema_qfq_60", "ema_qfq_90", "ema_qfq_250",
    "emv_qfq", "maemv_qfq",
    "expma_12_qfq", "expma_50_qfq",
    "kdj_qfq", "kdj_d_qfq", "kdj_k_qfq",
    "ktn_down_qfq", "ktn_mid_qfq", "ktn_upper_qfq",
    "ma_qfq_5", "ma_qfq_10", "ma_qfq_20", "ma_qfq_30", "ma_qfq_60", "ma_qfq_90", "ma_qfq_250",
    "macd_qfq", "macd_dea_qfq", "macd_dif_qfq",
    "mass_qfq", "ma_mass_qfq",
    "mfi_qfq",
    "mtm_qfq", "mtmma_qfq",
    "obv_qfq",
    "psy_qfq", "psyma_qfq",
    "roc_qfq", "maroc_qfq",
    "rsi_qfq_6", "rsi_qfq_12", "rsi_qfq_24",
    "taq_down_qfq", "taq_mid_qfq", "taq_up_qfq",
    "trix_qfq", "trma_qfq",
    "vr_qfq",
    "wr_qfq", "wr1_qfq",
    "xsii_td1_qfq", "xsii_td2_qfq", "xsii_td3_qfq", "xsii_td4_qfq",
]

VALUATION_COLS = [
    "turnover_rate", "turnover_rate_f", "volume_ratio",
    "pe", "pe_ttm", "pb", "ps", "ps_ttm",
    "dv_ratio", "dv_ttm",
    "total_mv", "circ_mv",
]

PRICE_COLS = [
    "open_qfq", "high_qfq", "low_qfq", "close_qfq",
    "pct_chg", "vol", "amount",
    "downdays", "updays", "lowdays", "topdays",
]

MONEY_FLOW_COLS = [
    "buy_sm_vol", "buy_sm_amount", "sell_sm_vol", "sell_sm_amount",
    "buy_md_vol", "buy_md_amount", "sell_md_vol", "sell_md_amount",
    "buy_lg_vol", "buy_lg_amount", "sell_lg_vol", "sell_lg_amount",
    "buy_elg_vol", "buy_elg_amount", "sell_elg_vol", "sell_elg_amount",
    "net_mf_vol", "net_mf_amount",
]

CYQ_COLS = [
    "his_low", "his_high",
    "cost_5pct", "cost_15pct", "cost_50pct", "cost_85pct", "cost_95pct",
    "weight_avg", "winner_rate",
]

MARGIN_COLS = [
    "rzye", "rqye", "rzmre", "rqyl", "rzche", "rqchl", "rqmcl", "rzrqye",
]


def _p(msg: str):
    print(msg, flush=True)


def _get_engine():
    from sqlalchemy import create_engine
    url = build_mysql_url("TS_MYSQL_DATABASE")
    return create_engine(url, pool_recycle=3600)


def _load_sampled_stocks(engine, start_date: str, sample_size: int) -> list[str]:
    """Pick the most actively traded stocks for analysis."""
    query = text("""
        SELECT ts_code, COUNT(*) as cnt
        FROM stock_stk_factor_pro
        WHERE trade_date >= :start_date AND vol > 0 AND close_qfq IS NOT NULL
        GROUP BY ts_code
        HAVING cnt >= :min_rows
        ORDER BY cnt DESC
        LIMIT :sample_size
    """)
    _p(f"  Sampling top {sample_size} stocks by trading-day count ...")
    df = pd.read_sql(query, engine, params={
        "start_date": start_date, "min_rows": MIN_ROWS_PER_STOCK, "sample_size": sample_size,
    })
    codes = df["ts_code"].tolist()
    _p(f"  => {len(codes)} stocks selected")
    return codes


def _load_factor_pro(engine, start_date: str, ts_codes: list[str]) -> pd.DataFrame:
    all_cols = ["ts_code", "trade_date"] + PRICE_COLS + VALUATION_COLS + QFQ_TECHNICAL_FACTORS
    cols_sql = ", ".join(f"`{c}`" for c in all_cols)
    placeholders = ",".join([f":c{i}" for i in range(len(ts_codes))])
    params = {"start_date": start_date}
    params.update({f"c{i}": code for i, code in enumerate(ts_codes)})
    query = text(f"""
        SELECT {cols_sql}
        FROM stock_stk_factor_pro
        WHERE trade_date >= :start_date AND ts_code IN ({placeholders})
        ORDER BY ts_code, trade_date
    """)
    _p(f"  Loading stock_stk_factor_pro (>= {start_date}, {len(ts_codes)} stocks) ...")
    df = pd.read_sql(query, engine, params=params)
    _p(f"  => {len(df):,} rows, {len(df['ts_code'].unique()):,} stocks")
    return df


def _in_clause(ts_codes: list[str]) -> tuple[str, dict]:
    placeholders = ",".join([f":c{i}" for i in range(len(ts_codes))])
    params = {f"c{i}": code for i, code in enumerate(ts_codes)}
    return placeholders, params


def _load_money_flow(engine, start_date: str, ts_codes: list[str]) -> pd.DataFrame:
    cols = ["ts_code", "trade_date"] + MONEY_FLOW_COLS
    cols_sql = ", ".join(f"`{c}`" for c in cols)
    placeholders, params = _in_clause(ts_codes)
    params["start_date"] = start_date
    query = text(f"""
        SELECT {cols_sql}
        FROM stock_money_flow
        WHERE trade_date >= :start_date AND ts_code IN ({placeholders})
    """)
    _p(f"  Loading stock_money_flow ...")
    df = pd.read_sql(query, engine, params=params)
    _p(f"  => {len(df):,} rows")
    return df


def _load_cyq_perf(engine, start_date: str, ts_codes: list[str]) -> pd.DataFrame:
    cols = ["ts_code", "trade_date"] + CYQ_COLS
    cols_sql = ", ".join(f"`{c}`" for c in cols)
    placeholders, params = _in_clause(ts_codes)
    params["start_date"] = start_date
    query = text(f"""
        SELECT {cols_sql}
        FROM stock_cyq_perf
        WHERE trade_date >= :start_date AND ts_code IN ({placeholders})
    """)
    _p(f"  Loading stock_cyq_perf ...")
    df = pd.read_sql(query, engine, params=params)
    _p(f"  => {len(df):,} rows")
    return df


def _load_margin_detail(engine, start_date: str, ts_codes: list[str]) -> pd.DataFrame:
    cols = ["ts_code", "trade_date"] + MARGIN_COLS
    cols_sql = ", ".join(f"`{c}`" for c in cols)
    placeholders, params = _in_clause(ts_codes)
    params["start_date"] = start_date
    query = text(f"""
        SELECT {cols_sql}
        FROM stock_margin_detail
        WHERE trade_date >= :start_date AND ts_code IN ({placeholders})
    """)
    _p(f"  Loading stock_margin_detail ...")
    df = pd.read_sql(query, engine, params=params)
    _p(f"  => {len(df):,} rows")
    return df


def _compute_start_date(months: int) -> str:
    from datetime import datetime, timedelta
    d = datetime.now() - timedelta(days=months * 30)
    return d.strftime("%Y%m%d")


def engineer_features(factor_df: pd.DataFrame, mf_df: pd.DataFrame,
                       cyq_df: pd.DataFrame, margin_df: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix with cross-table joins and derived features."""
    df = factor_df.copy()
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

    close = df["close_qfq"]
    eps = 1e-10

    # --- Relative price positions (normalize MA/BOLL/channel to close) ---
    ma_cols = [c for c in df.columns if c.startswith("ma_qfq_") or c.startswith("ema_qfq_") or c.startswith("expma_")]
    for col in ma_cols:
        df[f"rel_{col}"] = (close - df[col]) / (df[col].abs() + eps)

    for prefix in ["boll", "ktn", "taq", "xsii"]:
        upper_cols = [c for c in df.columns if c.startswith(prefix) and "upper" in c or "up" in c or "td1" in c or "td2" in c]
        lower_cols = [c for c in df.columns if c.startswith(prefix) and ("lower" in c or "down" in c or "td3" in c or "td4" in c)]
        for col in upper_cols + lower_cols:
            df[f"rel_{col}"] = (close - df[col]) / (df[col].abs() + eps)

    # --- Price-derived features ---
    df["intraday_range"] = (df["high_qfq"] - df["low_qfq"]) / (close + eps)
    df["upper_shadow"] = (df["high_qfq"] - np.maximum(df["open_qfq"], close)) / (close + eps)
    df["lower_shadow"] = (np.minimum(df["open_qfq"], close) - df["low_qfq"]) / (close + eps)
    df["body_ratio"] = (close - df["open_qfq"]) / (df["high_qfq"] - df["low_qfq"] + eps)
    df["amount_per_vol"] = df["amount"] / (df["vol"] + eps)

    # --- Cross-table: money flow ---
    if not mf_df.empty:
        mf = mf_df.copy()
        total_amount = mf["buy_sm_amount"] + mf["buy_md_amount"] + mf["buy_lg_amount"] + mf["buy_elg_amount"] + \
                       mf["sell_sm_amount"] + mf["sell_md_amount"] + mf["sell_lg_amount"] + mf["sell_elg_amount"]
        total_amount = total_amount.replace(0, np.nan)

        mf["mf_net_sm"] = (mf["buy_sm_amount"] - mf["sell_sm_amount"]) / total_amount
        mf["mf_net_md"] = (mf["buy_md_amount"] - mf["sell_md_amount"]) / total_amount
        mf["mf_net_lg"] = (mf["buy_lg_amount"] - mf["sell_lg_amount"]) / total_amount
        mf["mf_net_elg"] = (mf["buy_elg_amount"] - mf["sell_elg_amount"]) / total_amount
        mf["mf_net_ratio"] = mf["net_mf_amount"] / total_amount
        mf["mf_big_buy_ratio"] = (mf["buy_lg_amount"] + mf["buy_elg_amount"]) / total_amount
        mf["mf_big_sell_ratio"] = (mf["sell_lg_amount"] + mf["sell_elg_amount"]) / total_amount

        mf_features = mf[["ts_code", "trade_date",
                           "mf_net_sm", "mf_net_md", "mf_net_lg", "mf_net_elg",
                           "mf_net_ratio", "mf_big_buy_ratio", "mf_big_sell_ratio"]]
        df = df.merge(mf_features, on=["ts_code", "trade_date"], how="left")

    # --- Cross-table: chip distribution ---
    if not cyq_df.empty:
        cyq = cyq_df.copy()
        cyq["chip_spread"] = (cyq["cost_95pct"] - cyq["cost_5pct"]) / (cyq["weight_avg"] + eps)
        cyq["chip_skew"] = (cyq["cost_50pct"] - cyq["weight_avg"]) / (cyq["cost_95pct"] - cyq["cost_5pct"] + eps)
        cyq["chip_concentration"] = (cyq["cost_85pct"] - cyq["cost_15pct"]) / (cyq["cost_95pct"] - cyq["cost_5pct"] + eps)

        cyq_features = cyq[["ts_code", "trade_date",
                             "winner_rate", "chip_spread", "chip_skew", "chip_concentration"]]
        df = df.merge(cyq_features, on=["ts_code", "trade_date"], how="left")

    # --- Cross-table: margin ---
    if not margin_df.empty:
        mg = margin_df.copy()
        mg["margin_buy_intensity"] = mg["rzmre"] / (mg["rzye"] + eps)
        mg["margin_net_ratio"] = (mg["rzmre"] - mg["rzche"]) / (mg["rzye"] + eps)
        mg["short_sell_ratio"] = mg["rqmcl"] / (mg["rqye"] + eps)
        mg["margin_balance_ratio"] = mg["rzye"] / (mg["rzrqye"] + eps)

        mg_features = mg[["ts_code", "trade_date",
                           "margin_buy_intensity", "margin_net_ratio",
                           "short_sell_ratio", "margin_balance_ratio"]]
        df = df.merge(mg_features, on=["ts_code", "trade_date"], how="left")

    return df


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    """Create next-day open return as target. Shift within each stock group."""
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    df["next_open_qfq"] = df.groupby("ts_code")["open_qfq"].shift(-1)
    df["target"] = (df["next_open_qfq"] / df["close_qfq"]) - 1

    before = len(df)
    df = df.dropna(subset=["target"])
    df = df[df["target"].between(-0.20, 0.20)]
    _p(f"  Target built: {before:,} -> {len(df):,} rows (dropped NaN/extreme)")
    return df


def select_feature_columns(df: pd.DataFrame) -> list[str]:
    """Select numeric columns that are valid features (not identifiers/target)."""
    exclude = {"ts_code", "trade_date", "target", "next_open_qfq",
               "open_qfq", "high_qfq", "low_qfq", "close_qfq"}
    candidates = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]

    valid = []
    for col in candidates:
        nan_ratio = df[col].isna().mean()
        if nan_ratio < MAX_NAN_RATIO:
            valid.append(col)
    return valid


def analyze_correlations(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Spearman rank correlation with target."""
    results = []
    target = df["target"].values
    for feat in features:
        vals = df[feat].values
        mask = ~(np.isnan(vals) | np.isnan(target))
        if mask.sum() < 100:
            continue
        corr, pval = stats.spearmanr(vals[mask], target[mask])
        results.append({"feature": feat, "spearman_corr": corr, "spearman_pval": pval,
                         "abs_corr": abs(corr)})
    return pd.DataFrame(results).sort_values("abs_corr", ascending=False)


def analyze_mutual_info(X: np.ndarray, y: np.ndarray, features: list[str]) -> pd.DataFrame:
    """Mutual information regression scores."""
    mi_scores = mutual_info_regression(X, y, n_neighbors=5, random_state=42)
    return pd.DataFrame({
        "feature": features, "mutual_info": mi_scores,
    }).sort_values("mutual_info", ascending=False)


def analyze_tree_importance(X_train: np.ndarray, y_train: np.ndarray,
                             X_test: np.ndarray, y_test: np.ndarray,
                             features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Random Forest and Gradient Boosting feature importance."""
    _p("\n  Training Random Forest ...")
    rf = RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=50,
                                n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)
    rf_score = rf.score(X_test, y_test)
    _p(f"    RF R^2 = {rf_score:.6f}")

    rf_imp = pd.DataFrame({
        "feature": features,
        "rf_importance": rf.feature_importances_,
    }).sort_values("rf_importance", ascending=False)

    _p("  Training Gradient Boosting ...")
    gb = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                    subsample=0.8, min_samples_leaf=50, random_state=42)
    gb.fit(X_train, y_train)
    gb_score = gb.score(X_test, y_test)
    _p(f"    GB R^2 = {gb_score:.6f}")

    gb_imp = pd.DataFrame({
        "feature": features,
        "gb_importance": gb.feature_importances_,
    }).sort_values("gb_importance", ascending=False)

    _p("  Computing permutation importance (GB) ...")
    perm = permutation_importance(gb, X_test, y_test, n_repeats=10,
                                   random_state=42, n_jobs=-1)
    perm_imp = pd.DataFrame({
        "feature": features,
        "perm_importance_mean": perm.importances_mean,
        "perm_importance_std": perm.importances_std,
    }).sort_values("perm_importance_mean", ascending=False)

    return rf_imp, gb_imp, perm_imp, rf, gb


def analyze_interactions(df: pd.DataFrame, top_features: list[str], n_top: int = 10) -> pd.DataFrame:
    """Screen pairwise feature interactions for predicting target."""
    target = df["target"].values
    results = []
    candidates = top_features[:n_top]

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            f1, f2 = candidates[i], candidates[j]
            v1 = df[f1].values
            v2 = df[f2].values
            interaction = v1 * v2
            mask = ~(np.isnan(interaction) | np.isnan(target))
            if mask.sum() < 100:
                continue
            corr, _ = stats.spearmanr(interaction[mask], target[mask])
            results.append({
                "factor_1": f1, "factor_2": f2,
                "interaction_corr": corr, "abs_interaction_corr": abs(corr),
            })

    return pd.DataFrame(results).sort_values("abs_interaction_corr", ascending=False)


def print_section(title: str):
    _p(f"\n{'='*80}")
    _p(f"  {title}")
    _p(f"{'='*80}")


def _feature_category(name: str) -> str:
    if name.startswith("mf_"):
        return "资金流向"
    if name.startswith("chip_") or name == "winner_rate":
        return "筹码分布"
    if name.startswith("margin_") or name.startswith("short_"):
        return "融资融券"
    if name.startswith("rel_"):
        return "相对位置"
    if name in VALUATION_COLS:
        return "估值指标"
    if name in ("intraday_range", "upper_shadow", "lower_shadow", "body_ratio", "amount_per_vol"):
        return "K线形态"
    if name in ("pct_chg", "vol", "amount", "downdays", "updays", "lowdays", "topdays"):
        return "行情基础"
    return "技术因子"


def main():
    print_section("Factor Importance Analysis: Predicting Next-Day Open Price")
    _p("  Target: next_open_return = open_qfq[t+1] / close_qfq[t] - 1")

    engine = _get_engine()
    start_date = _compute_start_date(RECENT_MONTHS)

    print_section(f"Step 1: Loading Data (last {RECENT_MONTHS} months, >= {start_date})")
    ts_codes = _load_sampled_stocks(engine, start_date, STOCK_SAMPLE_SIZE)
    if not ts_codes:
        _p("ERROR: No stocks found. Aborting.")
        return

    factor_df = _load_factor_pro(engine, start_date, ts_codes)

    try:
        mf_df = _load_money_flow(engine, start_date, ts_codes)
    except Exception as e:
        _p(f"  [WARN] money_flow unavailable: {e}")
        mf_df = pd.DataFrame()

    try:
        cyq_df = _load_cyq_perf(engine, start_date, ts_codes)
    except Exception as e:
        _p(f"  [WARN] cyq_perf unavailable: {e}")
        cyq_df = pd.DataFrame()

    try:
        margin_df = _load_margin_detail(engine, start_date, ts_codes)
    except Exception as e:
        _p(f"  [WARN] margin_detail unavailable: {e}")
        margin_df = pd.DataFrame()

    if factor_df.empty:
        _p("ERROR: No data in stock_stk_factor_pro. Aborting.")
        return

    print_section("Step 2: Feature Engineering")
    df = engineer_features(factor_df, mf_df, cyq_df, margin_df)
    df = build_target(df)
    features = select_feature_columns(df)
    _p(f"  Valid features: {len(features)}")

    X = df[features].values.astype(np.float64)
    y = df["target"].values.astype(np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 1) Spearman ---
    print_section("Step 3: Spearman Rank Correlation")
    corr_df = analyze_correlations(df, features)
    _p("\n  Top 30 by |Spearman correlation|:")
    for _, row in corr_df.head(30).iterrows():
        cat = _feature_category(row["feature"])
        sig = "***" if row["spearman_pval"] < 0.001 else "**" if row["spearman_pval"] < 0.01 else "*" if row["spearman_pval"] < 0.05 else ""
        _p(f"    {row['feature']:<40s} r={row['spearman_corr']:+.4f}  [{cat}] {sig}")

    # --- 2) Mutual Information ---
    print_section("Step 4: Mutual Information (non-linear dependency)")
    mi_df = analyze_mutual_info(X, y, features)
    _p("\n  Top 30 by mutual information:")
    for _, row in mi_df.head(30).iterrows():
        cat = _feature_category(row["feature"])
        _p(f"    {row['feature']:<40s} MI={row['mutual_info']:.6f}  [{cat}]")

    # --- 3) Tree models ---
    print_section("Step 5: Tree-Based Feature Importance")
    rf_imp, gb_imp, perm_imp, rf_model, gb_model = analyze_tree_importance(
        X_train, y_train, X_test, y_test, features,
    )

    _p("\n  Top 30 Random Forest importance:")
    for _, row in rf_imp.head(30).iterrows():
        cat = _feature_category(row["feature"])
        _p(f"    {row['feature']:<40s} imp={row['rf_importance']:.6f}  [{cat}]")

    _p("\n  Top 30 Gradient Boosting importance:")
    for _, row in gb_imp.head(30).iterrows():
        cat = _feature_category(row["feature"])
        _p(f"    {row['feature']:<40s} imp={row['gb_importance']:.6f}  [{cat}]")

    _p("\n  Top 30 Permutation importance (GB model):")
    for _, row in perm_imp.head(30).iterrows():
        cat = _feature_category(row["feature"])
        _p(f"    {row['feature']:<40s} imp={row['perm_importance_mean']:.6f} +/- {row['perm_importance_std']:.6f}  [{cat}]")

    # --- 4) Consolidated ranking ---
    print_section("Step 6: Consolidated Factor Ranking")
    merged = corr_df[["feature", "abs_corr"]].merge(
        mi_df[["feature", "mutual_info"]], on="feature", how="outer"
    ).merge(
        rf_imp[["feature", "rf_importance"]], on="feature", how="outer"
    ).merge(
        gb_imp[["feature", "gb_importance"]], on="feature", how="outer"
    ).merge(
        perm_imp[["feature", "perm_importance_mean"]], on="feature", how="outer"
    ).fillna(0)

    for col in ["abs_corr", "mutual_info", "rf_importance", "gb_importance", "perm_importance_mean"]:
        col_max = merged[col].max()
        if col_max > 0:
            merged[f"{col}_rank"] = merged[col].rank(ascending=False, method="min")

    rank_cols = [c for c in merged.columns if c.endswith("_rank")]
    merged["avg_rank"] = merged[rank_cols].mean(axis=1)
    merged = merged.sort_values("avg_rank")

    _p("\n  Top 40 factors by average rank across all methods:")
    _p(f"  {'#':<4s} {'Feature':<40s} {'AvgRank':>8s}  {'Corr':>7s} {'MI':>7s} {'RF':>7s} {'GB':>7s} {'Perm':>7s}  Category")
    _p(f"  {'-'*4} {'-'*40} {'-'*8}  {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}  {'-'*10}")
    for i, (_, row) in enumerate(merged.head(40).iterrows(), 1):
        cat = _feature_category(row["feature"])
        _p(f"  {i:<4d} {row['feature']:<40s} {row['avg_rank']:8.1f}  "
           f"{row['abs_corr']:7.4f} {row['mutual_info']:7.4f} "
           f"{row['rf_importance']:7.4f} {row['gb_importance']:7.4f} "
           f"{row['perm_importance_mean']:7.4f}  {cat}")

    # --- 5) Interaction analysis ---
    print_section("Step 7: Multi-Factor Interaction Screening")
    top_factor_names = merged.head(20)["feature"].tolist()
    interaction_df = analyze_interactions(df, top_factor_names, n_top=15)

    _p("\n  Top 20 pairwise interactions (factor1 * factor2 -> target):")
    for i, (_, row) in enumerate(interaction_df.head(20).iterrows(), 1):
        _p(f"    {i:<3d} {row['factor_1']:<35s} x {row['factor_2']:<35s}  r={row['interaction_corr']:+.4f}")

    # --- 6) Category summary ---
    print_section("Step 8: Factor Category Summary")
    merged["category"] = merged["feature"].apply(_feature_category)
    cat_summary = merged.head(40).groupby("category").agg(
        count=("feature", "count"),
        best_avg_rank=("avg_rank", "min"),
        mean_abs_corr=("abs_corr", "mean"),
    ).sort_values("count", ascending=False)

    _p("\n  Category distribution in top-40 factors:")
    for cat, row in cat_summary.iterrows():
        _p(f"    {cat:<12s}  count={int(row['count']):>3d}  best_rank={row['best_avg_rank']:6.1f}  mean|corr|={row['mean_abs_corr']:.4f}")

    print_section("Analysis Complete")
    _p(f"  Total features analyzed: {len(features)}")
    _p(f"  Data period: {start_date} ~ present")
    _p(f"  Sample size: {len(df):,} stock-day observations")
    _p("")


if __name__ == "__main__":
    main()
