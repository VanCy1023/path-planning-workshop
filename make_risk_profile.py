"""Cumulative risk along the planned path (one panel per time slice)."""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


import config  # noqa: E402
from make_figures import COLORS, ORDER, load, pick

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

RES_M = 10.0
TENSOR = str(config.TPR02 / config.TENSOR_NAME)
STEP = 5
TIME_INDEX = {"0400": 0, "0800": 1, "1800": 2}


def coarsen(slice_zyx):
    return np.ascontiguousarray(np.transpose(slice_zyx, (2, 1, 0))[::STEP, ::STEP, ::STEP], dtype=np.float32) / 100.0


def profile(path, grid):
    pts = np.asarray(path, dtype=float)
    xs, ys = [], []
    s = 0.0
    rc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(round(np.linalg.norm(b - a))))
        for k in range(n):
            q = a + (b - a) * (k / n)
            x, y, z = (int(round(v)) for v in q)
            rc += float(grid[x, y, z]) * RES_M
            s += float(np.linalg.norm(b - a)) / n * RES_M
            xs.append(s)
            ys.append(rc)
    return np.asarray(xs), np.asarray(ys)


def main():
    rows = load("time")
    t = np.load(TENSOR, mmap_mode="r")
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.5))
    for ax, (case, idx) in zip(axes, TIME_INDEX.items()):
        grid = coarsen(np.asarray(t[idx]))
        for planner in ORDER:
            row = pick(rows, case, planner)
            if row is None:
                continue
            x, y = profile(row["path"], grid)
            ax.plot(x, y, color=COLORS[planner], linewidth=1.9,
                    linestyle="--" if planner == "A*-dist" else "-",
                    label=f"{planner} (RC={y[-1]:.0f})")
        ax.set_title(case, fontsize=10)
        ax.set_xlabel("Distance along path (m)", fontsize=8)
        ax.set_xlim(0, 2400)
        ax.set_ylim(0, 200)
        ax.grid(True, linewidth=0.35, alpha=0.5)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("Cumulative risk $RC$", fontsize=8)
    axes[0].legend(fontsize=6.5, frameon=True, framealpha=0.92)
    fig.tight_layout()
    for ext in ("png",):
        fig.savefig(os.path.join(OUT, f"fig_risk_profiles.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote fig_risk_profiles")


if __name__ == "__main__":
    main()
