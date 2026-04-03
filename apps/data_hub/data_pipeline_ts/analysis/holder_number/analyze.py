"""
股东户数 + 技术因子 → 次日收益分析
=============================================
信号：
  1. 户数环比下降 + 均线多头 → 主力吸筹
  2. 户数骤增 + 高换手 → 散户涌入见顶
  3. 户数变化与技术面共振
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
    signal_stats,
    holding_period_returns,
    print_report,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data(start_date: str = "20230101") -> pd.DataFrame:
    """
    股东户数是季报/半年报数据，用 ann_date (公告日) 关联 factor_pro。
    """
    sql = """
    SELECT
        hn.ts_code,
        hn.ann_date,
        hn.end_date,
        hn.holder_num,
        fp.close,
        fp.close_qfq,
        fp.vol,
        fp.amount,
        fp.volume_ratio,
        fp.turnover_rate_f,
        fp.pct_chg,
        fp.total_mv,
        fp.circ_mv,
        fp.rsi_bfq_6,
        fp.rsi_bfq_12,
        fp.kdj_k_bfq,
        fp.kdj_d_bfq,
        fp.macd_dif_bfq,
        fp.macd_dea_bfq,
        fp.boll_upper_bfq,
        fp.boll_mid_bfq,
        fp.boll_lower_bfq,
        fp.bias1_bfq,
        fp.cci_bfq,
        fp.ma_bfq_5,
        fp.ma_bfq_20,
        fp.ma_bfq_60
    FROM stock_stk_holdernumber hn
    JOIN stock_stk_factor_pro fp
        ON hn.ts_code = fp.ts_code AND hn.ann_date = fp.trade_date
    WHERE hn.ann_date >= :start_date
      AND hn.holder_num > 0
    ORDER BY hn.ts_code, hn.end_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns={"ann_date": "trade_date"}, inplace=True)

    # 户数环比变化
    df = df.sort_values(["ts_code", "end_date"])
    df["prev_holder_num"] = df.groupby("ts_code")["holder_num"].shift(1)
    df["holder_num_chg"] = (df["holder_num"] / df["prev_holder_num"] - 1) * 100

    # Signal 1: 户数下降 + 均线多头
    df["sig_num_down_bull_ma"] = (
        (df["holder_num_chg"] < -5)
        & (df["ma_bfq_5"] > df["ma_bfq_20"])
        & (df["ma_bfq_20"] > df["ma_bfq_60"])
    )

    # Signal 2: 户数骤增 + 高换手
    df["sig_num_surge_high_turn"] = (
        (df["holder_num_chg"] > 20) & (df["turnover_rate_f"] > 5)
    )

    # Signal 3: 户数下降 + RSI中性 (未超买超卖)
    df["sig_num_down_rsi_neutral"] = (
        (df["holder_num_chg"] < -10)
        & (df["rsi_bfq_6"] > 30)
        & (df["rsi_bfq_6"] < 70)
    )

    # Signal 4: 户数增加 + 接近布林上轨
    df["sig_num_up_boll_upper"] = (
        (df["holder_num_chg"] > 10)
        & (df["close"] > df["boll_upper_bfq"] * 0.98)
    )

    # Signal 5: 户数大幅下降 + MACD金叉
    df["sig_num_big_drop_macd"] = (
        (df["holder_num_chg"] < -15)
        & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Next-day return
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20230101"):
    print("Loading holdernumber + factor_pro data ...")
    raw = load_data(start_date)
    print(f"  Rows loaded: {len(raw):,}")

    if raw.empty:
        print("No data found.")
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret", "holder_num_chg"])
    print(f"  Valid rows: {len(valid):,}")

    signals = {
        "户数下降+均线多头 (chg<-5% & MA5>MA20>MA60)": "sig_num_down_bull_ma",
        "户数骤增+高换手 (chg>20% & turn>5%)": "sig_num_surge_high_turn",
        "户数下降+RSI中性 (chg<-10% & 30<RSI<70)": "sig_num_down_rsi_neutral",
        "户数增加+布林上轨 (chg>10% & near upper)": "sig_num_up_boll_upper",
        "户数大幅下降+MACD金叉 (chg<-15%)": "sig_num_big_drop_macd",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    summary = pd.concat(all_stats, ignore_index=True)
    summary.to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

    # 户数变化分组
    bins = [-100, -20, -10, -5, 0, 5, 10, 20, 100]
    labels = ["<-20%", "-20~-10%", "-10~-5%", "-5~0%", "0~5%", "5~10%", "10~20%", ">20%"]
    valid["chg_bin"] = pd.cut(valid["holder_num_chg"], bins=bins, labels=labels)
    chg_stats = signal_stats(valid, "chg_bin", "next_ret")
    print_report("股东户数变化分组 → 次日收益", chg_stats)
    chg_stats.to_csv(OUTPUT_DIR / "holder_num_chg_buckets.csv")

    # Holding period returns
    for title, col in signals.items():
        triggered = valid[valid[col] == True][["ts_code", "trade_date"]].drop_duplicates()
        if len(triggered) < 5:
            continue
        codes = triggered["ts_code"].unique().tolist()
        placeholders = ",".join([f"'{c}'" for c in codes[:200]])
        price_sql = f"""
        SELECT ts_code, trade_date, close_qfq
        FROM stock_stk_factor_pro
        WHERE ts_code IN ({placeholders})
          AND trade_date >= :start_date
        ORDER BY ts_code, trade_date
        """
        prices = query_df(price_sql, {"start_date": start_date})
        hp = holding_period_returns(prices, triggered, periods=[1, 2, 3, 5])
        if hp.empty:
            continue
        avg = hp[[c for c in hp.columns if c.startswith("ret_")]].mean() * 100
        print(f"\n  [{title}] 平均持有收益(%):")
        for k, v in avg.items():
            print(f"    {k}: {v:.2f}%")
        hp.to_csv(OUTPUT_DIR / f"hp_{col}.csv", index=False)

    print("\nDone.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="股东户数信号分析")
    parser.add_argument("--start", default="20230101", help="起始日期 YYYYMMDD")
    args = parser.parse_args()
    run_analysis(args.start)
