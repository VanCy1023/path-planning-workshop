"""Run the three experiment groups with the fixed planner core.

Groups
  time      : TPR02, 04:00 / 08:00 / 18:00 slices
  density   : TPR02 / TPR03 / TPR04 at 18:00
  ablation  : static / static+population / full tensors (TPR04 area, 18:00)

Every run is written to results/*.json; nothing is transcribed by hand.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config  # noqa: E402
from algorithms import PathPlanners, RISK_OBSTACLE  # noqa: E402

RES = os.path.join(HERE, "results")
STEP = 5
GRID_RES = 2.0 * STEP
START = (100 // STEP, 100 // STEP, 5 // STEP)
GOAL = (900 // STEP, 850 // STEP, 60 // STEP)
RRT_SEEDS = 10
PSO_SEEDS = 5

AREAS = {
    "Low": str(config.TPR02),
    "Medium": str(config.TPR03),
    "High": str(config.TPR04),
}
ABLATION = {
    "Static": str(config.ABLATION_DIR / "env_tensor_abl_static.npy"),
    "Pop": str(config.ABLATION_DIR / "env_tensor_abl_pop.npy"),
    "Full": str(config.ABLATION_DIR / "env_tensor_abl_full.npy"),
}
TIME_INDEX = {"0400": 0, "0800": 1, "1800": 2}


def nearest_valid(p, grid):
    nx, ny, nz = grid.shape
    if grid[p] < RISK_OBSTACLE:
        return p
    for r in range(1, 60):
        for dz in range(-3, 4):
            for dy in range(-r, r + 1):
                for dx in (-r, r):
                    q = (p[0] + dx, p[1] + dy, p[2] + dz)
                    if 0 <= q[0] < nx and 0 <= q[1] < ny and 0 <= q[2] < nz and grid[q] < RISK_OBSTACLE:
                        return q
    raise RuntimeError("no valid start/goal")


def coarsen(slice_zyx):
    return np.ascontiguousarray(np.transpose(slice_zyx, (2, 1, 0))[::STEP, ::STEP, ::STEP], dtype=np.float32) / 100.0


def run_one(grid, start, goal, name, seed):
    planner = PathPlanners(grid, GRID_RES, seed=seed)
    if name == "A*-dist":
        path, dt, nodes = planner.astar_distance(start, goal)
    elif name == "A*":
        path, dt, nodes = planner.risk_astar(start, goal)
    elif name == "PSO":
        path, dt, nodes = planner.pso(start, goal)
    elif name == "RRT*":
        path, dt, nodes = planner.rrt_star(start, goal, max_iter=2500)
    else:
        raise ValueError(name)
    metrics = planner.calc_metrics(path)
    return dict(planner=name, seed=seed, nodes=int(nodes), time_s=float(dt),
                path=[[int(v) for v in p] for p in path], **metrics)


def run_group(label, grids, out_name):
    records = []
    for key, grid in grids.items():
        start = nearest_valid(START, grid)
        goal = nearest_valid(GOAL, grid)
        free = float((grid < RISK_OBSTACLE).mean())
        print(f"[{out_name}] {key}: grid={grid.shape} free={free:.3f} start={start} goal={goal}", flush=True)
        for name in ("A*-dist", "A*", "PSO", "RRT*"):
            seeds = range(RRT_SEEDS) if name == "RRT*" else (range(PSO_SEEDS) if name == "PSO" else [0])
            for seed in seeds:
                t0 = time.time()
                rec = run_one(grid, start, goal, name, seed)
                rec.update(group=out_name, case=key, grid_shape=list(grid.shape), grid_res=GRID_RES,
                           free_share=free, start=list(start), goal=list(goal))
                records.append(rec)
                print(f"  {name:<9} seed={seed:<2} ok={rec['success']} t={rec['time_s']:.2f}s "
                      f"nodes={rec['nodes']} rc={rec.get('rc', float('nan')):.1f}", flush=True)
        # flush after each case so an interruption keeps partial results
        write(out_name, records)
    return records


def write(name, records):
    os.makedirs(RES, exist_ok=True)
    payload = dict(created=datetime.now().isoformat(timespec="seconds"), grid_res=GRID_RES,
                   step=STEP, rrt_seeds=RRT_SEEDS, records=records)
    with open(os.path.join(RES, f"{name}.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"

    if which in ("all", "time"):
        tensor = np.load(os.path.join(AREAS["Low"], "env_tensor_4D_v2.npy"), mmap_mode="r")
        grids = {t: coarsen(np.asarray(tensor[i])) for t, i in TIME_INDEX.items()}
        run_group("time", grids, "time")

    if which in ("all", "density"):
        grids = {}
        for name in ("Low", "Medium", "High"):
            tensor = np.load(os.path.join(AREAS[name], "env_tensor_4D_v2.npy"), mmap_mode="r")
            grids[name] = coarsen(np.asarray(tensor[2]))
        run_group("density", grids, "density")

    if which in ("all", "ablation"):
        grids = {}
        for name, path in ABLATION.items():
            arr = np.load(path, mmap_mode="r")
            grids[name] = coarsen(np.asarray(arr[2]) if arr.ndim == 4 else np.asarray(arr))
        run_group("ablation", grids, "ablation")

    print("done")


if __name__ == "__main__":
    main()
