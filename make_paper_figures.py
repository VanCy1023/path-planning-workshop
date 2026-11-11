"""Generate the final figure set (figure1 ... figure10) with uniform styling."""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator


import config  # noqa: E402
from make_figures import COLORS, ORDER, load, pick, risk_map

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

RES_M = 10.0
TPR = str(config.TPR02)
TENSOR = os.path.join(TPR, "env_tensor_4D_v2.npy")
AREAS = {
    "Low": os.path.join(TPR, "env_tensor_4D_v2.npy"),
    "Medium": str(config.TPR03 / config.TENSOR_NAME),
    "High": str(config.TPR04 / config.TENSOR_NAME),
}
ABL = {
    "Static": str(config.ABLATION_DIR / "env_tensor_abl_static.npy"),
    "Pop": str(config.ABLATION_DIR / "env_tensor_abl_pop.npy"),
    "Full": str(config.ABLATION_DIR / "env_tensor_abl_full.npy"),
}
TIMES = {"0400": 0, "0800": 1, "1800": 2}
LABEL = {"A*-dist": "A*", "A*": "Risk-A*", "PSO": "PSO", "RRT*": "RRT*"}

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def risk_panels(maps, titles, name, cbar_label="Discrete air-block risk (20 m × 20 m)", vmin=2.0):
    fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.0))
    pooled = np.concatenate([m.ravel() for m in maps])
    valid = pooled[pooled > vmin + 0.5]
    vmax = float(np.percentile(valid if len(valid) else pooled, 98))
    for ax, data, title in zip(axes, maps, titles):
        im = ax.imshow(data, origin="lower", extent=(0, 2000, 0, 2000), cmap="jet",
                       vmin=vmin, vmax=vmax, interpolation="nearest")
        ax.set_title(title)
        ax.set_xlabel("X (m)")
        ax.set_aspect("equal")
        ax.xaxis.set_major_locator(MultipleLocator(500))
        ax.yaxis.set_major_locator(MultipleLocator(500))
        ax.grid(True, color="#777777", linewidth=0.35, alpha=0.55)
    axes[0].set_ylabel("Y (m)")
    fig.subplots_adjust(wspace=0.30, left=0.05, right=0.92, bottom=0.13, top=0.90)
    fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label=cbar_label)
    save(fig, name)


def paths_2d(rows, cases, titles, name, risk_by_case):
    fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.0))
    pooled = np.concatenate([m.ravel() for m in risk_by_case.values()])
    valid = pooled[pooled > 2.5]
    vmax = float(np.percentile(valid if len(valid) else pooled, 98))
    for ax, case in zip(axes, cases):
        im = ax.imshow(risk_by_case[case], origin="lower", extent=(0, 2000, 0, 2000),
                  cmap="jet", vmin=2, vmax=vmax, interpolation="nearest")
        for planner in ORDER:
            row = pick(rows, case, planner)
            if row is None:
                continue
            pts = np.asarray(row["path"], dtype=float) * RES_M
            ax.plot(pts[:, 0], pts[:, 1], color=COLORS[planner], linewidth=1.9,
                    label=LABEL[planner], solid_capstyle="round", zorder=5,
                    linestyle="--" if planner == "A*-dist" else "-")
        start = np.asarray(rows[0]["start"], dtype=float) * RES_M
        goal = np.asarray(rows[0]["goal"], dtype=float) * RES_M
        ax.scatter(start[0], start[1], marker="^", s=80, color="white", edgecolor="black", linewidth=0.8, zorder=6)
        ax.scatter(goal[0], goal[1], marker="*", s=150, color="#ffd600", edgecolor="black", linewidth=0.8, zorder=6)
        ax.set_title(case)
        ax.set_xlabel("X (m)")
        ax.set_aspect("equal")
        ax.xaxis.set_major_locator(MultipleLocator(500))
        ax.yaxis.set_major_locator(MultipleLocator(500))
        ax.grid(True, color="#555555", linewidth=0.35, alpha=0.5)
    axes[0].set_ylabel("Y (m)")
    axes[0].legend(loc="upper left", frameon=True, framealpha=0.92)
    fig.subplots_adjust(wspace=0.30, left=0.05, right=0.92, bottom=0.13, top=0.90)
    fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label="Discrete air-block risk (20 m × 20 m)")
    save(fig, name)


