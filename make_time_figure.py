"""Figure for the departure-time / arrival-time analysis."""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)


def main():
    d = json.load(open(os.path.join(RES, "time_consistency.json"), encoding="utf-8"))
    rows = d["replanned"]
    t0 = np.array([r["t0"] for r in rows])
    rc_time = np.array([r["rc_time"] for r in rows])
    rc_snap = np.array([r["rc_snapshot"] for r in rows])

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.6))
    ax = axes[0]
    ax.plot(t0, rc_time, color="#1565c0", linewidth=1.8, marker="o", markersize=2.8, label="time-indexed cost")
    ax.plot(t0, rc_snap, color="#e65100", linewidth=1.2, linestyle="--", label="snapshot cost")
    best = int(np.argmin(rc_time))
    ax.scatter([t0[best]], [rc_time[best]], s=70, color="#2e7d32", zorder=5, label="best departure")
    ax.set_xlabel("Departure time (h)")
    ax.set_ylabel(r"Path risk cost $RC$")
    ax.set_title("(a) Departure-time sweep, replanned at every $t_0$", fontsize=10)
    ax.grid(alpha=0.3, linewidth=0.4)
    ax.legend(fontsize=7.5, frameon=True)

    ax = axes[1]
    lo, hi = min(rc_snap.min(), rc_time.min()), max(rc_snap.max(), rc_time.max())
    ax.plot([lo, hi], [lo, hi], color="#9e9e9e", linewidth=1.0, linestyle=":")
    ax.scatter(rc_snap, rc_time, s=12, color="#6a1b9a", alpha=0.85)
    ax.set_xlabel(r"Snapshot cost at $t_0$")
    ax.set_ylabel(r"Arrival-time cost")
    ax.set_title("(b) Snapshot vs. arrival-time evaluation", fontsize=10)
    ax.grid(alpha=0.3, linewidth=0.4)

    fig.tight_layout()
    for ext in ("png",):
        fig.savefig(os.path.join(OUT, f"fig_time_consistency.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote fig_time_consistency")


if __name__ == "__main__":
    main()
