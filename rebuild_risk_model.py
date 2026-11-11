"""Rebuild the population baseline and the 4D risk tensor (model v2).

Why this exists
----------------
* The submitted population layers are almost time-invariant (r = 0.996) and,
  for the medium/high-density districts, essentially flat noise (TPR03 range
  0.012-0.120, TPR04 0.006-0.028), so neither a diurnal cycle nor a
  cross-district comparison could be supported by the data.
* Traffic layers are on incompatible scales (TPR02 max ~1.0, TPR03 ~82,
  TPR04 ~105).

This script builds one consistent model for all three districts:

  population  = class_weight(land cover) * gamma(class, t) * eta(t), smoothed
  traffic     = layer / p99.5(layer)  (relative intensity per district)
  risk tensor = 0.4*pop*Rf + 0.3*traf*Rf*0.5 + 0.2*property + 0.1*noise

Outputs never overwrite the originals:
    <area>/Layer_PopRisk_v2_<time>.npy
    <area>/env_tensor_4D_v2.npy
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import config  # noqa: E402

AREAS = {
    "TPR02": str(config.TPR02),
    "TPR03": str(config.TPR03),
    "TPR04": str(config.TPR04),
}
TIMES = ("0400", "0800", "1800")

CELL = 2.0
NZ = 75
ALPHA_PED, ALPHA_VEH, ALPHA_PROP, ALPHA_NOISE = 0.4, 0.3, 0.2, 0.1
C_MAX = 100.0
M_U, G, R_D, RHO_A, S_HIT, BETA = 3.0, 9.81, 1.0, 1.225, 0.5, 34.0
MU_BLD, SIGMA_BLD = 3.2264, 0.5818

# residents per class (same units for every district)
CLASS_WEIGHT = {
    "residential": 100.0,
    "house": 90.0,
    "public": 80.0,
    "commercial": 60.0,
    "industrial": 20.0,
    "green": 1.0,
    "road": 5.0,
}

# gamma(class, t): daily redistribution between functional zones
GAMMA = {
    "residential": {"0400": 1.20, "0800": 0.80, "1800": 1.00},
    "house":       {"0400": 1.15, "0800": 0.85, "1800": 1.00},
    "commercial":  {"0400": 0.30, "0800": 1.30, "1800": 1.20},
    "public":      {"0400": 0.25, "0800": 1.25, "1800": 0.90},
    "industrial":  {"0400": 0.60, "0800": 1.10, "1800": 1.00},
    "green":       {"0400": 0.15, "0800": 0.45, "1800": 0.60},
    "road":        {"0400": 0.35, "0800": 1.00, "1800": 1.00},
}
# eta(t): outdoor-exposure fraction
ETA = {"0400": 0.35, "0800": 1.00, "1800": 0.85}


def gaussian_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    ny, nx = image.shape
    fy = np.fft.fftfreq(ny)[:, None]
    fx = np.fft.rfftfreq(nx)[None, :]
    kernel = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fy ** 2 + fx ** 2))
    return np.real(np.fft.irfft2(np.fft.rfft2(image) * kernel, s=image.shape))


def class_masks(vb: np.ndarray, ns: np.ndarray) -> dict[str, np.ndarray]:
    """Land-cover classes from the (Vb, Ns) prototype values.

    The shelter layer (Sc) uses different background conventions in the three
    districts (0.01 in TPR02, 1.0 in TPR03/TPR04), so it cannot identify the
    class on its own.  Property value Vb and noise sensitivity Ns are encoded
    with one prototype pair per class in all three districts, matching the
    mapping table of the paper.
    """
    prototypes = {
        "commercial":  (1.00, 0.40),
        "public":      (0.90, 1.00),
        "residential": (0.60, 0.90),
        "house":       (0.40, 0.80),
        "industrial":  (0.70, 0.20),
        "green":       (0.30, 0.10),
    }
    vb_r = np.round(vb, 2)
    ns_r = np.round(ns, 2)
    masks = {}
    assigned = np.zeros_like(vb, dtype=bool)
    for name, (v, n) in prototypes.items():
        m = (np.abs(vb_r - v) < 0.005) & (np.abs(ns_r - n) < 0.005)
        masks[name] = m
        assigned |= m
    # open ground (Vb = Ns = 0) and anything unmatched is treated as green space
    masks["green"] = masks["green"] | ~assigned
    return masks


def build_tensor(area: str, root: str) -> dict:
    sc = np.load(os.path.join(root, "Layer_Shelter_Sc.npy")).astype(np.float32)
    vb = np.load(os.path.join(root, "Layer_Property_Vb.npy")).astype(np.float32)
    ns = np.load(os.path.join(root, "Layer_Noise_Ns.npy")).astype(np.float32)
    height = np.load(os.path.join(root, "Layer_Height.npy")).astype(np.float32)

    masks = class_masks(vb, ns)

    # population baseline from land-cover class, identical units everywhere
    # residents scale with floor area: class weight x number of storeys
    floors = np.clip(height / 3.0, 1.0, 30.0)
    base = np.zeros_like(sc, dtype=np.float32)
    for name, mask in masks.items():
        base[mask] = CLASS_WEIGHT[name] * floors[mask]

    trafs = [np.load(os.path.join(root, f"Layer_TrafRisk_{t}.npy")).astype(np.float32) for t in TIMES]
    traf_scale = float(np.percentile(np.concatenate([t.ravel() for t in trafs]), 99.5))
    trafs = [np.clip(t / max(traf_scale, 1e-9), 0.0, 1.0) for t in trafs]

    new_pops = []
    for t in TIMES:
        field = np.zeros_like(base)
        for name, mask in masks.items():
            field[mask] = base[mask] * GAMMA[name][t]
        # mass conservation: residents are redistributed, not created or destroyed
        field *= float(base.sum()) / max(float(field.sum()), 1e-9)
        field *= ETA[t]
        new_pops.append(gaussian_blur(field, sigma=8.0))

    vb_max = float(vb.max()) if vb.max() > 0 else 1.0
    ns_max = float(ns.max()) if ns.max() > 0 else 1.0

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

    tensor = np.zeros((3, NZ, height.shape[0], height.shape[1]), dtype=np.float32)
    sc_safe = np.clip(sc, 0.01, 1.0)
    for ti in range(3):
        norm_pop = new_pops[ti] / 100.0
        norm_traf = trafs[ti]
        norm_vb = vb / vb_max
        norm_ns = ns / ns_max
        for k in range(NZ):
            z = (k + 1) * CELL
            r_f = 1.0 / (1.0 + np.sqrt(BETA * np.power(BETA / max(e_imp[k], 0.001), 1.0 / sc_safe)))
            air = (ALPHA_PED * norm_pop * r_f + ALPHA_VEH * norm_traf * r_f * 0.5
                   + ALPHA_PROP * norm_vb * decay[k] + ALPHA_NOISE * norm_ns * math.exp(-0.05 * z)) * 60.0
            occ = gaussian_blur((height >= z).astype(np.float32), sigma=0.8)
            tensor[ti, k] = (1.0 - occ) * air + occ * C_MAX

    np.save(os.path.join(root, "env_tensor_4D_v2.npy"), tensor)
    for t, p in zip(TIMES, new_pops):
        np.save(os.path.join(root, f"Layer_PopRisk_v2_{t}.npy"), p.astype(np.float32))

    report = {}
    for ti, t in enumerate(TIMES):
        free = tensor[ti][tensor[ti] < 90.0]
        report[t] = dict(pop_mean=float(new_pops[ti].mean()), pop_max=float(new_pops[ti].max()),
                         tensor_free_mean=float(free.mean()))
    return report


def main():
    report = {}
    for area, root in AREAS.items():
        print("rebuilding", area, flush=True)
        report[area] = build_tensor(area, root)
        print(" ", report[area], flush=True)
    out = str(config.RESULTS_DIR)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "rebuild_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("done")


if __name__ == "__main__":
    main()
