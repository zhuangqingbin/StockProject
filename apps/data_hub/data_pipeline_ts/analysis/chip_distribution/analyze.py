"""
每日筹码及胜率 + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价)

cyq_perf 字段:
  winner_rate: 获利比例
  cost_5pct/cost_95pct: 筹码5%/95%分位成本
  weight_avg: 加权平均成本

信号:
  1. 极低获利比例 + 放量 (恐慌盘出清)
  2. 极高获利比例 + 缩量 (获利盘锁仓)
  3. 股价突破95%成本线
  4. 获利比例急剧变化
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
        cp.ts_code, cp.trade_date,
        cp.winner_rate, cp.cost_5pct, cp.cost_15pct,
        cp.cost_50pct, cp.cost_85pct, cp.cost_95pct,
        cp.weight_avg,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6, fp.kdj_k_bfq, fp.kdj_d_bfq,
        fp.boll_upper_bfq, fp.boll_lower_bfq
    FROM stock_cyq_perf cp
    JOIN stock_stk_factor_pro fp
        ON cp.ts_code = fp.ts_code AND cp.trade_date = fp.trade_date
    WHERE cp.trade_date >= :start_date
    ORDER BY cp.ts_code, cp.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(["ts_code", "trade_date"])

    # 获利比例变化
    df["prev_winner"] = df.groupby("ts_code")["winner_rate"].shift(1)
    df["winner_chg"] = df["winner_rate"] - df["prev_winner"]

    # 筹码集中度 (95%-5% 区间越窄越集中)
    df["chip_spread"] = df["cost_95pct"] - df["cost_5pct"]
    df["chip_spread_pct"] = df["chip_spread"] / df["weight_avg"] * 100

    # Signal 1: 极低获利比例 + 放量 (恐慌出清 → 反弹)
    df["sig_low_winner_vol"] = (df["winner_rate"] < 5) & (df["volume_ratio"] > 1.5)

    # Signal 2: 极高获利比例 + 缩量 (锁仓惜售)
    df["sig_high_winner_shrink"] = (df["winner_rate"] > 90) & (df["volume_ratio"] < 0.8)

    # Signal 3: 股价突破95%成本线 + MACD多头
    df["sig_break_cost95_macd"] = (
        (df["close"] > df["cost_95pct"])
        & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Signal 4: 获利比例急剧上升 (>20pp) + 放量
    df["sig_winner_surge_vol"] = (df["winner_chg"] > 20) & (df["volume_ratio"] > 1.5)

    # Signal 5: 获利比例急剧下降 + RSI超卖
    df["sig_winner_crash_rsi"] = (df["winner_chg"] < -20) & (df["rsi_bfq_6"] < 30)

    # Signal 6: 筹码高度集中 + 均线金叉信号
    df["sig_chip_tight_macd"] = (
        (df["chip_spread_pct"] < 15)
        & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
        & (df["winner_rate"] > 50)
    )

    # Next-day return
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading cyq_perf + factor_pro ...")
    raw = load_data(start_date)
    print(f"  Rows: {len(raw):,}")
    if raw.empty:
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    signals = {
        "极低获利比例+放量 (winner<5% & vol>1.5)": "sig_low_winner_vol",
        "极高获利比例+缩量 (winner>90% & vol<0.8)": "sig_high_winner_shrink",
        "突破95%成本线+MACD多头": "sig_break_cost95_macd",
        "获利比例急升+放量 (chg>20pp & vol>1.5)": "sig_winner_surge_vol",
        "获利比例急降+RSI超卖 (chg<-20pp & RSI<30)": "sig_winner_crash_rsi",
        "筹码集中+MACD多头 (spread<15% & winner>50%)": "sig_chip_tight_macd",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    pd.concat(all_stats, ignore_index=True).to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

    # 获利比例分组
    valid = valid.copy()
    bins = [0, 5, 15, 30, 50, 70, 85, 95, 100]
    labels = ["0~5%", "5~15%", "15~30%", "30~50%", "50~70%", "70~85%", "85~95%", "95~100%"]
    valid["winner_bin"] = pd.cut(valid["winner_rate"], bins=bins, labels=labels)
    w_stats = signal_stats(valid, "winner_bin", "next_ret")
    print_report("获利比例分组 → 次日收益", w_stats)
    w_stats.to_csv(OUTPUT_DIR / "winner_rate_buckets.csv")

    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