def paths_3d(rows, cases, name):
    fig = plt.figure(figsize=(12.2, 5.4))
    for i, case in enumerate(cases, start=1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        for planner in ORDER:
            row = pick(rows, case, planner)
            if row is None:
                continue
            pts = np.asarray(row["path"], dtype=float) * RES_M
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=COLORS[planner], linewidth=1.6,
                    label=LABEL[planner], linestyle="--" if planner == "A*-dist" else "-")
        start = np.asarray(rows[0]["start"], dtype=float) * RES_M
        goal = np.asarray(rows[0]["goal"], dtype=float) * RES_M
        ax.scatter(start[0], start[1], start[2], marker="^", s=50, color="white", edgecolor="black", linewidth=0.6)
        ax.scatter(goal[0], goal[1], goal[2], marker="*", s=90, color="#ffd600", edgecolor="black", linewidth=0.6)
        ax.set_xlim(0, 2000); ax.set_ylim(0, 2000); ax.set_zlim(0, 150)
        ax.set_box_aspect((1, 1, 0.35))
        ax.view_init(elev=26, azim=-58)
        ax.set_title(case, pad=0)
        ax.set_xlabel("X (m)", labelpad=3)
        ax.set_ylabel("Y (m)", labelpad=3)
        ax.set_zlabel("Z (m)", labelpad=8)
        ax.tick_params(pad=1)
        ax.set_zticks([0, 50, 100, 150])
        ax.grid(True, linewidth=0.35, alpha=0.5)
        if i == 1:
            ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.06, top=0.90, wspace=0.02)
    save(fig, name)


def surfaces_3d(maps, titles, name):
    fig = plt.figure(figsize=(11.4, 3.8))
    xx, yy = np.meshgrid(np.linspace(0, 2000, maps[0].shape[1]), np.linspace(0, 2000, maps[0].shape[0]))
    for i, (data, title) in enumerate(zip(maps, titles), start=1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        ax.plot_surface(xx, yy, data, cmap="jet", linewidth=0, antialiased=False)
        ax.set_zlim(0, 30)
        ax.view_init(elev=35, azim=-55)
        ax.set_title(title, pad=0)
        ax.set_xlabel("X (m)", labelpad=3)
        ax.set_ylabel("Y (m)", labelpad=3)
        ax.set_zlabel("Risk", labelpad=10)
        ax.tick_params(pad=1)
        ax.set_zticks([0, 10, 20, 30])
        ax.set_box_aspect((1, 1, 0.55))
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.06, top=0.90, wspace=0.02)
    save(fig, name)


def layer_panels(files, titles, name, label, vmin=None, vmax=None, smooth=0):
    maps = []
    for f in files:
        a = np.load(f, mmap_mode="r")
        arr = np.asarray(a, dtype=np.float32)
        n = arr.shape[0] // 10
        m = arr.reshape(n, 10, n, 10).mean(axis=(1, 3))
        if block > 1:
            m = m.reshape(n // block, block, n // block, block).mean(axis=(1, 3))
        maps.append(gaussian_blur(m, sigma))
    fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.0))
    pooled = np.concatenate([m.ravel() for m in maps])
    if vmin is None:
        vmin = float(np.percentile(pooled, 2))
    if vmax is None:
        vmax = float(np.percentile(pooled, 98))
    for ax, data, title in zip(axes, maps, titles):
        im = ax.imshow(data, origin="lower", extent=(0, 2000, 0, 2000), cmap="jet",
                       vmin=vmin, vmax=vmax, interpolation="nearest")
        ax.set_title(title)
        ax.set_xlabel("X (m)")
        ax.set_aspect("equal")
        ax.xaxis.set_major_locator(MultipleLocator(500))
        ax.yaxis.set_major_locator(MultipleLocator(500))
        ax.grid(True, color="#777777", linewidth=0.35, alpha=0.55)
    axes[0].set_ylabel("Y (m)")
    fig.subplots_adjust(wspace=0.30, left=0.05, right=0.92, bottom=0.13, top=0.90)
    fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, label=label)
    save(fig, name)


def profiles(rows, name):
    def cumulative(path, grid):
        pts = np.asarray(path, dtype=float)
        xs, ys, s, rc = [], [], 0.0, 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(1, int(round(np.linalg.norm(b - a))))
            for k in range(n):
                q = a + (b - a) * (k / n)
                x, y, z = (int(round(v)) for v in q)
                rc += float(grid[x, y, z]) * RES_M
                s += float(np.linalg.norm(b - a)) / n * RES_M
                xs.append(s); ys.append(rc)
        return np.asarray(xs), np.asarray(ys)

    t = np.load(TENSOR, mmap_mode="r")
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.6))
    for ax, (case, idx) in zip(axes, TIMES.items()):
        grid = np.ascontiguousarray(np.transpose(np.asarray(t[idx]), (2, 1, 0))[::5, ::5, ::5], dtype=np.float32) / 100.0
        for planner in ORDER:
            row = pick(rows, case, planner)
            if row is None:
                continue
            x, y = cumulative(row["path"], grid)
            ax.plot(x, y, color=COLORS[planner], linewidth=1.8,
                    linestyle="--" if planner == "A*-dist" else "-", label=LABEL[planner])
        ax.set_title(case)
        ax.set_xlabel("Distance along path (m)")
        ax.set_xlim(0, 2400)
        ax.grid(True, linewidth=0.35, alpha=0.5)
    axes[0].set_ylabel("Cumulative risk $RC$")
    axes[0].legend(frameon=True, framealpha=0.92)
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.06, top=0.90, wspace=0.02)
    save(fig, name)




