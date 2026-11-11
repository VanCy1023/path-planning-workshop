# -*- coding: utf-8 -*-
"""Histogram of the Monte Carlo risk-reduction samples."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
data = json.load(open(os.path.join(HERE, "results", "monte_carlo.json"), encoding="utf-8"))
red = np.array([r["reduction"] for r in data["records"]])
s = data["summary"]

plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
                     "xtick.labelsize": 9, "ytick.labelsize": 9,
                     "font.sans-serif": ["Microsoft YaHei", "SimHei"], "axes.unicode_minus": False})

fig, ax = plt.subplots(figsize=(5.2, 3.4))
bins = np.arange(np.floor(red.min()), np.ceil(red.max()) + 0.5, 1.0)
ax.hist(red, bins=bins, color="#3b6fb6", edgecolor="white", linewidth=0.6, alpha=0.9, label="样本")
ax.axvline(s["median"], color="#c0392b", linewidth=1.6, label="中位数 %.1f%%" % s["median"])
ax.axvline(s["p5"], color="#7f8c8d", linewidth=1.2, linestyle="--", label="5%% 分位 %.1f%%" % s["p5"])
ax.axvline(s["p95"], color="#7f8c8d", linewidth=1.2, linestyle="--", label="95%% 分位 %.1f%%" % s["p95"])
ax.set_xlabel("累计风险降幅 (%)")
ax.set_ylabel("样本数")
ax.set_xlim(24, 37)
ax.grid(axis="y", linewidth=0.35, alpha=0.5)
ax.legend(frameon=True, framealpha=0.9, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "figure15.png"), dpi=300, bbox_inches="tight")
print("wrote figure15.png", len(red), red.min(), red.max())

