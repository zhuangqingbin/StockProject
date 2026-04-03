"""
跨表多因子组合 → 高胜率次日收益策略
=============================================
价格字段: close_qfq (前复权收盘价), 次日收益 = 次日close_qfq / 当日close_qfq - 1

方法:
  以 factor_pro 为基础表, LEFT JOIN 资金流向、筹码、融资融券、北向资金、涨跌停等
  构建跨表组合信号, 寻找高胜率+正收益的组合

核心逻辑:
  多个独立数据源同时发出同向信号 → 共振 → 更高置信度
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import numpy as np

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df
from apps.data_hub.data_pipeline_ts.analysis.common.metrics import (
    signal_stats, holding_period_returns, print_report,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_base(start_date: str) -> pd.DataFrame:
    """加载 factor_pro 基础数据 (只取需要的列)"""
    sql = """
    SELECT
        ts_code, trade_date,
        close, close_qfq, vol, amount,
        volume_ratio, turnover_rate_f, pct_chg,
        pe_ttm, pb, total_mv, circ_mv,
        macd_dif_bfq, macd_dea_bfq, macd_bfq,
        rsi_bfq_6, rsi_bfq_12,
        kdj_k_bfq, kdj_d_bfq,
        boll_upper_bfq, boll_mid_bfq, boll_lower_bfq,
        bias1_bfq, cci_bfq,
        ma_bfq_5, ma_bfq_20, ma_bfq_60
    FROM stock_stk_factor_pro
    WHERE trade_date >= :start_date
    ORDER BY ts_code, trade_date
    """
    return query_df(sql, {"start_date": start_date})


def load_money_flow(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        ts_code, trade_date,
        buy_elg_amount, sell_elg_amount,
        buy_lg_amount, sell_lg_amount,
        net_mf_amount
    FROM stock_money_flow
    WHERE trade_date >= :start_date
    """
    df = query_df(sql, {"start_date": start_date})
    df["main_net"] = (df["buy_elg_amount"] + df["buy_lg_amount"]
                      - df["sell_elg_amount"] - df["sell_lg_amount"])
    df["elg_net"] = df["buy_elg_amount"] - df["sell_elg_amount"]
    return df[["ts_code", "trade_date", "main_net", "elg_net", "net_mf_amount"]]


