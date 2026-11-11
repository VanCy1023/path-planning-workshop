# -*- coding: utf-8 -*-
"""Layered framework: three columns (data | modelling | planning), vertical flow."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch
from matplotlib.path import Path

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

for cand in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=cand).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

INK, TEAL, GREY = "#1B2A4A", "#0E8A6E", "#33405A"
EDGE, SOFT, MUTED = "#B3C1D2", "#E9EFF9", "#8C9AAE"

fig, ax = plt.subplots(figsize=(9.0, 6.1), dpi=300)
ax.set_xlim(0, 92)
ax.set_ylim(0, 64)
ax.axis("off")
fig.patch.set_facecolor("white")


def node(x, y, w, h, text, key=False, soft=False, fs=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.7",
                                linewidth=1.05, edgecolor=INK if key else EDGE,
                                facecolor=INK if key else (SOFT if soft else "white"), zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color="white" if key else GREY, zorder=4, linespacing=1.45,
            fontweight="bold" if (key or soft) else "normal")
    return (x, y, w, h)


def _path(pts, r=1.6):
    verts, codes = [pts[0]], [Path.MOVETO]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = np.array(pts[i - 1]), np.array(pts[i]), np.array(pts[i + 1])
        v1, v2 = p0 - p1, p2 - p1
        l1, l2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if l1 < 1e-6 or l2 < 1e-6:
            verts.append(tuple(p1)); codes.append(Path.LINETO); continue
        r1, r2 = min(r, l1 / 2), min(r, l2 / 2)
        verts += [tuple(p1 + v1 / l1 * r1), tuple(p1), tuple(p1 + v2 / l2 * r2)]
        codes += [Path.LINETO, Path.CURVE3, Path.CURVE3]
    verts.append(pts[-1]); codes.append(Path.LINETO)
    return Path(verts, codes)


def line(pts, c=TEAL, lw=1.35):
    ax.add_patch(PathPatch(_path(pts), fill=False, edgecolor=c, linewidth=lw,
                           zorder=2, capstyle="round", joinstyle="round"))


def arr(pts, c=TEAL, lw=1.35, ms=8.5):
    line(pts, c, lw)
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=ms,
                                 linewidth=lw, color=c, zorder=2, shrinkA=0, shrinkB=0))


def cx(b): return b[0] + b[2] / 2
def cy(b): return b[1] + b[3] / 2
def rt(b): return b[0] + b[2]

# ---------------- column captions ----------------
for label, x in [("数据输入", 2), ("风险场构建", 30), ("规划与评价", 64)]:
    ax.text(x, 61.4, label, fontsize=8.4, color=TEAL, fontweight="bold")

# ---------------- A: data ----------------
A = [node(2, 53.5, 20, 5.2, "OSM 建筑轮廓"),
     node(2, 47.0, 20, 5.2, "WorldPop 人口栅格"),
     node(2, 40.5, 20, 5.2, "时段出行强度曲线")]

# ---------------- B: modelling chain ----------------
B1 = node(30, 53.5, 26, 5.2, "形态学语义推断", soft=True)
B2 = node(30, 47.0, 26, 5.2, "五类地类")
B3 = node(30, 40.5, 26, 5.2, "人口基底  $P_{base}$")
B4 = node(30, 34.0, 26, 5.2, "时段重分配  $\\gamma,\\ \\eta(t)$", soft=True)

R = [node(28, 25.5, 8.4, 4.6, "致死", fs=8.2),
     node(38.4, 25.5, 8.4, 4.6, "财产", fs=8.2),
     node(48.8, 25.5, 8.4, 4.6, "噪声", fs=8.2)]

B5 = node(30, 15.5, 26, 5.4, "归一化加权融合  0.4/0.3/0.2/0.1", soft=True, fs=8.0)
B6 = node(28, 4.2, 30, 8.0, "四维风险张量  $T(x,y,z,t)$", key=True, fs=9.2)

# ---------------- C: planning ----------------
C = [node(64, 53.5, 24, 5.2, "A*"),
     node(64, 47.0, 24, 5.2, "Risk-A*", soft=True),
     node(64, 40.5, 24, 5.2, "PSO"),
     node(64, 34.0, 24, 5.2, "RRT*")]
C5 = node(64, 5.6, 24, 6.2, "评价指标\nRC ｜ 暴露 ｜ PL", fs=8.2)

# ---------------- links ----------------
BUS_X = 26.5
line([(rt(A[0]), cy(A[0])), (BUS_X, cy(A[0]))])
for a in A[1:]:
    line([(rt(a), cy(a)), (BUS_X, cy(a))])
line([(BUS_X, cy(A[2])), (BUS_X, cy(A[0]))])
arr([(BUS_X, cy(A[0])), (30, cy(A[0]))])

for a, b in [(B1, B2), (B2, B3), (B3, B4)]:
    arr([(cx(a), a[1]), (cx(b), b[1] + b[3])])

RB = 32.0
line([(cx(B4), B4[1]), (cx(B4), RB)])
line([(cx(R[2]), RB), (cx(R[0]), RB)])
for r in R:
    arr([(cx(r), RB), (cx(r), r[1] + r[3])])

MB = 22.2
for r in R:
    line([(cx(r), r[1]), (cx(r), MB)])
line([(cx(R[0]), MB), (cx(R[2]), MB)])
arr([(cx(B5), MB), (cx(B5), B5[1] + B5[3])])

arr([(cx(B5), B5[1]), (cx(B6), B6[1] + B6[3])])

TB = 61.0
line([(rt(B6), cy(B6)), (TB, cy(B6))])
line([(TB, cy(B6)), (TB, cy(C[0]))])
for c in C:
    arr([(TB, cy(c)), (64, cy(c))])
ax.text(cx(B6), 1.6, "按到达时刻切取 $t_{arr}$", fontsize=7.2, color=TEAL,
        ha="center", va="center")

COL = 90.0
for c in C:
    line([(rt(c), cy(c)), (COL, cy(c))])
line([(COL, cy(C[0])), (COL, cy(C5))])
arr([(COL, cy(C5)), (rt(C5), cy(C5))])

plt.tight_layout(pad=0.1)
out = str(config.PROJECT_DIR / "ppt" / "框架图_分层版.png")
fig.savefig(out, dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0.08)
print("saved", out, os.path.getsize(out) // 1024, "KB")
