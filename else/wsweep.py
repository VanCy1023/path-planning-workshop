"""Speed-risk trade-off of weighted A*: sweep the heuristic inflation w."""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_experiments as R  # noqa: E402
from algorithms import PathPlanners  # noqa: E402

WEIGHTS = [1.0, 1.1, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0]


def main():
    t = np.load(os.path.join(R.AREAS["Low"], "env_tensor_4D_v2.npy"), mmap_mode="r")
    out = {}
    for label, idx in R.TIME_INDEX.items():
        grid = R.coarsen(np.asarray(t[idx]))
        start = R.nearest_valid(R.START, grid)
        goal = R.nearest_valid(R.GOAL, grid)
        rows = []
        for w in WEIGHTS:
            planner = PathPlanners(grid, R.GRID_RES, seed=0)
            path, dt, nodes = planner.wa_star(start, goal, w=w)
            m = planner.calc_metrics(path)
            rows.append(dict(w=w, nodes=int(nodes), time_s=float(dt), pl_m=m["pl_m"],
                             rc=m["rc"], rc_norm=m["rc_norm"], success=m["success"]))
            print(f"[{label}] w={w:<5} nodes={nodes:>4} t={dt:.3f}s rc={m['rc']:.1f}", flush=True)
        out[label] = rows
    with open(os.path.join(R.RES, "wsweep.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print("wrote wsweep.json")


if __name__ == "__main__":
    main()
