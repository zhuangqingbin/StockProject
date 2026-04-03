"""
大宗交易 + 技术因子 → 次日收益分析
=============================================
信号：
  1. 折价大宗 (block price / close < 0.95) + 放量 (volume_ratio > 1.5)
  2. 溢价大宗 (block price / close > 1.0) + MACD金叉
  3. 大宗成交额占比高 + 低换手率
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
    """Join block_trade with stk_factor_pro on (ts_code, trade_date)."""
    sql = """
    SELECT
        bt.ts_code,
        bt.trade_date,
        bt.price   AS block_price,
        bt.vol     AS block_vol,
        bt.amount  AS block_amount,
        bt.buyer,
        bt.seller,
        fp.close,
        fp.close_qfq,
        fp.vol           AS market_vol,
        fp.amount        AS market_amount,
        fp.volume_ratio,
        fp.turnover_rate_f,
        fp.pct_chg,
        fp.pe_ttm,
        fp.pb,
        fp.total_mv,
        fp.circ_mv,
        fp.macd_dif_bfq,
        fp.macd_dea_bfq,
        fp.macd_bfq,
        fp.rsi_bfq_6,
        fp.rsi_bfq_12,
        fp.kdj_k_bfq,
        fp.kdj_d_bfq,
        fp.boll_upper_bfq,
        fp.boll_mid_bfq,
        fp.boll_lower_bfq,
        fp.bias1_bfq,
        fp.cci_bfq
    FROM stock_block_trade bt
    JOIN stock_stk_factor_pro fp
        ON bt.ts_code = fp.ts_code AND bt.trade_date = fp.trade_date
    WHERE bt.trade_date >= :start_date
    ORDER BY bt.ts_code, bt.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Derive signal columns."""
    df = df.copy()

    # 折溢价率
    df["premium_rate"] = df["block_price"] / df["close"] - 1

    # 大宗成交额占当日成交额比例 (block_amount 单位万元, market_amount 单位千元)
    df["block_pct"] = df["block_amount"] / (df["market_amount"] / 10) * 100

    # Signal 1: 深度折价 + 放量
    df["sig_discount_vol"] = (df["premium_rate"] < -0.05) & (df["volume_ratio"] > 1.5)

    # Signal 2: 溢价 + MACD金叉 (dif > dea 且 dif 前一日 < dea → 简化为 dif > dea)
    df["sig_premium_macd"] = (df["premium_rate"] > 0) & (
        df["macd_dif_bfq"] > df["macd_dea_bfq"]
    )

    # Signal 3: 大宗占比高 + 低换手
    df["sig_high_block_low_turn"] = (df["block_pct"] > 5) & (
        df["turnover_rate_f"] < 3
    )

    # Signal 4: 折价 + RSI超卖
    df["sig_discount_rsi_oversold"] = (df["premium_rate"] < -0.03) & (
        df["rsi_bfq_6"] < 30
    )

    # Signal 5: 溢价 + 接近布林上轨
    df["sig_premium_boll_upper"] = (df["premium_rate"] > 0) & (
        df["close"] > df["boll_upper_bfq"] * 0.98
    )

    # Next-day return (forward)
    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    return df


def run_analysis(start_date: str = "20240101"):
    print("Loading block_trade + factor_pro data ...")
    raw = load_data(start_date)
    print(f"  Rows loaded: {len(raw):,}")

    if raw.empty:
        print("No data found. Check date range or database.")
        return

    df = compute_signals(raw)
    valid = df.dropna(subset=["next_ret"])
    print(f"  Valid rows (with next-day return): {len(valid):,}")

    # ---- per-signal stats ----
    signals = {
        "折价放量 (discount<-5% & vol_ratio>1.5)": "sig_discount_vol",
        "溢价+MACD金叉": "sig_premium_macd",
        "大宗占比高+低换手 (block>5% & turn<3%)": "sig_high_block_low_turn",
        "折价+RSI超卖 (discount<-3% & RSI6<30)": "sig_discount_rsi_oversold",
        "溢价+接近布林上轨": "sig_premium_boll_upper",
    }

    all_stats = []
    for title, col in signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    summary = pd.concat(all_stats, ignore_index=True)
    summary.to_csv(OUTPUT_DIR / "signal_summary.csv", index=False)
    print(f"Summary saved to {OUTPUT_DIR / 'signal_summary.csv'}")

    # ---- holding period returns for top signals ----
    for title, col in signals.items():
        triggered = valid[valid[col] == True][["ts_code", "trade_date"]].copy()
        if len(triggered) < 5:
            continue
        # Load full price data for holding period calc
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

    # ---- 折溢价率分布 ----
    bins = [-1, -0.1, -0.05, -0.02, 0, 0.02, 0.05, 0.1, 1]
    labels = ["<-10%", "-10~-5%", "-5~-2%", "-2~0%", "0~2%", "2~5%", "5~10%", ">10%"]
    valid["premium_bin"] = pd.cut(valid["premium_rate"], bins=bins, labels=labels)
    premium_stats = signal_stats(valid, "premium_bin", "next_ret")
    print_report("大宗折溢价率分组 → 次日收益", premium_stats)
    premium_stats.to_csv(OUTPUT_DIR / "premium_rate_buckets.csv")

    print("\nDone.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="大宗交易信号分析")
    parser.add_argument("--start", default="20240101", help="起始日期 YYYYMMDD")
    args = parser.parse_args()
    run_analysis(args.start)
