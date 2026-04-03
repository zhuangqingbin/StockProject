"""
涨跌停统计 + 龙虎榜 + 技术因子 → 次日收益分析
=============================================
价格字段: close_qfq (前复权收盘价)

涨跌停(limit_list_d): limit=U涨停/D跌停, open_times开板次数, fd_amount封单金额
龙虎榜(top_list): net_amount净买入, l_buy买入总额
龙虎榜机构(top_inst): side买卖方向, net_buy机构净买入
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


def load_limit_data(start_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        ld.ts_code, ld.trade_date,
        ld.limit, ld.open_times, ld.fd_amount, ld.limit_times,
        ld.up_stat, ld.first_time, ld.last_time,
        ld.float_mv, ld.turnover_ratio,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq,
        fp.rsi_bfq_6
    FROM stock_limit_list_d ld
    JOIN stock_stk_factor_pro fp
        ON ld.ts_code = fp.ts_code AND ld.trade_date = fp.trade_date
    WHERE ld.trade_date >= :start_date
    ORDER BY ld.ts_code, ld.trade_date
    """
    return query_df(sql, {"start_date": start_date})


def load_toplist_data(start_date: str) -> pd.DataFrame:
    """龙虎榜 + 机构明细 聚合到 (ts_code, trade_date) 级别"""
    # 龙虎榜汇总
    sql_top = """
    SELECT
        tl.ts_code, tl.trade_date,
        SUM(tl.net_amount) AS tl_net_amount,
        SUM(tl.l_buy) AS tl_buy,
        SUM(tl.l_sell) AS tl_sell,
        MAX(tl.reason) AS tl_reason
    FROM stock_top_list tl
    WHERE tl.trade_date >= :start_date
    GROUP BY tl.ts_code, tl.trade_date
    """
    # 机构净买入汇总
    sql_inst = """
    SELECT
        ti.ts_code, ti.trade_date,
        SUM(CASE WHEN ti.side = '0' THEN ti.buy ELSE 0 END) AS inst_buy,
        SUM(CASE WHEN ti.side = '1' THEN ti.sell ELSE 0 END) AS inst_sell,
        SUM(ti.net_buy) AS inst_net_buy,
        COUNT(*) AS inst_count
    FROM stock_top_inst ti
    WHERE ti.trade_date >= :start_date
    GROUP BY ti.ts_code, ti.trade_date
    """
    tl = query_df(sql_top, {"start_date": start_date})
    ti = query_df(sql_inst, {"start_date": start_date})

    merged = pd.merge(tl, ti, on=["ts_code", "trade_date"], how="left")
    return merged


def analyze_limit(start_date: str):
    print("=== 涨跌停分析 ===")
    print("Loading limit_list_d + factor_pro ...")
    df = load_limit_data(start_date)
    print(f"  Rows: {len(df):,}")
    if df.empty:
        return

    df = df.sort_values(["ts_code", "trade_date"])
    df["next_close_qfq"] = df.groupby("ts_code")["close_qfq"].shift(-1)
    df["next_ret"] = df["next_close_qfq"] / df["close_qfq"] - 1

    # 拆分涨停/跌停
    up = df[df["limit"] == "U"].copy()
    down = df[df["limit"] == "D"].copy()

    # 涨停信号
    if len(up) > 0:
        # 一字涨停 (open_times == 0)
        up["sig_yizi"] = up["open_times"] == 0
        # 烂板 (open_times >= 3)
        up["sig_lanban"] = up["open_times"] >= 3
        # 首板 (limit_times == 1 or up_stat starts with 1)
        up["sig_first_limit"] = up["limit_times"] == 1
        # 连板 (limit_times >= 2)
        up["sig_lianban"] = up["limit_times"] >= 2

        up_signals = {
            "一字涨停 (open_times=0)": "sig_yizi",
            "烂板涨停 (open_times>=3)": "sig_lanban",
            "首板涨停 (limit_times=1)": "sig_first_limit",
            "连板涨停 (limit_times>=2)": "sig_lianban",
        }
        up_valid = up.dropna(subset=["next_ret"])
        print(f"  涨停记录: {len(up_valid):,}")

        up_all = []
        for title, col in up_signals.items():
            stats = signal_stats(up_valid, col, "next_ret")
            print_report(f"涨停: {title}", stats)
            stats["signal"] = title
            up_all.append(stats.reset_index())
        pd.concat(up_all, ignore_index=True).to_csv(OUTPUT_DIR / "limit_up_signals.csv", index=False)

    # 跌停信号
    if len(down) > 0:
        down["sig_yizi_down"] = down["open_times"] == 0
        down["sig_open_down"] = down["open_times"] >= 2

        down_valid = down.dropna(subset=["next_ret"])
        print(f"  跌停记录: {len(down_valid):,}")

        down_signals = {
            "一字跌停": "sig_yizi_down",
            "多次开板跌停 (open>=2)": "sig_open_down",
        }
        down_all = []
        for title, col in down_signals.items():
            stats = signal_stats(down_valid, col, "next_ret")
            print_report(f"跌停: {title}", stats)
            stats["signal"] = title
            down_all.append(stats.reset_index())
        pd.concat(down_all, ignore_index=True).to_csv(OUTPUT_DIR / "limit_down_signals.csv", index=False)


def analyze_toplist(start_date: str):
    print("\n=== 龙虎榜+机构分析 ===")
    tl = load_toplist_data(start_date)
    print(f"  龙虎榜+机构 Rows: {len(tl):,}")
    if tl.empty:
        return

    # Join with factor_pro for next-day return
    sql_fp = """
    SELECT ts_code, trade_date, close_qfq
    FROM stock_stk_factor_pro
    WHERE trade_date >= :start_date
    ORDER BY ts_code, trade_date
    """
    fp = query_df(sql_fp, {"start_date": start_date})
    fp = fp.sort_values(["ts_code", "trade_date"])
    fp["next_close_qfq"] = fp.groupby("ts_code")["close_qfq"].shift(-1)

    merged = pd.merge(tl, fp, on=["ts_code", "trade_date"], how="inner")
    merged["next_ret"] = merged["next_close_qfq"] / merged["close_qfq"] - 1
    valid = merged.dropna(subset=["next_ret"])
    print(f"  Valid: {len(valid):,}")

    # Signal: 机构净买入 > 0
    valid = valid.copy()
    valid["inst_net_buy"] = valid["inst_net_buy"].fillna(0)
    valid["sig_inst_net_buy"] = valid["inst_net_buy"] > 0
    valid["sig_inst_heavy_buy"] = valid["inst_net_buy"] > 5000  # >5000万
    valid["sig_inst_net_sell"] = valid["inst_net_buy"] < -5000

    inst_signals = {
        "机构净买入": "sig_inst_net_buy",
        "机构重仓买入 (>5000万)": "sig_inst_heavy_buy",
        "机构大幅净卖出 (<-5000万)": "sig_inst_net_sell",
    }

    all_stats = []
    for title, col in inst_signals.items():
        stats = signal_stats(valid, col, "next_ret")
        print_report(title, stats)
        stats["signal"] = title
        all_stats.append(stats.reset_index())

    pd.concat(all_stats, ignore_index=True).to_csv(OUTPUT_DIR / "toplist_signals.csv", index=False)


def run_analysis(start_date: str = "20240101"):
    analyze_limit(start_date)
    analyze_toplist(start_date)
    print("\nAll done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20240101")
    run_analysis(parser.parse_args().start)
