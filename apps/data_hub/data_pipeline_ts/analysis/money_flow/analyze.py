"""
个股资金流向 + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价), 次日收益 = 次日close_qfq / 当日close_qfq - 1

信号:
  1. 超大单净流入 + 放量
  2. 主力净流出 + 缩量 (大单+超大单净卖出)
  3. 资金流向反转 (前日净流出今日净流入)
  4. 净流入金额分组
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
        mf.ts_code, mf.trade_date,
        mf.buy_elg_amount, mf.sell_elg_amount,
        mf.buy_lg_amount, mf.sell_lg_amount,
        mf.buy_md_amount, mf.sell_md_amount,
        mf.buy_sm_amount, mf.sell_sm_amount,
        mf.net_mf_vol, mf.net_mf_amount,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6, fp.kdj_k_bfq, fp.kdj_d_bfq,
        fp.boll_upper_bfq, fp.boll_lower_bfq, fp.bias1_bfq
    FROM stock_money_flow mf
    JOIN stock_stk_factor_pro fp
        ON mf.ts_code = fp.ts_code AND mf.trade_date = fp.trade_date
    WHERE mf.trade_date >= :start_date
    ORDER BY mf.ts_code, mf.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 主力资金 = 超大单 + 大单
    df["main_net"] = (df["buy_elg_amount"] + df["buy_lg_amount"]
                      - df["sell_elg_amount"] - df["sell_lg_amount"])
    df["elg_net"] = df["buy_elg_amount"] - df["sell_elg_amount"]
    # 主力净流入占成交额比例
    df["main_net_pct"] = df["main_net"] / df["amount"] * 100

    # 前日主力净流入
    df = df.sort_values(["ts_code", "trade_date"])
    df["prev_main_net"] = df.groupby("ts_code")["main_net"].shift(1)
    df["prev_elg_net"] = df.groupby("ts_code")["elg_net"].shift(1)

    # Signal 1: 超大单净流入 + 放量
    df["sig_elg_inflow_vol"] = (df["elg_net"] > 0) & (df["volume_ratio"] > 1.5)

    # Signal 2: 主力净流出 + 缩量
    df["sig_main_outflow_shrink"] = (df["main_net"] < 0) & (df["volume_ratio"] < 0.8)

    # Signal 3: 资金流向反转 (前日主力净流出 → 今日净流入)
    df["sig_flow_reversal_bull"] = (df["prev_main_net"] < 0) & (df["main_net"] > 0)

    # Signal 4: 连续超大单流入 + MACD多头
    df["sig_elg_streak_macd"] = (
        (df["elg_net"] > 0) & (df["prev_elg_net"] > 0)
        & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Signal 5: 主力大幅流出 + RSI超卖 (抄底)
    df["sig_main_dump_rsi_low"] = (
        (df["main_net_pct"] < -10) & (df["rsi_bfq_6"] < 30)
    )

    # Signal 6: 主力大幅流入 + 近布林上轨 (追高风险)
    df["sig_main_surge_boll_high"] = (
        (df["main_net_pct"] > 10)
        & (df["close"] > df["boll_upper_bfq"] * 0.98)
    )

    # Next-day return
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading money_flow + factor_pro ...")
    raw = load_data(start_date)
    print(f"  Rows: {len(raw):,}")
    if raw.empty:
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    signals = {
        "超大单净流入+放量 (elg_net>0 & vol_ratio>1.5)": "sig_elg_inflow_vol",
        "主力净流出+缩量 (main<0 & vol_ratio<0.8)": "sig_main_outflow_shrink",
        "资金流向反转 (昨流出今流入)": "sig_flow_reversal_bull",
        "连续超大单流入+MACD多头": "sig_elg_streak_macd",
        "主力大幅流出+RSI超卖 (pct<-10% & RSI<30)": "sig_main_dump_rsi_low",
        "主力大幅流入+近布林上轨": "sig_main_surge_boll_high",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    summary = pd.concat(all_stats, ignore_index=True)
    summary.to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

    # 主力净流入占比分组
    bins = [-100, -20, -10, -5, 0, 5, 10, 20, 100]
    labels = ["<-20%", "-20~-10%", "-10~-5%", "-5~0%", "0~5%", "5~10%", "10~20%", ">20%"]
    valid = valid.copy()
    valid["main_net_bin"] = pd.cut(valid["main_net_pct"], bins=bins, labels=labels)
    mf_stats = signal_stats(valid, "main_net_bin", "next_ret")
    print_report("主力净流入占比分组 → 次日收益", mf_stats)
    mf_stats.to_csv(OUTPUT_DIR / "main_net_pct_buckets.csv")

    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
