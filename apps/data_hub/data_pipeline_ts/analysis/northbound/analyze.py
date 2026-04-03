"""
沪深股通持股(北向资金) + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价)

信号:
  1. 北向持股比例大幅增加 + MACD多头
  2. 北向持股比例下降 + 高位
  3. 北向高持仓 + 底部形态
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
        hk.ts_code, hk.trade_date,
        hk.vol AS hk_vol, hk.ratio AS hk_ratio,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6, fp.kdj_k_bfq, fp.kdj_d_bfq,
        fp.boll_upper_bfq, fp.boll_lower_bfq,
        fp.ma_bfq_5, fp.ma_bfq_20, fp.ma_bfq_60
    FROM stock_hk_hold hk
    JOIN stock_stk_factor_pro fp
        ON hk.ts_code = fp.ts_code AND hk.trade_date = fp.trade_date
    WHERE hk.trade_date >= :start_date
      AND hk.ratio IS NOT NULL AND hk.ratio > 0
    ORDER BY hk.ts_code, hk.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(["ts_code", "trade_date"])

    # 持股比例变化
    df["prev_ratio"] = df.groupby("ts_code")["hk_ratio"].shift(1)
    df["ratio_chg"] = df["hk_ratio"] - df["prev_ratio"]
    df["ratio_chg_pct"] = (df["hk_ratio"] / df["prev_ratio"] - 1) * 100

    # Signal 1: 北向大幅加仓 + MACD多头
    df["sig_nb_add_macd"] = (
        (df["ratio_chg"] > 0.3) & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Signal 2: 北向减仓 + 高位
    df["sig_nb_reduce_high"] = (
        (df["ratio_chg"] < -0.2)
        & (df["close"] > df["boll_upper_bfq"] * 0.95)
    )

    # Signal 3: 北向高持仓 + 底部 (ratio > 5% & near boll_lower)
    df["sig_nb_high_hold_bottom"] = (
        (df["hk_ratio"] > 5)
        & (df["close"] < df["boll_lower_bfq"] * 1.02)
    )

    # Signal 4: 北向连续加仓 + 均线多头
    df["prev_ratio_chg"] = df.groupby("ts_code")["ratio_chg"].shift(1)
    df["sig_nb_streak_add_bull"] = (
        (df["ratio_chg"] > 0.1) & (df["prev_ratio_chg"] > 0.1)
        & (df["ma_bfq_5"] > df["ma_bfq_20"])
    )

    # Signal 5: 北向大幅减仓 + 放量 (机构出逃)
    df["sig_nb_dump_vol"] = (
        (df["ratio_chg"] < -0.5) & (df["volume_ratio"] > 2)
    )

    # Next-day return
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading hk_hold + factor_pro ...")
    raw = load_data(start_date)
    print(f"  Rows: {len(raw):,}")
    if raw.empty:
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    signals = {
        "北向大幅加仓+MACD多头 (chg>0.3pp)": "sig_nb_add_macd",
        "北向减仓+高位 (chg<-0.2pp & near upper)": "sig_nb_reduce_high",
        "北向高持仓+底部 (ratio>5% & near lower)": "sig_nb_high_hold_bottom",
        "北向连续加仓+均线多头": "sig_nb_streak_add_bull",
        "北向大幅减仓+放量 (chg<-0.5pp & vol>2)": "sig_nb_dump_vol",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    pd.concat(all_stats, ignore_index=True).to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

    # 持股比例变化分组
    valid = valid.copy()
    bins = [-100, -1, -0.3, -0.1, 0, 0.1, 0.3, 1, 100]
    labels = ["<-1pp", "-1~-0.3", "-0.3~-0.1", "-0.1~0", "0~0.1", "0.1~0.3", "0.3~1", ">1pp"]
    valid["ratio_chg_bin"] = pd.cut(valid["ratio_chg"], bins=bins, labels=labels)
    rc_stats = signal_stats(valid, "ratio_chg_bin", "next_ret")
    print_report("北向持股比例变化分组 → 次日收益", rc_stats)
    rc_stats.to_csv(OUTPUT_DIR / "ratio_chg_buckets.csv")

    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
