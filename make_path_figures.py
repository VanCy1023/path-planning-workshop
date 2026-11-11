"""Top-view path figures: risk heat map + planned paths for each case."""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


import config  # noqa: E402
from make_figures import COLORS, ORDER, load, pick, risk_map

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

RES_M = 10.0
TENSORS = {
    "Low": str(config.TPR02 / config.TENSOR_NAME),
    "Medium": str(config.TPR03 / config.TENSOR_NAME),
    "High": str(config.TPR04 / config.TENSOR_NAME),
}
TIME_SLICE = {"0400": 0, "0800": 1, "1800": 2}


def draw_topview(records, cases, titles, filename, risk_by_case):
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.9))
    pooled = np.concatenate([m.ravel() for m in risk_by_case.values()])
    vmax = float(np.percentile(pooled[pooled > 4.5], 98))
    for ax, case in zip(axes, cases):
        im = ax.imshow(risk_by_case[case], origin="lower", extent=(0, 2000, 0, 2000),
                       cmap="jet", vmin=2, vmax=vmax, interpolation="nearest", alpha=0.95)
        for planner in ORDER:
            row = pick(records, case, planner)
            if row is None:
                continue
            pts = np.asarray(row["path"], dtype=float) * RES_M
            ax.plot(pts[:, 0], pts[:, 1], color=COLORS[planner], linewidth=2.0,
                    label=planner, solid_capstyle="round", zorder=5,
                    linestyle="--" if planner == "A*-dist" else "-")
        start = np.asarray(records[0]["start"], dtype=float) * RES_M
        goal = np.asarray(records[0]["goal"], dtype=float) * RES_M
        ax.scatter(start[0], start[1], marker="^", s=90, color="white", edgecolor="black", linewidth=0.8, zorder=6)
        ax.scatter(goal[0], goal[1], marker="*", s=170, color="#ffd600", edgecolor="black", linewidth=0.8, zorder=6)
        ax.set_title(case, fontsize=10)
        ax.set_xlabel("X (m)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal")
        ax.grid(True, color="#555555", linewidth=0.35, alpha=0.5)
    axes[0].set_ylabel("Y (m)", fontsize=8)
    axes[0].legend(loc="upper left", fontsize=7, frameon=True, framealpha=0.92, handlelength=2.2)
    fig.colorbar(im, ax=axes, shrink=0.78, pad=0.015, label="Discrete air-block risk (20 m × 20 m)")
    for ext in ("png",):
        fig.savefig(os.path.join(OUT, f"{filename}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    time_rows = load("time")
    t = np.load(TENSORS["Low"], mmap_mode="r")
    risk_time = {k: risk_map(np.asarray(t[i])) for k, i in TIME_SLICE.items()}
    draw_topview(time_rows, ["0400", "0800", "1800"],
                 ["04:00", "08:00", "18:00"], "fig_time_paths", risk_time)

    density_rows = load("density")
    risk_density = {}
    for name in ("Low", "Medium", "High"):
        arr = np.load(TENSORS[name], mmap_mode="r")
        risk_density[name] = risk_map(np.asarray(arr[2]))
    draw_topview(density_rows, ["Low", "Medium", "High"],
                 ["Low density", "Medium density", "High density"], "fig_density_paths", risk_density)

    abl_rows = load("ablation")
    abl_files = {
        "Static": str(config.ABLATION_DIR / "env_tensor_abl_static.npy"),
        "Pop": str(config.ABLATION_DIR / "env_tensor_abl_pop.npy"),
        "Full": str(config.ABLATION_DIR / "env_tensor_abl_full.npy"),
    }
    risk_abl = {k: risk_map(np.asarray(np.load(v, mmap_mode="r")[2])) for k, v in abl_files.items()}
    draw_topview(abl_rows, ["Static", "Pop", "Full"],
                 ["Static", "Static + population", "Full multi-source"], "fig_ablation_paths", risk_abl)


if __name__ == "__main__":
    main()
