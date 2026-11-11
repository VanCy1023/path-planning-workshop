# -*- coding: utf-8 -*-
"""Richer three-line tables built from the manuscript's real numbers."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

BASE = str(config.PROJECT_DIR / "ppt" / "assets")
for cand in (r"C:\Windows\Fonts\msyh.ttc",):
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        CN = font_manager.FontProperties(fname=cand).get_name()
plt.rcParams["font.family"] = CN
plt.rcParams["text.usetex"] = False
INK = "#1B2A4A"


def table(name, header, rows, widths, fs=10.5, row_h=0.36):
    w = float(sum(widths))
    h = row_h * (len(rows) + 1) + 0.26
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    xs = [0]
    for cw in widths:
        xs.append(xs[-1] + cw)
    top = h - 0.1
    y_head = top - row_h
    y_bot = y_head - row_h * len(rows)
    ax.plot([0, w], [top, top], color=INK, lw=1.5)
    ax.plot([0, w], [y_head, y_head], color=INK, lw=0.8)
    ax.plot([0, w], [y_bot, y_bot], color=INK, lw=1.5)
    for i, t in enumerate(header):
        ax.text((xs[i] + xs[i + 1]) / 2, y_head + row_h / 2, t, ha="center", va="center",
                fontsize=fs, color=INK, fontweight="bold")
    for r, row in enumerate(rows):
        yc = y_head - row_h * (r + 0.5)
        for i, cell in enumerate(row):
            bold = isinstance(cell, tuple)
            text = cell[0] if bold else cell
            ax.text((xs[i] + xs[i + 1]) / 2, yc, text, ha="center", va="center",
                    fontsize=fs, color=INK, fontweight="bold" if bold else "normal")
    fig.savefig(os.path.join(BASE, name), dpi=300, transparent=True,
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("table", name)


HDR = ["时段", "方法", "节点数", "PL/m", "RC", "RC/L"]
W6 = [0.95, 1.25, 1.35, 1.15, 1.05, 1.05]

table("t1.png", HDR,
      [["04:00", "A*", "51177", "2256.3", "127.5", "0.0565"],
       ["", "Risk-A*", "91978", "2269.0", ("39.7",), ("0.0175",)],
       ["08:00", "A*", "50852", "2256.3", "230.4", "0.1021"],
       ["", "Risk-A*", "177464", "2286.5", ("155.3",), ("0.0679",)],
       ["18:00", "A*", "50865", "2256.3", "221.2", "0.0980"],
       ["", "Risk-A*", "170661", "2286.5", ("142.4",), ("0.0623",)]],
      W6)

table("t2.png", ["区域", "方法", "节点数", "PL/m", "RC", "RC/L"],
      [["低密度", "A*", "50865", "2256.3", "221.2", "0.0980"],
       ["", "Risk-A*", "170661", "2286.5", ("142.4",), ("0.0623",)],
       ["中密度", "A*", "51032", "2256.3", "221.5", "0.0982"],
       ["", "Risk-A*", "190265", "2262.1", ("126.7",), ("0.0560",)],
       ["高密度", "A*", "30069", "2251.4", "516.9", "0.2296"],
       ["", "Risk-A*", "197776", "2343.2", ("203.4",), ("0.0868",)]],
      W6)

table("t3.png", ["配置", "方法", "节点数", "PL/m", "RC", "RC/L"],
      [["仅静态", "A*", "51189", "2256.3", "64.6", "0.0286"],
       ["", "Risk-A*", "46346", "2258.2", ("0.3",), ("0.0001",)],
       ["+ 人口", "A*", "51169", "2256.3", "166.5", "0.0738"],
       ["", "Risk-A*", "134368", "2269.0", ("97.0",), ("0.0427",)],
       ["完整", "A*", "50865", "2256.3", "221.2", "0.0980"],
       ["", "Risk-A*", "170661", "2286.5", ("142.4",), ("0.0623",)]],
      W6)

table("t4.png", ["条件", "08:00 RC", "18:00 RC", "相对基准"],
      [["权重 w = 1.00", "155.3", "142.4", "—"],
       ["权重 w = 1.25", ("193.1",), ("183.7",), ("+24.3%",)],
       ["60 组蒙特卡洛", ("26.7–35.4%",), ("中位 31.4%",), "60/60 优于 A*"]],
      [1.75, 1.45, 1.45, 1.65], fs=10, row_h=0.4)
