# -*- coding: utf-8 -*-
"""Chinese flowchart v3: same layout, much larger type relative to the canvas."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

for cand in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=cand).get_name()
        break
plt.rcParams["mathtext.fontset"] = "stix"
plt.rcParams["axes.unicode_minus"] = False

INK = "#1B2A4A"
EDGE = "#54657F"
FILL = "#FFFFFF"

fig, ax = plt.subplots(figsize=(5.9, 6.5), dpi=400)
ax.set_xlim(0, 76)
ax.set_ylim(0, 84)
ax.axis("off")
fig.patch.set_facecolor("white")

FS_D, FS_B, FS_I = 14.5, 15.5, 13.5


def rbox(x, y, w, h, text, fs=FS_B):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2.4",
                                linewidth=1.3, edgecolor=EDGE, facecolor=FILL, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, zorder=4, linespacing=1.45)


def diamond(cx, cy, w, h, text, fs=FS_D):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.3, edgecolor=EDGE,
                         facecolor=FILL, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK,
            zorder=4, linespacing=1.4)


def arr(p1, p2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.3, color=EDGE, zorder=2,
                                 shrinkA=0, shrinkB=0))


CX = 45
DW, DH1, DH2 = 50, 13.5, 10.5
D1, D2, D3, D4 = 63.0, 48.5, 34.0, 20.0

rbox(19, 72.5, 44, 6.6, r"输入  $F=(T_{orig},N_f,H,S_b)$", fs=14)

diamond(CX, D1, DW, DH1, r"地类$\in$｛办公,零售,商业｝" "\n" r"且 $H\geq 50$ 或 $N_f\geq 15$")
diamond(CX, D2, DW, DH2, r"$S_b>2500$ 且 $N_f\leq 3$")
diamond(CX, D3, DW, DH1, r"地类$\in$｛学校,医院,大学｝" "\n" r"且 $800<S_b\leq 2500$" "\n" r"或 $3\leq N_f\leq 6$")
diamond(CX, D4, DW, DH2, r"$S_b\leq 300$ 且 $N_f\leq 3$")

arr((CX, 72.5), (CX, D1 + DH1 / 2))
arr((CX, D1 - DH1 / 2), (CX, D2 + DH2 / 2))
arr((CX, D2 - DH2 / 2), (CX, D3 + DH1 / 2))
arr((CX, D3 - DH1 / 2), (CX, D4 + DH2 / 2))

outs = [("商业", D1), ("工业", D2), ("公共设施", D3), ("住宅", D4)]
for label, y in outs:
    rbox(0.5, y - 3.1, 16.0, 6.2, label, fs=15)
    arr((CX - DW / 2, y), (16.6, y))
    ax.text(18.4, y + 1.1, "是", ha="center", va="bottom", fontsize=12.5, color=INK)

gaps = [(D1 - DH1 / 2, D2 + DH2 / 2), (D2 - DH2 / 2, D3 + DH1 / 2),
        (D3 - DH1 / 2, D4 + DH2 / 2)]
for top, bot in gaps:
    ax.text(CX + 1.8, (top + bot) / 2, "否", ha="left", va="center",
            fontsize=12.5, color=INK)

arr((CX, D4 - DH2 / 2), (CX, 11.4))
ax.text(CX + 1.8, (D4 - DH2 / 2 + 11.4) / 2, "否", ha="left", va="center",
        fontsize=12.5, color=INK)

rbox(23, 4.2, 44, 6.6, "其他", fs=15)

plt.tight_layout(pad=0.05)
out = str(config.PROJECT_DIR / "ppt" / "地类推断流程_中文.png")
fig.savefig(out, dpi=400, facecolor="white", bbox_inches="tight", pad_inches=0.04)
print("saved", out, os.path.getsize(out) // 1024, "KB")