def load_cyq(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT ts_code, trade_date, winner_rate, cost_5pct, cost_95pct, weight_avg
    FROM stock_cyq_perf
    WHERE trade_date >= :start_date
    """
    return query_df(sql, {"start_date": start_date})


def load_margin(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT ts_code, trade_date, rzye, rzmre, rzche, rqye, rqyl
    FROM stock_margin_detail
    WHERE trade_date >= :start_date
    """
    return query_df(sql, {"start_date": start_date})


def load_northbound(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT ts_code, trade_date, vol AS hk_vol, ratio AS hk_ratio
    FROM stock_hk_hold
    WHERE trade_date >= :start_date AND ratio IS NOT NULL AND ratio > 0
    """
    return query_df(sql, {"start_date": start_date})


def load_limit(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT ts_code, trade_date, `limit` AS limit_type, open_times, fd_amount, limit_times
    FROM stock_limit_list_d
    WHERE trade_date >= :start_date
    """
    return query_df(sql, {"start_date": start_date})


def build_features(start_date: str) -> pd.DataFrame:
    """合并所有数据源, 构建特征"""
    print("  Loading base (factor_pro) ...")
    base = load_base(start_date)
    print(f"    {len(base):,} rows")

    print("  Loading money_flow ...")
    mf = load_money_flow(start_date)
    print(f"    {len(mf):,} rows")

    print("  Loading cyq_perf ...")
    cyq = load_cyq(start_date)
    print(f"    {len(cyq):,} rows")

    print("  Loading margin_detail ...")
    margin = load_margin(start_date)
    print(f"    {len(margin):,} rows")

    print("  Loading hk_hold ...")
    nb = load_northbound(start_date)
    print(f"    {len(nb):,} rows")

    print("  Loading limit_list_d ...")
    limit = load_limit(start_date)
    print(f"    {len(limit):,} rows")

    # Merge all onto base
    print("  Merging ...")
    df = base.merge(mf, on=["ts_code", "trade_date"], how="left")
    df = df.merge(cyq, on=["ts_code", "trade_date"], how="left")
    df = df.merge(margin, on=["ts_code", "trade_date"], how="left")
    df = df.merge(nb, on=["ts_code", "trade_date"], how="left")
    df = df.merge(limit, on=["ts_code", "trade_date"], how="left")

    print(f"  Merged: {len(df):,} rows")
    return df


def compute_factor_flags(df: pd.DataFrame) -> pd.DataFrame:
    """计算每个数据源的二元看多/看空标记"""
    df = df.copy()
    df = df.sort_values(["ts_code", "trade_date"])

    # ---------- 技术面 ----------
    df["f_macd_bull"] = df["macd_dif_bfq"] > df["macd_dea_bfq"]
    df["f_rsi_oversold"] = df["rsi_bfq_6"] < 30
    df["f_rsi_overbought"] = df["rsi_bfq_6"] > 70
    df["f_ma_bull"] = (df["ma_bfq_5"] > df["ma_bfq_20"]) & (df["ma_bfq_20"] > df["ma_bfq_60"])
    df["f_near_boll_lower"] = df["close"] < df["boll_lower_bfq"] * 1.02
    df["f_near_boll_upper"] = df["close"] > df["boll_upper_bfq"] * 0.98
    df["f_vol_surge"] = df["volume_ratio"] > 1.5
    df["f_vol_shrink"] = df["volume_ratio"] < 0.8

    # ---------- 资金流向 ----------
    df["main_net_pct"] = df["main_net"] / df["amount"].replace(0, np.nan) * 100
    df["f_main_inflow"] = df["main_net"] > 0
    df["f_main_heavy_inflow"] = df["main_net_pct"] > 5
    df["f_main_heavy_outflow"] = df["main_net_pct"] < -5
    df["f_elg_inflow"] = df["elg_net"] > 0

    # ---------- 筹码 ----------
    df["f_low_winner"] = df["winner_rate"] < 10
    df["f_high_winner"] = df["winner_rate"] > 85
    df["f_mid_winner"] = (df["winner_rate"] > 30) & (df["winner_rate"] < 70)
    df["chip_spread_pct"] = (df["cost_95pct"] - df["cost_5pct"]) / df["weight_avg"].replace(0, np.nan) * 100
    df["f_chip_tight"] = df["chip_spread_pct"] < 20

    # ---------- 融资融券 ----------
    df["prev_rzye"] = df.groupby("ts_code")["rzye"].shift(1)
    df["rzye_chg_pct"] = (df["rzye"] / df["prev_rzye"].replace(0, np.nan) - 1) * 100
    df["f_rz_up"] = df["rzye_chg_pct"] > 3
    df["f_rz_down"] = df["rzye_chg_pct"] < -3

    # ---------- 北向资金 ----------
    df["prev_hk_ratio"] = df.groupby("ts_code")["hk_ratio"].shift(1)
    df["hk_ratio_chg"] = df["hk_ratio"] - df["prev_hk_ratio"]
    df["f_nb_add"] = df["hk_ratio_chg"] > 0.1
    df["f_nb_reduce"] = df["hk_ratio_chg"] < -0.1

    # ---------- 涨跌停 ----------
    df["f_limit_up"] = df["limit_type"] == "U"
    df["f_limit_down"] = df["limit_type"] == "D"
    df["f_first_limit_up"] = (df["limit_type"] == "U") & (df["limit_times"] == 1)

    # ---------- 次日收益 ----------
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def analyze_combos(df: pd.DataFrame):
    """测试所有有意义的跨表组合"""
    valid = df.dropna(subset=["next_ret"]).copy()
    print(f"\n  Total valid rows for combo analysis: {len(valid):,}")

    combos = {}

    # ============================================================
    # 做多组合
    # ============================================================

    # Combo 1: 主力流入 + MACD多头 + 筹码集中
    combos["L1: 主力流入+MACD多头+筹码集中"] = (
        valid["f_main_inflow"] & valid["f_macd_bull"] & valid["f_chip_tight"]
    )

    # Combo 2: 超大单流入 + 放量 + 均线多头
    combos["L2: 超大单流入+放量+均线多头"] = (
        valid["f_elg_inflow"] & valid["f_vol_surge"] & valid["f_ma_bull"]
    )

    # Combo 3: 北向加仓 + 主力流入 + MACD多头
    combos["L3: 北向加仓+主力流入+MACD多头"] = (
        valid["f_nb_add"] & valid["f_main_inflow"] & valid["f_macd_bull"]
    )

    # Combo 4: 融资增加 + 主力流入 + 均线多头
    combos["L4: 融资增加+主力流入+均线多头"] = (
        valid["f_rz_up"] & valid["f_main_inflow"] & valid["f_ma_bull"]
    )

    # Combo 5: 低获利比例 + 主力流入 + RSI超卖 (极端抄底)
    combos["L5: 低获利+主力流入+RSI超卖"] = (
        valid["f_low_winner"] & valid["f_main_inflow"] & valid["f_rsi_oversold"]
    )

    # Combo 6: 北向加仓 + 融资增加 + 放量
    combos["L6: 北向加仓+融资增加+放量"] = (
        valid["f_nb_add"] & valid["f_rz_up"] & valid["f_vol_surge"]
    )

    # Combo 7: 首板涨停 + 主力大幅流入
    combos["L7: 首板涨停+主力大幅流入"] = (
        valid["f_first_limit_up"] & valid["f_main_heavy_inflow"]
    )

    # Combo 8: 高获利比例 + 筹码集中 + MACD多头 + 缩量 (强势锁仓)
    combos["L8: 高获利+筹码集中+MACD多头+缩量"] = (
        valid["f_high_winner"] & valid["f_chip_tight"]
        & valid["f_macd_bull"] & valid["f_vol_shrink"]
    )

    # Combo 9: 北向加仓 + 超大单流入 + 筹码集中
    combos["L9: 北向加仓+超大单流入+筹码集中"] = (
        valid["f_nb_add"] & valid["f_elg_inflow"] & valid["f_chip_tight"]
    )

    # Combo 10: 底部共振 (近布林下轨 + RSI超卖 + 主力流入)
    combos["L10: 底部共振 (boll下轨+RSI超卖+主力流入)"] = (
        valid["f_near_boll_lower"] & valid["f_rsi_oversold"] & valid["f_main_inflow"]
    )

    # ============================================================
    # 做空/回避组合
    # ============================================================

    # Combo S1: 主力大幅流出 + RSI超买 + 近布林上轨
    combos["S1: 主力流出+RSI超买+近布林上轨"] = (
        valid["f_main_heavy_outflow"] & valid["f_rsi_overbought"] & valid["f_near_boll_upper"]
    )

    # Combo S2: 北向减仓 + 主力流出 + 高获利比例
    combos["S2: 北向减仓+主力流出+高获利比例"] = (
        valid["f_nb_reduce"] & valid["f_main_heavy_outflow"] & valid["f_high_winner"]
    )

    # Combo S3: 融资下降 + 主力流出 + 近布林上轨
    combos["S3: 融资下降+主力流出+近上轨"] = (
        valid["f_rz_down"] & valid["f_main_heavy_outflow"] & valid["f_near_boll_upper"]
    )

    # Combo S4: 跌停 + 主力大幅流出
    combos["S4: 跌停+主力大幅流出"] = (
        valid["f_limit_down"] & valid["f_main_heavy_outflow"]
    )

    # ============================================================
    # 评估
    # ============================================================

    results = []
    for name, mask in combos.items():
        n_triggered = mask.sum()
        if n_triggered < 10:
            results.append({
                "combo": name, "n": n_triggered,
                "avg_ret": np.nan, "med_ret": np.nan,
                "win_rate": np.nan, "std_ret": np.nan,
            })
            continue

        rets = valid.loc[mask, "next_ret"]
        results.append({
            "combo": name,
            "n": n_triggered,
            "avg_ret": round(rets.mean() * 100, 3),
            "med_ret": round(rets.median() * 100, 3),
            "win_rate": round((rets > 0).mean() * 100, 2),
            "std_ret": round(rets.std() * 100, 3),
        })

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values("win_rate", ascending=False)

    print("\n" + "=" * 80)
    print("  跨表组合信号 → 次日收益 (按胜率排序)")
    print("=" * 80)
    for _, row in result_df.iterrows():
        flag = "***" if row["win_rate"] and row["win_rate"] > 55 else "   "
        print(f"{flag} {row['combo']}")
        print(f"       样本={row['n']:,.0f}  胜率={row['win_rate']}%  "
              f"均收益={row['avg_ret']}%  中位数={row['med_ret']}%  "
              f"标准差={row['std_ret']}%")
        print()

    result_df.to_csv(OUTPUT_DIR / "combo_summary.csv", index=False)
    print(f"  Saved to {OUTPUT_DIR / 'combo_summary.csv'}")

    # ============================================================
    # 对胜率 > 50% 的组合计算持有期收益
    # ============================================================
    print("\n" + "=" * 80)
    print("  高胜率组合 — 多日持有收益")
    print("=" * 80)

    for name, mask in combos.items():
        row = result_df[result_df["combo"] == name].iloc[0]
        if pd.isna(row["win_rate"]) or row["win_rate"] < 50 or row["n"] < 20:
            continue

        triggered = valid.loc[mask, ["ts_code", "trade_date"]].drop_duplicates()
        # Sample max 300 for speed
        if len(triggered) > 300:
            triggered = triggered.sample(300, random_state=42)

        codes = triggered["ts_code"].unique().tolist()
        placeholders = ",".join([f"'{c}'" for c in codes[:300]])
        min_date = triggered["trade_date"].min()
        price_sql = f"""
        SELECT ts_code, trade_date, close_qfq
        FROM stock_stk_factor_pro
        WHERE ts_code IN ({placeholders})
          AND trade_date >= '{min_date}'
        ORDER BY ts_code, trade_date
        """
        prices = query_df(price_sql)
        hp = holding_period_returns(prices, triggered, periods=[1, 2, 3, 5])
        if hp.empty:
            continue

        avg = hp[[c for c in hp.columns if c.startswith("ret_")]].mean() * 100
        print(f"\n  [{name}] (n={row['n']:.0f}, 胜率={row['win_rate']}%)")
        for k, v in avg.items():
            print(f"    {k}: {v:.2f}%")

        hp.to_csv(OUTPUT_DIR / f"hp_{name[:10].replace(' ', '_')}.csv", index=False)

    return result_df


def scan_signal_strength(df: pd.DataFrame):
    """扫描信号强度: 统计每只股票当天有多少个看多/看空因子亮灯"""
    valid = df.dropna(subset=["next_ret"]).copy()

    bull_cols = [c for c in valid.columns if c.startswith("f_") and any(
        k in c for k in ["inflow", "bull", "add", "rz_up", "tight", "first_limit_up"]
    )]
    bear_cols = [c for c in valid.columns if c.startswith("f_") and any(
        k in c for k in ["outflow", "overbought", "reduce", "rz_down", "limit_down", "near_boll_upper"]
    )]

    valid["bull_count"] = valid[bull_cols].fillna(False).sum(axis=1)
    valid["bear_count"] = valid[bear_cols].fillna(False).sum(axis=1)
    valid["net_signal"] = valid["bull_count"] - valid["bear_count"]

    # 看多因子数量分组
    bull_stats = signal_stats(valid, "bull_count", "next_ret")
    print_report("看多因子亮灯数量 → 次日收益", bull_stats)
    bull_stats.to_csv(OUTPUT_DIR / "bull_count_stats.csv")

    # 净信号分组
    net_stats = signal_stats(valid, "net_signal", "next_ret")
    print_report("净信号 (多-空) → 次日收益", net_stats)
    net_stats.to_csv(OUTPUT_DIR / "net_signal_stats.csv")

    return valid


def run_analysis(start_date: str = "20240101"):
    print("=" * 80)
    print("  跨表多因子组合分析")
    print("  价格字段: close_qfq (前复权收盘价)")
    print("  次日收益 = 次交易日close_qfq / 当日close_qfq - 1")
    print("=" * 80)

    print("\nStep 1: Loading & merging data ...")
    df = build_features(start_date)

    print("\nStep 2: Computing factor flags ...")
    df = compute_factor_flags(df)

    print("\nStep 3: Analyzing combo signals ...")
    combo_results = analyze_combos(df)

    print("\nStep 4: Scanning signal strength ...")
    scan_signal_strength(df)

    print("\n" + "=" * 80)
    print("  DONE — All results saved to:", OUTPUT_DIR)
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="跨表多因子组合分析")
    parser.add_argument("--start", default="20240101", help="起始日期 YYYYMMDD")
    run_analysis(parser.parse_args().start)
