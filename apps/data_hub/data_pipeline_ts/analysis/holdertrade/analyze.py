"""
股东增减持 + 技术因子 → 次日收益分析
=============================================
信号：
  1. 高管减持 + KDJ死叉
  2. 大股东增持 + 底部形态 (close 接近 boll_lower + CCI < -100)
  3. 减持比例大 + 放量
  4. 增减持类型分组 → 次日收益
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
    Join holdertrade with factor_pro on (ts_code, ann_date = trade_date).
    Use ann_date as the signal date since that's when the market learns about it.
    """
    sql = """
    SELECT
        ht.ts_code,
        ht.ann_date,
        ht.holder_name,
        ht.holder_type,
        ht.in_de,
        ht.change_vol,
        ht.change_ratio,
        ht.after_share,
        ht.after_ratio,
        ht.avg_price,
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
    FROM stock_stk_holdertrade ht
    JOIN stock_stk_factor_pro fp
        ON ht.ts_code = fp.ts_code AND ht.ann_date = fp.trade_date
    WHERE ht.ann_date >= :start_date
      AND ht.in_de IN ('IN', 'DE')
    ORDER BY ht.ts_code, ht.ann_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns={"ann_date": "trade_date"}, inplace=True)

    is_de = df["in_de"] == "DE"
    is_in = df["in_de"] == "IN"

    # Signal 1: 高管减持 + KDJ死叉
    df["sig_exec_sell_kdj_death"] = (
        is_de
        & (df["holder_type"] == "G")
        & (df["kdj_k_bfq"] < df["kdj_d_bfq"])
    )

    # Signal 2: 增持 + 底部形态
    df["sig_buy_bottom"] = (
        is_in
        & (df["close"] < df["boll_lower_bfq"] * 1.02)
        & (df["cci_bfq"] < -100)
    )

    # Signal 3: 减持比例大 + 放量
    df["sig_big_sell_high_vol"] = (
        is_de
        & (df["change_ratio"].abs() > 1)
        & (df["volume_ratio"] > 2)
    )

    # Signal 4: 增持 + MACD金叉
    df["sig_buy_macd_golden"] = (
        is_in & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
    )

    # Signal 5: 减持 + RSI超买
    df["sig_sell_rsi_overbought"] = (
        is_de & (df["rsi_bfq_6"] > 70)
    )

    # Next-day return
    # Deduplicate: one stock may have multiple holder events on same date
    # Keep aggregated view per (ts_code, trade_date)
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading holdertrade + factor_pro data ...")
    raw = load_data(start_date)
    print(f"  Rows loaded: {len(raw):,}")

    if raw.empty:
        print("No data found.")
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid rows: {len(valid):,}")

    # 基础统计: 增持 vs 减持
    in_de_stats = signal_stats(valid, "in_de", "next_ret")
    print_report("增持(IN) vs 减持(DE) → 次日收益", in_de_stats)
    in_de_stats.to_csv(OUTPUT_DIR / "in_de_basic.csv")

    # 股东类型 × 增减持
    valid["type_inde"] = valid["holder_type"] + "_" + valid["in_de"]
    type_stats = signal_stats(valid, "type_inde", "next_ret")
    print_report("股东类型×增减持 → 次日收益", type_stats)
    type_stats.to_csv(OUTPUT_DIR / "holder_type_inde.csv")

    signals = {
        "高管减持+KDJ死叉": "sig_exec_sell_kdj_death",
        "增持+底部形态 (near boll_lower & CCI<-100)": "sig_buy_bottom",
        "大比例减持+放量 (ratio>1% & vol_ratio>2)": "sig_big_sell_high_vol",
        "增持+MACD金叉": "sig_buy_macd_golden",
        "减持+RSI超买 (RSI6>70)": "sig_sell_rsi_overbought",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    summary = pd.concat(all_stats, ignore_index=True)
    summary.to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)

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

    parser = argparse.ArgumentParser(description="股东增减持信号分析")
    parser.add_argument("--start", default="20240101", help="起始日期 YYYYMMDD")
    args = parser.parse_args()
    run_analysis(args.start)
