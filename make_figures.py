"""Build the paper figures from results/*.json (no hand-edited numbers)."""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
import matplotlib.colors

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

COLORS = {"A*-dist": "#111111", "A*": "#6a1b9a", "PSO": "#2e7d32", "RRT*": "#1565c0"}
ORDER = ["A*-dist", "A*", "PSO", "RRT*"]
RES_M = 10.0


def load(name):
    with open(os.path.join(RES, f"{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)["records"]


def pick(records, case, planner):
    rows = [r for r in records if r["case"] == case and r["planner"] == planner and r["success"]]
    if not rows:
        return None
    rows.sort(key=lambda r: r["rc"])
    return rows[len(rows) // 2]


def draw_paths(records, cases, titles, filename, elev=26, azim=-60):
    fig = plt.figure(figsize=(11.2, 3.7))
    for i, (case, title) in enumerate(zip(cases, titles), start=1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        for planner in ORDER:
            row = pick(records, case, planner)
            if row is None:
                continue
            pts = np.asarray(row["path"], dtype=float) * RES_M
            if planner == "A*-dist":
                # Dijkstra and A* coincide; draw Dijkstra as a wide halo so both show.
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=COLORS[planner], linewidth=5.0,
                        alpha=0.30, label="A* (distance cost)", solid_capstyle="round")
            else:
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=COLORS[planner], linewidth=1.8,
                        label=planner, solid_capstyle="round")
        start = np.asarray(records[0]["start"], dtype=float) * RES_M
        goal = np.asarray(records[0]["goal"], dtype=float) * RES_M
        ax.scatter(*start, marker="^", s=55, color="#2e7d32", edgecolor="white", linewidth=0.4)
        ax.scatter(*goal, marker="*", s=110, color="#f9a825", edgecolor="white", linewidth=0.4)
        ax.set_xlim(0, 2000); ax.set_ylim(0, 2000); ax.set_zlim(0, 150)
        ax.set_zticks([0, 50, 100, 150])
        ax.set_box_aspect((1, 1, 0.16))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=10, pad=0)
        ax.tick_params(labelsize=7, pad=0)
        ax.set_xlabel("X (m)", fontsize=7, labelpad=-2)
        ax.set_ylabel("Y (m)", fontsize=7, labelpad=-2)
        ax.set_zlabel("Z (m)", fontsize=7, labelpad=-2)
        ax.grid(True, linewidth=0.3, alpha=0.5)
        if i == 1:
            ax.legend(loc="upper left", fontsize=7, frameon=True, framealpha=0.9)
    fig.tight_layout()
    for ext in ("png",):
        fig.savefig(os.path.join(OUT, f"{filename}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def risk_map(slice_zyx, clip=38.0, factor=10, fill=4.0):
    """Reproduce the original 20 m air-risk map.

    Values >= clip are building cells and their high-risk halo; they are removed
    before the column maximum so that the map shows the smooth background risk
    rather than isolated spikes.  Columns that are entirely building are filled
    with the background level.
    """
    arr = np.transpose(slice_zyx, (2, 1, 0)).astype(np.float32)   # (x, y, z) at 2 m
    arr[arr >= clip] = np.nan
    proj = np.nanmax(arr, axis=2)                                  # 1000 x 1000
    n = proj.shape[0] // factor
    out = np.nanmean(proj.reshape(n, factor, n, factor), axis=(1, 3))
    out = np.nan_to_num(out, nan=fill)
    k = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    k = k / k.sum()
    out = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, out)
    out = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, out)
    return out


def draw_risk(maps, titles, filename):
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.5))
    pooled = np.concatenate([m.ravel() for m in maps])
    valid = pooled[pooled > 4.5]
    vmax = float(np.percentile(valid if len(valid) else pooled, 98))
    norm = matplotlib.colors.Normalize(vmin=2.0, vmax=vmax)
    for ax, data, title in zip(axes, maps, titles):
        im = ax.imshow(data, origin="lower", extent=(0, 2000, 0, 2000), cmap="jet",
                       norm=norm, interpolation="nearest")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("X (m)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal")
        ax.grid(True, color="#777777", linewidth=0.35, alpha=0.55)
    axes[0].set_ylabel("Y (m)", fontsize=8)
    fig.colorbar(im, ax=axes, shrink=0.75, pad=0.015, label="Discrete air-block risk (20 m × 20 m)")
    for ext in ("png",):
        fig.savefig(os.path.join(OUT, f"{filename}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    time_rows = load("time")
    draw_paths(time_rows, ["0400", "0800", "1800"],
               ["04:00", "08:00", "18:00"], "fig_time_paths")

    try:
        density_rows = load("density")
        draw_paths(density_rows, ["Low", "Medium", "High"],
                   ["Low density", "Medium density", "High density"], "fig_density_paths")
    except FileNotFoundError:
        pass

    try:
        ablation_rows = load("ablation")
        draw_paths(ablation_rows, ["Static", "Pop", "Full"],
                   ["Static", "Static + population", "Full multi-source"], "fig_ablation_paths")
    except FileNotFoundError:
        pass

    tensor = np.load(str(config.TPR02 / config.TENSOR_NAME), mmap_mode="r")
    draw_risk([risk_map(tensor[i]) for i in range(3)], ["04:00", "08:00", "18:00"], "fig_time_risk")

    areas = {"Low": str(config.TPR02 / config.TENSOR_NAME),
             "Medium": str(config.TPR03 / config.TENSOR_NAME),
             "High": str(config.TPR04 / config.TENSOR_NAME)}
    maps = []
    for name in ("Low", "Medium", "High"):
        arr = np.load(areas[name], mmap_mode="r")
        maps.append(risk_map(np.asarray(arr[2])))
    draw_risk(maps, ["Low density", "Medium density", "High density"], "fig_density_risk")
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
