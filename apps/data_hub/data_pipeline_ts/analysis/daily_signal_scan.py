"""
每日信号扫描器 — 输出高胜率策略选股 + 回避股票
==============================================
用法:
    python -m apps.data_hub.data_pipeline_ts.analysis.daily_signal_scan
    python -m apps.data_hub.data_pipeline_ts.analysis.daily_signal_scan --date 20260325
    python -m apps.data_hub.data_pipeline_ts.analysis.daily_signal_scan --days 3   # 最近3个交易日

价格字段: close_qfq (前复权收盘价)
次日收益定义: 次交易日 close_qfq / 当日 close_qfq - 1
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import argparse
from datetime import datetime

import numpy as np
import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.common.db import query_df

OUTPUT_DIR = Path(__file__).parent / "daily_output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────

def get_latest_trade_dates(n: int = 1) -> list[str]:
    """获取最近 n 个交易日日期"""
    sql = """
    SELECT DISTINCT trade_date
    FROM stock_stk_factor_pro
    ORDER BY trade_date DESC
    LIMIT :n
    """
    df = query_df(sql, {"n": n})
    return sorted(df["trade_date"].tolist())


def load_factor_pro(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT
        fp.ts_code, fp.trade_date,
        fp.close, fp.close_qfq, fp.vol, fp.amount,
        fp.volume_ratio, fp.turnover_rate_f, fp.pct_chg,
        fp.pe_ttm, fp.pb, fp.total_mv, fp.circ_mv,
        fp.macd_dif_bfq, fp.macd_dea_bfq, fp.macd_bfq,
        fp.rsi_bfq_6, fp.rsi_bfq_12,
        fp.kdj_k_bfq, fp.kdj_d_bfq,
        fp.boll_upper_bfq, fp.boll_mid_bfq, fp.boll_lower_bfq,
        fp.bias1_bfq, fp.cci_bfq,
        fp.ma_bfq_5, fp.ma_bfq_20, fp.ma_bfq_60
    FROM stock_stk_factor_pro fp
    WHERE fp.trade_date IN ({placeholders})
    ORDER BY fp.ts_code, fp.trade_date
    """
    return query_df(sql)


