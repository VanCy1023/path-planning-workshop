"""Quick timing and validity probe before the full run."""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import config  # noqa: E402
from algorithms import PathPlanners, RISK_OBSTACLE

TENSOR = str(config.TPR02 / "env_tensor_4D_Final.npy")
STEP = 5
START = (100 // STEP, 100 // STEP, 5 // STEP)
GOAL = (900 // STEP, 850 // STEP, 60 // STEP)


def nearest_valid(p, grid):
    nx, ny, nz = grid.shape
    if grid[p] < RISK_OBSTACLE:
        return p
    for r in range(1, 40):
        for dz in range(-2, 3):
            for dy in range(-r, r + 1):
                for dx in (-r, r):
                    q = (p[0] + dx, p[1] + dy, p[2] + dz)
                    if 0 <= q[0] < nx and 0 <= q[1] < ny and 0 <= q[2] < nz and grid[q] < RISK_OBSTACLE:
                        return q
    raise RuntimeError("no valid point")


def main():
    t = np.load(TENSOR, mmap_mode="r")
    grid = np.ascontiguousarray(np.transpose(t[1], (2, 1, 0))[::STEP, ::STEP, ::STEP], dtype=np.float32)
    print("grid", grid.shape, "res", 2.0 * STEP, "free", float((grid < RISK_OBSTACLE).mean()))
    s = nearest_valid(START, grid)
    g = nearest_valid(GOAL, grid)
    print("start", START, "->", s, "| goal", GOAL, "->", g)

    p = PathPlanners(grid, grid_res=2.0 * STEP, seed=0)
    t0 = time.time(); path, dt, n = p.risk_astar(s, g)
    print("Risk-A*  success=%s t=%.1fs nodes=%d len=%d" % (bool(path), dt, n, len(path)))
    if path:
        print("  ", p.calc_metrics(path))
    t0 = time.time(); path, dt, n = p.rrt_star(s, g, max_iter=8000)
    print("RRT*     success=%s t=%.1fs nodes=%d len=%d" % (bool(path), dt, n, len(path)))
    if path:
        print("  ", p.calc_metrics(path))


if __name__ == "__main__":
    main()