def gaussian_blur(image, sigma):
    radius = max(1, int(3 * sigma))
    x = np.arange(-radius, radius + 1)
    k = np.exp(-(x ** 2) / (2 * sigma ** 2)); k /= k.sum()
    out = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, image)
    out = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, out)
    return out


def surfaces_layers(files, titles, name, label, block=2, sigma=1.2):
    """3-D surface of a 2-D risk layer with its projection on the base plane."""
    maps = []
    for f in files:
        arr = np.asarray(np.load(f, mmap_mode="r"), dtype=np.float32)
        n = arr.shape[0] // 10
        m = arr.reshape(n, 10, n, 10).mean(axis=(1, 3))
        if block > 1:
            m = m.reshape(n // block, block, n // block, block).mean(axis=(1, 3))
        maps.append(gaussian_blur(m, sigma))
    pooled = np.concatenate([m.ravel() for m in maps])
    vmax = float(np.percentile(pooled, 99.5))
    maps = [np.clip(m, 0, vmax) for m in maps]
    xx, yy = np.meshgrid(np.linspace(0, 2000, maps[0].shape[1]), np.linspace(0, 2000, maps[0].shape[0]))
    fig = plt.figure(figsize=(11.8, 4.7))
    for i, (data, title) in enumerate(zip(maps, titles), start=1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        ax.plot_surface(xx, yy, data, cmap="jet", vmin=0, vmax=vmax, linewidth=0, antialiased=False)
        ax.contourf(xx, yy, data, zdir="z", offset=0, levels=18, cmap="jet", vmin=0, vmax=vmax, alpha=0.85)
        ax.set_zlim(0, vmax)
        ax.view_init(elev=32, azim=-60)
        ax.set_title(title, pad=0)
        ax.set_xticks([0, 1000, 2000]); ax.set_yticks([0, 1000, 2000])
        if i == 1:
            ax.set_xlabel("X (m)", labelpad=1)
            ax.set_ylabel("Y (m)", labelpad=1)
        ax.set_box_aspect((1, 1, 0.45))
        ax.tick_params(pad=0, labelsize=8)
    fig.subplots_adjust(left=0.05, right=0.93, bottom=0.07, top=0.90, wspace=0.10)
    save(fig, name)


def main():
    t = np.load(TENSOR, mmap_mode="r")
    risk_time = {k: risk_map(np.asarray(t[i])) for k, i in TIMES.items()}
    risk_panels([risk_time[k] for k in TIMES], ["04:00", "08:00", "18:00"], "figure1")

    surfaces_layers([os.path.join(TPR, f"Layer_PopRisk_v2_{k}.npy") for k in TIMES],
                    ["04:00", "08:00", "18:00"], "figure2", "Exposure")
    surfaces_layers([os.path.join(TPR, f"Layer_TrafRisk_{k}.npy") for k in TIMES],
                    ["04:00", "08:00", "18:00"], "figure3", "Traffic")

    time_rows = load("time")
    paths_2d(time_rows, ["0400", "0800", "1800"],
             ["04:00", "08:00", "18:00"], "figure5", risk_time)
    paths_3d(time_rows, ["0400", "0800", "1800"], "figure6")
    profiles(time_rows, "figure7")

    density_rows = load("density")
    risk_density = {k: risk_map(np.asarray(np.load(v, mmap_mode="r")[2])) for k, v in AREAS.items()}
    risk_panels([risk_density[k] for k in ("Low", "Medium", "High")],
                ["Low density", "Medium density", "High density"], "figure8")
    paths_2d(density_rows, ["Low", "Medium", "High"],
             ["Low density", "Medium density", "High density"], "figure9", risk_density)

    abl_rows = load("ablation")
    risk_abl = {k: risk_map(np.asarray(np.load(v, mmap_mode="r")[2])) for k, v in ABL.items()}
    paths_2d(abl_rows, ["Static", "Pop", "Full"],
             ["Static", "Static + population", "Full multi-source"], "figure10", risk_abl)


if __name__ == "__main__":
    main()










