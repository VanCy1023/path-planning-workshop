# -*- coding: utf-8 -*-
"""Physical exposure metrics along the planned paths, used in the ablation discussion."""
import json
import os

import numpy as np

import config  # noqa: E402

HERE = config.REPO_ROOT
TPR = str(config.TPR02)
ABL = str(config.ABLATION_DIR)
STEP = 5
RES = 10.0

records = json.load(open(os.path.join(HERE, "results", "ablation.json"), encoding="utf-8"))["records"]


def coarsen_xy(arr, factor=STEP):
    n = arr.shape[0] // factor
    return arr[:n * factor, :n * factor].reshape(n, factor, n, factor).mean(axis=(1, 3))


pop2d = np.load(os.path.join(TPR, "Layer_PopRisk_v2_1800.npy")).astype(np.float32)  # 1000x1000 (y,x)
pop_small = coarsen_xy(pop2d)          # 200x200
full = np.load(os.path.join(TPR, "env_tensor_4D_v2.npy"), mmap_mode="r")
full18 = np.asarray(full[2])           # z,y,x at 2 m
full_small = coarse = full18.reshape(15, 5, 200, 5, 200, 5).mean(axis=(1, 3, 5))

print("grid shapes", pop_small.shape, full_small.shape)


def exposure(path):
    """person-metres overflown and peak risk met, sampled every grid step."""
    exp = 0.0
    peak = 0.0
    pts = np.asarray(path, dtype=float)
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) * 2)))
        for t in np.linspace(0, 1, n, endpoint=False):
            q = a + (b - a) * t
            i, j, k = (int(round(v)) for v in q)
            i = min(max(i, 0), 199); j = min(max(j, 0), 199); k = min(max(k, 0), 14)
            exp += float(pop_small[j, i]) * RES
            peak = max(peak, float(full_small[k, j, i]))
    return exp, peak


rows = []
for cfg in ("Static", "Pop", "Full"):
    for planner in ("A*-dist", "A*"):
        cand = [r for r in records if r["case"] == cfg and r["planner"] == planner and r["success"]]
        if not cand:
            continue
        e, p = exposure(cand[0]["path"])
        rows.append((cfg, planner, e, p, cand[0]["rc"]))

print("%-8s %-8s %14s %10s %8s" % ("config", "planner", "exposure", "peak", "RC"))
for r in rows:
    print("%-8s %-8s %14.0f %10.3f %8.1f" % r)

json.dump([dict(config=a, planner=b, exposure=c, peak=d, rc=e) for a, b, c, d, e in rows],
          open(os.path.join(HERE, "results", "exposure.json"), "w", encoding="utf-8"), indent=1)
