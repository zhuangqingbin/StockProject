"""
限售股解禁 + 技术因子 → 次日/多日收益分析
=============================================
信号：
  1. 大比例解禁 (float_ratio > 5%) + 高位 (close 接近 boll_upper)
  2. 解禁前缩量 (volume_ratio < 0.8)
  3. 解禁 + RSI超买 (rsi_6 > 80)
  4. 解禁比例分组 → 次日收益
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


def load_data(start_date: str = "20240101") -> pd.DataFrame:
    """
    Join share_float events with factor_pro on float_date = trade_date.
    One stock may have multiple unlock events on same day → aggregate first.
    """
    sql = """
    SELECT
        sf.ts_code,
        sf.float_date,
        sf.ann_date,
        SUM(sf.float_share) AS total_float_share,
        MAX(sf.float_ratio) AS max_float_ratio,
        COUNT(*)             AS unlock_count,
        fp.close,
        fp.close_qfq,
        fp.vol,
        fp.amount,
        fp.volume_ratio,
        fp.turnover_rate_f,
        fp.pct_chg,
        fp.total_mv,
        fp.circ_mv,
        fp.total_share,
        fp.float_share AS fp_float_share,
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
    FROM stock_share_float sf
    JOIN stock_stk_factor_pro fp
        ON sf.ts_code = fp.ts_code AND sf.float_date = fp.trade_date
    WHERE sf.float_date >= :start_date
      AND sf.float_share > 0
    GROUP BY sf.ts_code, sf.float_date, sf.ann_date,
             fp.close, fp.close_qfq, fp.vol, fp.amount,
             fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
             fp.total_mv, fp.circ_mv, fp.total_share, fp.float_share,
             fp.rsi_bfq_6, fp.rsi_bfq_12, fp.kdj_k_bfq, fp.kdj_d_bfq,
             fp.macd_dif_bfq, fp.macd_dea_bfq,
             fp.boll_upper_bfq, fp.boll_mid_bfq, fp.boll_lower_bfq,
             fp.bias1_bfq, fp.cci_bfq, fp.ma_bfq_5, fp.ma_bfq_20, fp.ma_bfq_60
    ORDER BY sf.ts_code, sf.float_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns={"float_date": "trade_date"}, inplace=True)

    # 解禁占总股本比例 (total_float_share 单位: 股, total_share 单位: 万股)
    df["unlock_ratio_pct"] = df["total_float_share"] / (df["total_share"] * 10000) * 100

    # Signal 1: 大比例解禁 + 高位
    df["sig_big_unlock_high"] = (df["unlock_ratio_pct"] > 5) & (
        df["close"] > df["boll_upper_bfq"] * 0.98
    )

    # Signal 2: 解禁 + 缩量
    df["sig_unlock_shrink_vol"] = (df["unlock_ratio_pct"] > 1) & (
        df["volume_ratio"] < 0.8
    )

    # Signal 3: 解禁 + RSI超买
    df["sig_unlock_rsi_overbought"] = (df["unlock_ratio_pct"] > 1) & (
        df["rsi_bfq_6"] > 80
    )

    # Signal 4: 解禁 + 均线空头 (ma5 < ma20 < ma60)
    df["sig_unlock_bearish_ma"] = (df["unlock_ratio_pct"] > 2) & (
        (df["ma_bfq_5"] < df["ma_bfq_20"]) & (df["ma_bfq_20"] < df["ma_bfq_60"])
    )

    # Signal 5: 小比例解禁 + MACD多头
    df["sig_small_unlock_bullish"] = (df["unlock_ratio_pct"] < 1) & (
        df["macd_dif_bfq"] > df["macd_dea_bfq"]
    )

    # Next-day return
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading share_float + factor_pro data ...")
    raw = load_data(start_date)
    print(f"  Rows loaded: {len(raw):,}")

    if raw.empty:
        print("No data found.")
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid rows: {len(valid):,}")

    signals = {
        "大比例解禁+高位 (unlock>5% & near boll_upper)": "sig_big_unlock_high",
        "解禁+缩量 (unlock>1% & vol_ratio<0.8)": "sig_unlock_shrink_vol",
        "解禁+RSI超买 (unlock>1% & RSI6>80)": "sig_unlock_rsi_overbought",
        "解禁+均线空头 (unlock>2% & MA5<MA20<MA60)": "sig_unlock_bearish_ma",
        "小比例解禁+MACD多头 (unlock<1% & DIF>DEA)": "sig_small_unlock_bullish",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    summary = pd.concat(all_stats, ignore_index=True)
    summary.to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

    # 解禁比例分组
    bins = [0, 0.5, 1, 2, 5, 10, 100]
    labels = ["0~0.5%", "0.5~1%", "1~2%", "2~5%", "5~10%", ">10%"]
    valid["unlock_bin"] = pd.cut(valid["unlock_ratio_pct"], bins=bins, labels=labels)
    unlock_stats = signal_stats(valid, "unlock_bin", "next_ret")
    print_report("解禁比例分组 → 次日收益", unlock_stats)
    unlock_stats.to_csv(OUTPUT_DIR / "unlock_ratio_buckets.csv")

    # Holding period returns for bearish signals
    for title, col in signals.items():
        triggered = valid[valid[col] == True][["ts_code", "trade_date"]].copy()
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

    parser = argparse.ArgumentParser(description="限售解禁信号分析")
    parser.add_argument("--start", default="20240101", help="起始日期 YYYYMMDD")
    args = parser.parse_args()
    run_analysis(args.start)
