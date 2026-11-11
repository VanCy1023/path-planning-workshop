import json, os, sys
import numpy as np

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402
import time_consistency as TC
payload = json.load(open(os.path.join(TC.RES, "time.json"), encoding="utf-8"))
rows = [r for r in payload["records"] if r["case"] == "0800" and r["planner"] == "A*" and r["success"]]
path = rows[0]["path"]
tensor = np.load(TC.TENSOR, mmap_mode="r")
grids = [TC.coarsen(np.asarray(tensor[i])) for i in range(3)]
for t0 in (6.5, 7.0, 7.5, 16.5, 17.5):
    out = []
    for v in (5.0, 10.0, 20.0):
        rc_t, rc_s, _ = TC.evaluate(path, grids, t0, speed=v)
        out.append("%.1f:%.2f%%" % (v, (rc_t - rc_s) / rc_s * 100))
    print("t0=%.1f  " % t0 + "  ".join(out))
