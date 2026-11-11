"""Time-indexed risk evaluation and departure-time sweep.

The three retained slices (04:00, 08:00, 18:00) are interpolated linearly on the
24 h clock.  A path is evaluated with the risk met at the *arrival* time of each
point, t(s) = t0 + s / v, instead of with a single snapshot.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config  # noqa: E402
from algorithms import PathPlanners, RISK_OBSTACLE  # noqa: E402

RES = os.path.join(HERE, "results")
TENSOR = str(config.TPR02 / config.TENSOR_NAME)
STEP = 5
GRID_RES = 10.0
SPEED = 10.0  # m/s
ANCHORS = [4.0, 8.0, 18.0, 28.0]
START = (20, 20, 1)
GOAL = (180, 170, 12)


def coarsen(slice_zyx):
    return np.ascontiguousarray(np.transpose(slice_zyx, (2, 1, 0))[::STEP, ::STEP, ::STEP], dtype=np.float32) / 100.0


def segment(t):
    t = t + 24 if t < ANCHORS[0] else t
    for i in range(len(ANCHORS) - 1):
        if ANCHORS[i] <= t <= ANCHORS[i + 1]:
            a = (t - ANCHORS[i]) / (ANCHORS[i + 1] - ANCHORS[i])
            return i, float(a)
    return len(ANCHORS) - 2, 1.0


def field_at(grids, t):
    i, a = segment(t)
    return (1.0 - a) * grids[i] + a * grids[min(i + 1, 2)]


def risk_at(grids, t, x, y, z):
    i, a = segment(t)
    lo = grids[i][x, y, z]
    hi = grids[min(i + 1, 2)][x, y, z]
    return float((1.0 - a) * lo + a * hi)


def evaluate(path, grids, t0, speed=SPEED):
    """Risk integral with arrival-time sampling, and the snapshot counterpart."""
    pts = np.asarray(path, dtype=float)
    snap = field_at(grids, t0)
    rc_time = rc_snap = 0.0
    dist = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(round(np.linalg.norm(b - a))))
        for k in range(n):
            q = a + (b - a) * (k / n)
            x, y, z = int(round(q[0])), int(round(q[1])), int(round(q[2]))
            step_m = np.linalg.norm(b - a) / n * GRID_RES
            t = t0 + dist / (speed * 3600.0)  # hours after departure
            rc_time += risk_at(grids, t, x, y, z) * step_m
            rc_snap += float(snap[x, y, z]) * step_m
            dist += step_m
    return rc_time, rc_snap, dist


def main():
    tensor = np.load(TENSOR, mmap_mode="r")
    grids = [coarsen(np.asarray(tensor[i])) for i in range(3)]

    records = []
    best = None
    t0 = 6.0
    while t0 <= 21.999:
        grid = field_at(grids, min(t0, 23.999))
        planner = PathPlanners(np.ascontiguousarray(grid), GRID_RES, seed=0)
        path, dt, nodes = planner.risk_astar(START, GOAL)
        if path:
            rc_time, rc_snap, length = evaluate(path, grids, t0)
            rec = dict(t0=t0, success=True, pl_m=length, rc_time=rc_time, rc_snapshot=rc_snap,
                       gap_pct=(rc_time - rc_snap) / rc_snap * 100.0, nodes=int(nodes),
                       time_s=float(dt), path=[[int(v) for v in p] for p in path])
            records.append(rec)
            if best is None or rc_time < best["rc_time"]:
                best = rec
        t0 += 0.25

    # fixed path planned at 08:00, evaluated for every departure time
    fixed_path, _, _ = PathPlanners(grids[1], GRID_RES, seed=0).risk_astar(START, GOAL)
    fixed = []
    for h in np.arange(6.0, 22.0 + 1e-9, 0.5):
        rc_time, rc_snap, _ = evaluate(fixed_path, grids, float(h))
        fixed.append(dict(t0=float(h), rc_time=rc_time, rc_snapshot=rc_snap))

    out = dict(speed_m_s=SPEED, anchors=ANCHORS, replanned=records, fixed_path=fixed,
               best=best)
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "time_consistency.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print("best departure %.2f h  rc_time=%.1f  rc_snap=%.1f  gap=%.1f%%" % (
        best["t0"], best["rc_time"], best["rc_snapshot"], best["gap_pct"]))
    print("wrote", os.path.join(RES, "time_consistency.json"))


if __name__ == "__main__":
    main()
