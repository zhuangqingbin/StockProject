"""
业绩预告/快报 + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价)

forecast_vip: type=预增/预减/略增/略减/扭亏/首亏/续亏/续盈, p_change_min/max=预计变动幅度
express_vip: yoy_net_profit=净利润同比, diluted_roe=ROE
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


def analyze_forecast(start_date: str):
    print("=== 业绩预告分析 ===")
    sql = """
    SELECT
        fv.ts_code, fv.ann_date, fv.end_date,
        fv.type, fv.p_change_min, fv.p_change_max,
        fv.net_profit_min, fv.net_profit_max,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6, fp.boll_upper_bfq, fp.boll_lower_bfq
    FROM stock_forecast_vip fv
    JOIN stock_stk_factor_pro fp
        ON fv.ts_code = fp.ts_code AND fv.ann_date = fp.trade_date
    WHERE fv.ann_date >= :start_date
    ORDER BY fv.ts_code, fv.ann_date
    """
    df = query_df(sql, {"start_date": start_date})
    print(f"  Rows: {len(df):,}")
    if df.empty:
        return

    df.rename(columns={"ann_date": "trade_date"}, inplace=True)
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    # 按预告类型分组
    type_stats = signal_stats(valid, "type", "next_ret")
    print_report("业绩预告类型 → 次日收益", type_stats)
    type_stats.to_csv(OUTPUT_DIR / "forecast_type.csv")

    # 预计变动幅度中值
    valid = valid.copy()
    valid["p_change_mid"] = (valid["p_change_min"].fillna(0) + valid["p_change_max"].fillna(0)) / 2

    # Signal: 预增 + 高变动 + MACD多头
    valid["sig_yuzeng_high_macd"] = (
        (valid["type"] == "预增")
        & (valid["p_change_mid"] > 100)
        & (valid["macd_dif_bfq"] > valid["macd_dea_bfq"])
    )
    # Signal: 首亏/续亏 + 高位
    valid["sig_loss_high"] = (
        valid["type"].isin(["首亏", "续亏"])
        & (valid["close"] > valid["boll_upper_bfq"] * 0.95)
    )
    # Signal: 扭亏 + RSI低位
    valid["sig_turnaround_rsi_low"] = (
        (valid["type"] == "扭亏") & (valid["rsi_bfq_6"] < 50)
    )
    # Signal: 预增/略增 + 超预期 (p_change > 200%)
    valid["sig_super_beat"] = (
        valid["type"].isin(["预增"]) & (valid["p_change_mid"] > 200)
    )

    fc_signals = {
        "预增+高变动+MACD多头 (chg>100%)": "sig_yuzeng_high_macd",
        "首亏/续亏+高位": "sig_loss_high",
        "扭亏+RSI低位": "sig_turnaround_rsi_low",
        "超预期预增 (chg>200%)": "sig_super_beat",
    }

    all_stats = []
    for title, col in fc_signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    pd.concat(all_stats, ignore_index=True).to_csv(OUTPUT_DIR / "forecast_signals.csv", index=False)


def analyze_express(start_date: str):
    print("\n=== 业绩快报分析 ===")
    sql = """
    SELECT
        ev.ts_code, ev.ann_date, ev.end_date,
        ev.yoy_net_profit, ev.yoy_sales, ev.diluted_roe, ev.diluted_eps,
        ev.revenue, ev.n_income,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq, fp.rsi_bfq_6
    FROM stock_express_vip ev
    JOIN stock_stk_factor_pro fp
        ON ev.ts_code = fp.ts_code AND ev.ann_date = fp.trade_date
    WHERE ev.ann_date >= :start_date
    ORDER BY ev.ts_code, ev.ann_date
    """
    df = query_df(sql, {"start_date": start_date})
    print(f"  Rows: {len(df):,}")
    if df.empty:
        return

    df.rename(columns={"ann_date": "trade_date"}, inplace=True)
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    # 净利润同比分组
    valid = valid.copy()
    bins = [-10000, -50, -20, 0, 20, 50, 100, 200, 10000]
    labels = ["<-50%", "-50~-20%", "-20~0%", "0~20%", "20~50%", "50~100%", "100~200%", ">200%"]
    valid["yoy_bin"] = pd.cut(valid["yoy_net_profit"], bins=bins, labels=labels)
    yoy_stats = signal_stats(valid, "yoy_bin", "next_ret")
    print_report("净利润同比分组 → 次日收益", yoy_stats)
    yoy_stats.to_csv(OUTPUT_DIR / "express_yoy_buckets.csv")


def run_analysis(start_date: str = "20240101"):
    analyze_forecast(start_date)
    analyze_express(start_date)
    print("\nAll done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
