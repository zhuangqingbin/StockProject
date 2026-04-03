"""
融资融券明细 + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价)

信号:
  1. 融资余额大幅增加 + 放量 (杠杆做多)
  2. 融券余量增加 + 高位 (做空信号)
  3. 融资买入占比异常高
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


def load_data(start_date: str = "20240101") -> pd.DataFrame:
    sql = """
    SELECT
        md.ts_code, md.trade_date,
        md.rzye, md.rqye, md.rzmre, md.rzche, md.rqyl, md.rqchl, md.rzrqye,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6, fp.kdj_k_bfq, fp.kdj_d_bfq,
        fp.boll_upper_bfq, fp.boll_lower_bfq
    FROM stock_margin_detail md
    JOIN stock_stk_factor_pro fp
        ON md.ts_code = fp.ts_code AND md.trade_date = fp.trade_date
    WHERE md.trade_date >= :start_date
    ORDER BY md.ts_code, md.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(["ts_code", "trade_date"])

    # 融资余额变化率
    df["prev_rzye"] = df.groupby("ts_code")["rzye"].shift(1)
    df["rzye_chg"] = (df["rzye"] / df["prev_rzye"] - 1) * 100

    # 融资买入占成交额比例 (rzmre: 融资买入额, amount: 成交额千元)
    df["rzmre_pct"] = df["rzmre"] / (df["amount"] / 10) * 100

    # 融券余量变化
    df["prev_rqyl"] = df.groupby("ts_code")["rqyl"].shift(1)
    df["rqyl_chg"] = (df["rqyl"] / df["prev_rqyl"].replace(0, np.nan) - 1) * 100

    # Signal 1: 融资余额大幅增加 + 放量
    df["sig_rz_surge_vol"] = (df["rzye_chg"] > 5) & (df["volume_ratio"] > 1.5)

    # Signal 2: 融券余量大幅增加 + 高位
    df["sig_rq_surge_high"] = (
        (df["rqyl_chg"] > 20) & (df["close"] > df["boll_upper_bfq"] * 0.95)
    )

    # Signal 3: 融资买入占比超高 + MACD多头
    df["sig_rz_buy_heavy_macd"] = (
        (df["rzmre_pct"] > 15) & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Signal 4: 融资净偿还(rzche > rzmre) + RSI超卖
    df["sig_rz_repay_rsi_low"] = (
        (df["rzche"] > df["rzmre"]) & (df["rsi_bfq_6"] < 30)
    )

    # Signal 5: 融资余额持续增长 (连续2日)
    df["prev_rzye_chg"] = df.groupby("ts_code")["rzye_chg"].shift(1)
    df["sig_rz_streak_up"] = (df["rzye_chg"] > 3) & (df["prev_rzye_chg"] > 3)

    # Next-day return
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading margin_detail + factor_pro ...")
    raw = load_data(start_date)
    print(f"  Rows: {len(raw):,}")
    if raw.empty:
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    signals = {
        "融资余额大增+放量 (rzye_chg>5% & vol_ratio>1.5)": "sig_rz_surge_vol",
        "融券余量大增+高位 (rqyl_chg>20% & near boll_upper)": "sig_rq_surge_high",
        "融资买入占比高+MACD多头 (rzmre>15%)": "sig_rz_buy_heavy_macd",
        "融资净偿还+RSI超卖": "sig_rz_repay_rsi_low",
        "融资连续增长 (连续2日>3%)": "sig_rz_streak_up",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    pd.concat(all_stats, ignore_index=True).to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)
    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
