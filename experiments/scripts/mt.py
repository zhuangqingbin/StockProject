#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot gap width vs twist angle with dashed line & formatting like the sample.
Usage:
  1) 从 CSV 读入（两列：x,y，含或不含表头）：
     python plot_gap_twist.py --csv data.csv --label "gap 6" --out gap_vs_twist.png
  2) 直接传入数组：
     python plot_gap_twist.py --x 0,5,10,80,85,90 --y 0.05,1.5,1.6,1.6,0.2,0.05 --label "gap 6"

  额外参数：
     --xmin 0 --xmax 90 --ymin 0 --ymax 2 --show  (显示窗口)
"""

import argparse
import csv
import math
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt

def parse_list(s: str) -> List[float]:
    return [float(t) for t in s.split(",") if t.strip() != ""]

def read_csv_xy(path: str) -> Tuple[List[float], List[float]]:
    xs, ys = [], []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        rows = list(r)
        # 如果第一行含非数字表头就跳过
        start_idx = 1 if rows and (not rows[0] or any(not _is_float(x) for x in rows[0][:2])) else 0
        for row in rows[start_idx:]:
            if len(row) < 2:
                continue
            if _is_float(row[0]) and _is_float(row[1]):
                xs.append(float(row[0]))
                ys.append(float(row[1]))
    if not xs:
        raise ValueError("CSV 未读取到有效的 x,y 数据（确保前两列为数字）。")
    return xs, ys

def _is_float(v: str) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False

def plot_xy(
    x: List[float],
    y: List[float],
    label: str = "gap 6",
    xmin: Optional[float] = 0,
    xmax: Optional[float] = 90,
    ymin: Optional[float] = 0,
    ymax: Optional[float] = 2.0,
    out: Optional[str] = "gap_vs_twist.png",
    show: bool = False,
) -> None:
    deg = "\N{DEGREE SIGN}"

    plt.figure(figsize=(7.5, 5.2), dpi=150)

    # 曲线：虚线，无标记
    plt.plot(x, y, linestyle="--", linewidth=2.0, label=label)

    # 轴范围
    if xmin is not None and xmax is not None:
        plt.xlim(xmin, xmax)
    if ymin is not None and ymax is not None:
        plt.ylim(ymin, ymax)

    # 刻度：x 每 10°；y 自动或每 0.2（若设了范围则给出 0.2 的主刻度）
    if xmin is not None and xmax is not None:
        xticks = list(range(int(xmin), int(xmax) + 1, 10))
        plt.xticks(xticks)
    if ymin is not None and ymax is not None:
        step = 0.2
        yticks = [round(ymin + i * step, 10) for i in range(int((ymax - ymin) / step) + 1)]
        plt.yticks(yticks)

    # 标签与图例
    plt.xlabel(f"twist angle({deg})", fontsize=12)
    plt.ylabel("gap width(mm)", fontsize=12)
    plt.legend(loc="upper left", frameon=False)

    # 轴外观（类似示例）
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
    ax.tick_params(direction="out", length=4, width=1, which="major")

    plt.tight_layout()

    if out:
        plt.savefig(out, bbox_inches="tight")
        print(f"Saved figure to: {out}")
    if show:
        plt.show()
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=str, help="CSV 文件路径（两列：x,y）")
    ap.add_argument("--x", type=str, help="逗号分隔的 x 数组，如: 0,5,10,80,85,90")
    ap.add_argument("--y", type=str, help="逗号分隔的 y 数组，如: 0.05,1.5,1.6,1.6,0.2,0.05")
    ap.add_argument("--label", type=str, default="gap 6")
    ap.add_argument("--xmin", type=float, default=0)
    ap.add_argument("--xmax", type=float, default=90)
    ap.add_argument("--ymin", type=float, default=0)
    ap.add_argument("--ymax", type=float, default=2.0)
    ap.add_argument("--out", type=str, default="gap_vs_twist.png")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.csv:
        xs, ys = read_csv_xy(args.csv)
    elif args.x and args.y:
        xs, ys = parse_list(args.x), parse_list(args.y)
        if len(xs) != len(ys):
            raise ValueError("x 与 y 的长度不一致。")
    else:
        raise SystemExit("请提供 --csv 或同时提供 --x 与 --y。")

    plot_xy(
        xs,
        ys,
        label=args.label,
        xmin=args.xmin,
        xmax=args.xmax,
        ymin=args.ymin,
        ymax=args.ymax,
        out=args.out,
        show=args.show,
    )

if __name__ == "__main__":
    main()