def load_money_flow(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date,
        buy_elg_amount, sell_elg_amount,
        buy_lg_amount, sell_lg_amount,
        net_mf_amount
    FROM stock_money_flow
    WHERE trade_date IN ({placeholders})
    """
    df = query_df(sql)
    if df.empty:
        return df
    df["main_net"] = (df["buy_elg_amount"] + df["buy_lg_amount"]
                      - df["sell_elg_amount"] - df["sell_lg_amount"])
    df["elg_net"] = df["buy_elg_amount"] - df["sell_elg_amount"]
    return df


def load_cyq_perf(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date, winner_rate, cost_5pct, cost_95pct, weight_avg
    FROM stock_cyq_perf
    WHERE trade_date IN ({placeholders})
    """
    return query_df(sql)


def load_limit_list(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date, `limit` AS limit_type, open_times, fd_amount, limit_times
    FROM stock_limit_list_d
    WHERE trade_date IN ({placeholders})
    """
    return query_df(sql)


def load_top_inst(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date,
        SUM(CASE WHEN side = '0' THEN buy ELSE 0 END) AS inst_buy,
        SUM(CASE WHEN side = '1' THEN sell ELSE 0 END) AS inst_sell,
        SUM(net_buy) AS inst_net_buy
    FROM stock_top_inst
    WHERE trade_date IN ({placeholders})
    GROUP BY ts_code, trade_date
    """
    return query_df(sql)


def load_hk_hold(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date, vol AS hk_vol, ratio AS hk_ratio
    FROM stock_hk_hold
    WHERE trade_date IN ({placeholders}) AND ratio IS NOT NULL AND ratio > 0
    """
    return query_df(sql)


def load_margin_detail(dates: list[str]) -> pd.DataFrame:
    placeholders = ",".join([f"'{d}'" for d in dates])
    sql = f"""
    SELECT ts_code, trade_date, rzye, rzmre, rzche, rqye, rqyl
    FROM stock_margin_detail
    WHERE trade_date IN ({placeholders})
    """
    return query_df(sql)


def load_stock_names() -> pd.DataFrame:
    sql = "SELECT ts_code, name FROM stock_basic"
    return query_df(sql)


# ─────────────────────────────────────────────
# Merge and compute signals
# ─────────────────────────────────────────────

def build_daily_dataset(dates: list[str]) -> pd.DataFrame:
    """合并所有数据源"""
    print("  加载 factor_pro ...")
    base = load_factor_pro(dates)
    print(f"    {len(base):,} rows")

    print("  加载 money_flow ...")
    mf = load_money_flow(dates)
    print(f"    {len(mf):,} rows")

    print("  加载 cyq_perf ...")
    cyq = load_cyq_perf(dates)
    print(f"    {len(cyq):,} rows")

    print("  加载 limit_list_d ...")
    limit = load_limit_list(dates)
    print(f"    {len(limit):,} rows")

    print("  加载 top_inst ...")
    inst = load_top_inst(dates)
    print(f"    {len(inst):,} rows")

    print("  加载 hk_hold ...")
    hk = load_hk_hold(dates)
    print(f"    {len(hk):,} rows")

    print("  加载 margin_detail ...")
    margin = load_margin_detail(dates)
    print(f"    {len(margin):,} rows")

    df = base
    if not mf.empty:
        df = df.merge(mf[["ts_code", "trade_date", "main_net", "elg_net"]],
                       on=["ts_code", "trade_date"], how="left")
    if not cyq.empty:
        df = df.merge(cyq, on=["ts_code", "trade_date"], how="left")
    if not limit.empty:
        df = df.merge(limit, on=["ts_code", "trade_date"], how="left")
    if not inst.empty:
        df = df.merge(inst, on=["ts_code", "trade_date"], how="left")
    if not hk.empty:
        df = df.merge(hk, on=["ts_code", "trade_date"], how="left")
    if not margin.empty:
        df = df.merge(margin[["ts_code", "trade_date", "rzye"]],
                       on=["ts_code", "trade_date"], how="left")

    # 派生指标
    df["main_net_pct"] = df["main_net"] / df["amount"].replace(0, np.nan) * 100
    if "cost_95pct" in df.columns and "cost_5pct" in df.columns:
        df["chip_spread_pct"] = ((df["cost_95pct"] - df["cost_5pct"])
                                  / df["weight_avg"].replace(0, np.nan) * 100)

    return df


# ─────────────────────────────────────────────
# Signal definitions
# ─────────────────────────────────────────────

LONG_SIGNALS = {
    "S1_首板涨停+主力大幅流入": {
        "desc": "首板涨停 + 主力净流入占比>5% | 历史胜率69.1%, 5日+5.35%",
        "filter": lambda df: (
            (df["limit_type"] == "U") & (df["limit_times"] == 1)
            & (df["main_net_pct"] > 5)
        ),
    },
    "S2_主力净流入5~10pct": {
        "desc": "主力净流入占成交额5~10% | 历史胜率78.5%, 次日+5.02%",
        "filter": lambda df: (
            (df["main_net_pct"] > 5) & (df["main_net_pct"] < 10)
        ),
    },
    "S3_极低获利+放量": {
        "desc": "获利比例<5% + 量比>1.5 | 历史胜率56.8%, 次日+0.64%, 样本22K",
        "filter": lambda df: (
            (df["winner_rate"] < 5) & (df["volume_ratio"] > 1.5)
        ),
    },
    "S4_一字涨停": {
        "desc": "一字涨停 (开板次数=0) | 历史胜率73.2%, 次日+5.59%",
        "filter": lambda df: (
            (df["limit_type"] == "U") & (df["open_times"] == 0)
        ),
    },
    "S5_机构龙虎榜净买入": {
        "desc": "龙虎榜机构净买入>0 | 历史胜率54.0%, 次日+1.35%",
        "filter": lambda df: (
            df["inst_net_buy"].fillna(0) > 0
        ),
    },
    "S6_北向大幅加仓+MACD多头": {
        "desc": "北向持股比例增>0.3pp + MACD金叉 | 历史胜率53.3%, 次日+4.06%",
        "filter": lambda df: (
            (df["hk_ratio_chg"] > 0.3) & (df["macd_dif_bfq"] > df["macd_dea_bfq"])
        ),
    },
    "S7_底部共振": {
        "desc": "近布林下轨 + RSI<30 + 主力净流入 | 历史胜率50.9%, 5日+1.18%",
        "filter": lambda df: (
            (df["close"] < df["boll_lower_bfq"] * 1.02)
            & (df["rsi_bfq_6"] < 30)
            & (df["main_net"] > 0)
        ),
    },
    "S8_多因子共振≥6": {
        "desc": "≥6个看多因子同时亮灯 | 历史胜率47~58%, 样本稀缺但胜率高",
        "filter": lambda df: df["bull_count"] >= 6,
    },
    "S9_大宗溢价>5pct": {
        "desc": "注意: 需隔日查看大宗交易数据, 此处仅标记主力大幅流入+近涨停",
        "filter": lambda df: (
            (df["pct_chg"] > 8) & (df["main_net_pct"] > 5)
        ),
    },
}

AVOID_SIGNALS = {
    "A1_跌停+主力大幅流出": {
        "desc": "跌停 + 主力净流出占比>5% | 历史84.8%继续跌, 次日-6.18%",
        "filter": lambda df: (
            (df["limit_type"] == "D") & (df["main_net_pct"] < -5)
        ),
    },
    "A2_主力净流出超10pct": {
        "desc": "主力净流出占成交额>10% | 历史100%跌, 次日-5.04%",
        "filter": lambda df: df["main_net_pct"] < -10,
    },
    "A3_机构龙虎榜大幅净卖出": {
        "desc": "龙虎榜机构净卖出>5000万 | 历史60.5%跌, 次日-1.11%",
        "filter": lambda df: df["inst_net_buy"].fillna(0) < -5000,
    },
    "A4_RSI超买+近布林上轨+主力流出": {
        "desc": "RSI>70 + 近上轨 + 主力流出 | 多空分歧见顶",
        "filter": lambda df: (
            (df["rsi_bfq_6"] > 70)
            & (df["close"] > df["boll_upper_bfq"] * 0.98)
            & (df["main_net"] < 0)
        ),
    },
}


def compute_bull_count(df: pd.DataFrame) -> pd.Series:
    """计算每行看多因子亮灯数"""
    flags = pd.DataFrame(index=df.index)
    flags["f_macd_bull"] = df["macd_dif_bfq"] > df["macd_dea_bfq"]
    flags["f_ma_bull"] = (df["ma_bfq_5"] > df["ma_bfq_20"]) & (df["ma_bfq_20"] > df["ma_bfq_60"])
    flags["f_main_inflow"] = df["main_net"].fillna(0) > 0
    flags["f_elg_inflow"] = df["elg_net"].fillna(0) > 0
    flags["f_vol_surge"] = df["volume_ratio"] > 1.5
    flags["f_nb_add"] = df.get("hk_ratio_chg", pd.Series(dtype=float)).fillna(0) > 0.1
    flags["f_rz_up"] = df.get("rzye_chg_pct", pd.Series(dtype=float)).fillna(0) > 3
    flags["f_chip_tight"] = df.get("chip_spread_pct", pd.Series(dtype=float)).fillna(100) < 20
    flags["f_low_winner"] = df.get("winner_rate", pd.Series(dtype=float)).fillna(50) < 10
    return flags.fillna(False).sum(axis=1)


# ─────────────────────────────────────────────
# Main scan
# ─────────────────────────────────────────────

def scan(target_date: str | None = None, days: int = 1):
    print("=" * 70)
    print("  每日信号扫描器")
    print("  价格: close_qfq (前复权)  次日收益: 次日close_qfq/当日-1")
    print("=" * 70)

    # Determine dates
    if target_date:
        dates = [target_date]
    else:
        dates = get_latest_trade_dates(days)

    print(f"\n  扫描日期: {', '.join(dates)}")

    # Load data
    print("\n[1/4] 加载数据 ...")
    df = build_daily_dataset(dates)
    print(f"  合并后: {len(df):,} rows")

    # Load stock names
    print("\n[2/4] 加载股票名称 ...")
    names = load_stock_names()
    name_map = dict(zip(names["ts_code"], names["name"]))

    # Compute derived fields needed for some signals
    df = df.sort_values(["ts_code", "trade_date"])
    # 北向持股变化 (需要前一日数据, 如果只有1天则从DB取)
    if "hk_ratio" in df.columns:
        if len(dates) > 1:
            df["prev_hk_ratio"] = df.groupby("ts_code")["hk_ratio"].shift(1)
        else:
            # 取前一天的北向数据
            prev_dates = get_latest_trade_dates(2)
            if len(prev_dates) >= 2:
                prev_date = prev_dates[0]
                prev_hk = load_hk_hold([prev_date])
                if not prev_hk.empty:
                    prev_map = dict(zip(prev_hk["ts_code"], prev_hk["hk_ratio"]))
                    df["prev_hk_ratio"] = df["ts_code"].map(prev_map)
        df["hk_ratio_chg"] = df["hk_ratio"] - df.get("prev_hk_ratio", pd.Series(dtype=float))

    # 融资余额变化
    if "rzye" in df.columns:
        if len(dates) > 1:
            df["prev_rzye"] = df.groupby("ts_code")["rzye"].shift(1)
        else:
            prev_dates = get_latest_trade_dates(2)
            if len(prev_dates) >= 2:
                prev_margin = load_margin_detail([prev_dates[0]])
                if not prev_margin.empty:
                    prev_rz = dict(zip(prev_margin["ts_code"], prev_margin["rzye"]))
                    df["prev_rzye"] = df["ts_code"].map(prev_rz)
        if "prev_rzye" in df.columns:
            df["rzye_chg_pct"] = (df["rzye"] / df["prev_rzye"].replace(0, np.nan) - 1) * 100

    # Bull count
    df["bull_count"] = compute_bull_count(df)

    # Only keep target date(s)
    scan_df = df[df["trade_date"].isin(dates)].copy()
    print(f"  扫描范围: {len(scan_df):,} 条记录")

    # ── Scan signals ──
    print("\n[3/4] 扫描信号 ...\n")

    all_picks = []

    # LONG signals
    print("=" * 70)
    print("  📈 做多信号 (高胜率策略)")
    print("=" * 70)

    for sig_name, sig_def in LONG_SIGNALS.items():
        try:
            mask = sig_def["filter"](scan_df)
        except Exception:
            mask = pd.Series(False, index=scan_df.index)

        hits = scan_df[mask].copy()
        if hits.empty:
            print(f"\n  [{sig_name}] {sig_def['desc']}")
            print(f"    今日无触发")
            continue

        hits["name"] = hits["ts_code"].map(name_map).fillna("")
        hits = hits.sort_values("pct_chg", ascending=False)

        print(f"\n  [{sig_name}] {sig_def['desc']}")
        print(f"    触发数: {len(hits)}")
        print(f"    {'代码':<12} {'名称':<8} {'收盘':>8} {'涨跌幅':>8} {'换手率':>8} {'量比':>6} {'主力净流入%':>10}")
        print(f"    {'-'*62}")

        for _, row in hits.head(20).iterrows():
            print(f"    {row['ts_code']:<12} {row['name']:<8} "
                  f"{row['close']:>8.2f} {row['pct_chg']:>7.2f}% "
                  f"{row.get('turnover_rate_f', 0):>7.2f}% "
                  f"{row.get('volume_ratio', 0):>5.2f} "
                  f"{row.get('main_net_pct', 0):>9.2f}%")

        if len(hits) > 20:
            print(f"    ... 还有 {len(hits) - 20} 只")

        for _, row in hits.iterrows():
            all_picks.append({
                "trade_date": row["trade_date"],
                "ts_code": row["ts_code"],
                "name": row["name"],
                "signal": sig_name,
                "direction": "LONG",
                "close": row["close"],
                "pct_chg": row["pct_chg"],
                "volume_ratio": row.get("volume_ratio"),
                "turnover_rate_f": row.get("turnover_rate_f"),
                "main_net_pct": row.get("main_net_pct"),
                "winner_rate": row.get("winner_rate"),
                "rsi_6": row.get("rsi_bfq_6"),
                "bull_count": row.get("bull_count"),
            })

    # AVOID signals
    print(f"\n\n{'=' * 70}")
    print("  📉 回避信号 (高概率下跌)")
    print("=" * 70)

    for sig_name, sig_def in AVOID_SIGNALS.items():
        try:
            mask = sig_def["filter"](scan_df)
        except Exception:
            mask = pd.Series(False, index=scan_df.index)

        hits = scan_df[mask].copy()
        if hits.empty:
            print(f"\n  [{sig_name}] {sig_def['desc']}")
            print(f"    今日无触发")
            continue

        hits["name"] = hits["ts_code"].map(name_map).fillna("")
        hits = hits.sort_values("pct_chg")

        print(f"\n  [{sig_name}] {sig_def['desc']}")
        print(f"    触发数: {len(hits)}")
        print(f"    {'代码':<12} {'名称':<8} {'收盘':>8} {'涨跌幅':>8} {'主力净流入%':>10}")
        print(f"    {'-'*48}")

        for _, row in hits.head(20).iterrows():
            print(f"    {row['ts_code']:<12} {row['name']:<8} "
                  f"{row['close']:>8.2f} {row['pct_chg']:>7.2f}% "
                  f"{row.get('main_net_pct', 0):>9.2f}%")

        if len(hits) > 20:
            print(f"    ... 还有 {len(hits) - 20} 只")

        for _, row in hits.iterrows():
            all_picks.append({
                "trade_date": row["trade_date"],
                "ts_code": row["ts_code"],
                "name": row["name"],
                "signal": sig_name,
                "direction": "AVOID",
                "close": row["close"],
                "pct_chg": row["pct_chg"],
                "volume_ratio": row.get("volume_ratio"),
                "turnover_rate_f": row.get("turnover_rate_f"),
                "main_net_pct": row.get("main_net_pct"),
                "winner_rate": row.get("winner_rate"),
                "rsi_6": row.get("rsi_bfq_6"),
                "bull_count": row.get("bull_count"),
            })

    # ── Save to CSV ──
    print(f"\n\n[4/4] 保存结果 ...")
    if all_picks:
        picks_df = pd.DataFrame(all_picks)
        date_str = dates[-1]
        out_file = OUTPUT_DIR / f"signals_{date_str}.csv"
        picks_df.to_csv(out_file, index=False)
        print(f"  已保存: {out_file}")

        # Summary
        long_count = len(picks_df[picks_df["direction"] == "LONG"])
        avoid_count = len(picks_df[picks_df["direction"] == "AVOID"])
        print(f"\n  汇总: 做多信号 {long_count} 条, 回避信号 {avoid_count} 条")

        # 多信号重叠的股票 (出现在2个以上做多信号中)
        long_picks = picks_df[picks_df["direction"] == "LONG"]
        if not long_picks.empty:
            overlap = long_picks.groupby(["ts_code", "name"]).agg(
                signals=("signal", lambda x: " + ".join(sorted(set(x)))),
                count=("signal", "nunique"),
            ).reset_index()
            overlap = overlap[overlap["count"] >= 2].sort_values("count", ascending=False)

            if not overlap.empty:
                print(f"\n  {'=' * 70}")
                print(f"  ⭐ 多信号重叠 (出现在2个以上做多策略中)")
                print(f"  {'=' * 70}")
                for _, row in overlap.head(15).iterrows():
                    print(f"    {row['ts_code']} {row['name']} — {row['count']}个信号: {row['signals']}")
                overlap.to_csv(OUTPUT_DIR / f"overlap_{date_str}.csv", index=False)
    else:
        print("  今日无信号触发")

    print(f"\n{'=' * 70}")
    print("  扫描完成")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日信号扫描器")
    parser.add_argument("--date", default=None, help="指定日期 YYYYMMDD (默认最新交易日)")
    parser.add_argument("--days", type=int, default=1, help="扫描最近N个交易日 (默认1)")
    args = parser.parse_args()
    scan(target_date=args.date, days=args.days)
