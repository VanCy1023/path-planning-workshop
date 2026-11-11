"""Replace the RRT* records with a properly sampled anytime RRT* run.

The first pass used 2 500 iterations, which is far below what a 2 km problem
needs; the paths were almost straight and carried 20-50x the optimal risk.
This script re-runs only RRT* with 8 000 iterations and 10 seeds per case.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_experiments as R  # noqa: E402
from algorithms import PathPlanners  # noqa: E402

SEEDS = 10
ITER = 8000


def grids_for(group):
    if group == "time":
        t = np.load(os.path.join(R.AREAS["Low"], "env_tensor_4D_v2.npy"), mmap_mode="r")
        return {k: R.coarsen(np.asarray(t[i])) for k, i in R.TIME_INDEX.items()}
    if group == "density":
        out = {}
        for name in ("Low", "Medium", "High"):
            t = np.load(os.path.join(R.AREAS[name], "env_tensor_4D_v2.npy"), mmap_mode="r")
            out[name] = R.coarsen(np.asarray(t[2]))
        return out
    out = {}
    for k, p in R.ABLATION.items():
        arr = np.load(p, mmap_mode="r")
        out[k] = R.coarsen(np.asarray(arr[2]) if arr.ndim == 4 else np.asarray(arr))
    return out


def main():
    groups = sys.argv[1:] or ["time", "density", "ablation"]
    for group in groups:
        path = os.path.join(R.RES, f"{group}.json")
        if not os.path.exists(path):
            print("skip", group)
            continue
        payload = json.load(open(path, encoding="utf-8"))
        records = [r for r in payload["records"] if r["planner"] != "RRT*"]
        grids = grids_for(group)
        for case, grid in grids.items():
            start = R.nearest_valid(R.START, grid)
            goal = R.nearest_valid(R.GOAL, grid)
            free = float((grid < R.RISK_OBSTACLE).mean())
            for seed in range(SEEDS):
                planner = PathPlanners(grid, R.GRID_RES, seed=seed)
                p, dt, nodes = planner.rrt_star(start, goal, max_iter=ITER)
                m = planner.calc_metrics(p)
                records.append(dict(planner="RRT*", seed=seed, nodes=int(nodes), time_s=float(dt),
                                    path=[[int(v) for v in q] for q in p], **m,
                                    group=group, case=case, grid_shape=list(grid.shape),
                                    grid_res=R.GRID_RES, free_share=free,
                                    start=list(start), goal=list(goal)))
                print(f"[{group}] {case} RRT* seed={seed} ok={m['success']} t={dt:.1f}s "
                      f"nodes={nodes} rc={m.get('rc', float('nan')):.1f}", flush=True)
            payload["records"] = records
            R.write(group, records)
            print(f"[{group}] {case} written", flush=True)


if __name__ == "__main__":
    main()
