"""Build the ablation tensors by switching risk terms off in the same model.

Static   : population and traffic terms removed (property + noise + buildings)
+Pop     : population added
Full     : population and traffic (identical to env_tensor_4D_v2.npy)

Using the same area, task and 18:00 slice isolates the contribution of each
risk factor; the three tensors share one scale.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config  # noqa: E402
from rebuild_risk_model import (  # noqa: E402
    ALPHA_NOISE, ALPHA_PED, ALPHA_PROP, ALPHA_VEH, CELL, CLASS_WEIGHT, C_MAX,
    ETA, GAMMA, MU_BLD, NZ, SIGMA_BLD, class_masks, gaussian_blur,
)

ROOT = str(config.TPR02)
OUT_DIR = str(config.ABLATION_DIR)
TIMES = ("0400", "0800", "1800")
M_U, G, R_D, RHO_A, S_HIT, BETA = 3.0, 9.81, 1.0, 1.225, 0.5, 34.0


def main():
    sc = np.load(os.path.join(ROOT, "Layer_Shelter_Sc.npy")).astype(np.float32)
    vb = np.load(os.path.join(ROOT, "Layer_Property_Vb.npy")).astype(np.float32)
    ns = np.load(os.path.join(ROOT, "Layer_Noise_Ns.npy")).astype(np.float32)
    height = np.load(os.path.join(ROOT, "Layer_Height.npy")).astype(np.float32)

    masks = class_masks(vb, ns)
    floors = np.clip(height / 3.0, 1.0, 30.0)
    base = np.zeros_like(sc, dtype=np.float32)
    for name, mask in masks.items():
        base[mask] = CLASS_WEIGHT[name] * floors[mask]

    pops = []
    for t in TIMES:
        field = np.zeros_like(base)
        for name, mask in masks.items():
            field[mask] = base[mask] * GAMMA[name][t]
        field *= float(base.sum()) / max(float(field.sum()), 1e-9)
        pops.append(gaussian_blur(field * ETA[t], sigma=8.0))

    trafs = [np.load(os.path.join(ROOT, f"Layer_TrafRisk_{t}.npy")).astype(np.float32) for t in TIMES]
    scale = float(np.percentile(np.concatenate([t.ravel() for t in trafs]), 99.5))
    trafs = [np.clip(t / max(scale, 1e-9), 0.0, 1.0) for t in trafs]

    e_imp = np.zeros(NZ)
    decay = np.zeros(NZ)
    for k in range(NZ):
        z = (k + 1) * CELL
        term = (R_D * S_HIT * RHO_A) / M_U
        v2 = (2 * M_U * G) / (R_D * S_HIT * RHO_A) * (1.0 - math.exp(-z * term))
        e_imp[k] = 0.5 * M_U * v2
        if z <= math.exp(MU_BLD):
            decay[k] = 1.0
        else:
            decay[k] = (1.0 / (z * SIGMA_BLD * math.sqrt(2 * math.pi))) * math.exp(
                -((math.log(z) - MU_BLD) ** 2) / (2 * SIGMA_BLD ** 2))
    decay /= decay.max()

    vb_max, ns_max = float(vb.max()), float(ns.max())
    sc_safe = np.clip(sc, 0.01, 1.0)
    variants = {"static": (0.0, 0.0), "pop": (1.0, 0.0), "full": (1.0, 1.0)}

    for name, (wp, wt) in variants.items():
        tensor = np.zeros((3, NZ, height.shape[0], height.shape[1]), dtype=np.float32)
        for ti in range(3):
            norm_pop = pops[ti] / 100.0
            norm_traf = trafs[ti]
            for k in range(NZ):
                z = (k + 1) * CELL
                r_f = 1.0 / (1.0 + np.sqrt(BETA * np.power(BETA / max(e_imp[k], 0.001), 1.0 / sc_safe)))
                air = (wp * ALPHA_PED * norm_pop * r_f + wt * ALPHA_VEH * norm_traf * r_f * 0.5
                       + ALPHA_PROP * (vb / vb_max) * decay[k]
                       + ALPHA_NOISE * (ns / ns_max) * math.exp(-0.05 * z)) * 60.0
                occ = gaussian_blur((height >= z).astype(np.float32), sigma=0.8)
                tensor[ti, k] = (1.0 - occ) * air + occ * C_MAX
        out = os.path.join(OUT_DIR, f"env_tensor_abl_{name}.npy")
        np.save(out, tensor)
        free = tensor[tensor < 90.0]
        print(f"{name:>6}: free mean {free.mean():.2f}  max {tensor.max():.1f}  -> {out}", flush=True)


if __name__ == "__main__":
    main()
