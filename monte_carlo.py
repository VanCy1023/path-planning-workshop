# -*- coding: utf-8 -*-
"""Monte Carlo over the population-model parameters (gamma, eta).

Each sample perturbs every gamma coefficient and every eta factor by +/-20%,
rebuilds the 08:00 risk slice in memory (mass conservation enforced), plans
with A* (distance) and Risk-A*, and records the risk reduction.
"""
import copy
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config  # noqa: E402
import rebuild_risk_model as R  # noqa: E402
from algorithms import PathPlanners  # noqa: E402

ROOT = str(config.TPR02)
STEP = 5
START = (100 // STEP, 100 // STEP, 5 // STEP)
GOAL = (900 // STEP, 850 // STEP, 60 // STEP)
GRID_RES = 10.0
N_SAMPLES = 60
TI = 1  # 08:00

OUT = os.path.join(HERE, "results", "monte_carlo.json")


def load_layers():
    sc = np.load(os.path.join(ROOT, "Layer_Shelter_Sc.npy")).astype(np.float32)
    vb = np.load(os.path.join(ROOT, "Layer_Property_Vb.npy")).astype(np.float32)
    ns = np.load(os.path.join(ROOT, "Layer_Noise_Ns.npy")).astype(np.float32)
    height = np.load(os.path.join(ROOT, "Layer_Height.npy")).astype(np.float32)
    traf = np.load(os.path.join(ROOT, "Layer_TrafRisk_0800.npy")).astype(np.float32)
    traf_scale = float(np.percentile(traf, 99.5))
    traf = np.clip(traf / max(traf_scale, 1e-9), 0.0, 1.0)
    return sc, vb, ns, height, traf


def build_slice(sc, vb, ns, height, traf, gamma, eta):
    masks = R.class_masks(vb, ns)
    floors = np.clip(height / 3.0, 1.0, 30.0)
    base = np.zeros_like(sc, dtype=np.float32)
    for name, mask in masks.items():
        base[mask] = R.CLASS_WEIGHT[name] * floors[mask]

    field = np.zeros_like(base)
    for name, mask in masks.items():
        field[mask] = base[mask] * gamma[name]
    field *= float(base.sum()) / max(float(field.sum()), 1e-9)
    field *= eta
    pop = R.gaussian_blur(field, sigma=8.0) / 100.0

    vb_max = float(vb.max()) if vb.max() > 0 else 1.0
    ns_max = float(ns.max()) if ns.max() > 0 else 1.0
    norm_vb = vb / vb_max
    norm_ns = ns / ns_max
    sc_safe = np.clip(sc, 0.01, 1.0)

    tensor = np.zeros((R.NZ, height.shape[0], height.shape[1]), dtype=np.float32)
    for k in range(R.NZ):
        z = (k + 1) * R.CELL
        term = (R.R_D * R.S_HIT * R.RHO_A) / R.M_U
        v2 = (2 * R.M_U * R.G) / (R.R_D * R.S_HIT * R.RHO_A) * (1.0 - math.exp(-z * term))
        e_imp = 0.5 * R.M_U * v2
        if z <= math.exp(R.MU_BLD):
            decay_k = 1.0
        else:
            decay_k = (1.0 / (z * R.SIGMA_BLD * math.sqrt(2 * math.pi))) * math.exp(
                -((math.log(z) - R.MU_BLD) ** 2) / (2 * R.SIGMA_BLD ** 2))
        r_f = 1.0 / (1.0 + np.sqrt(R.BETA * np.power(R.BETA / max(e_imp, 0.001), 1.0 / sc_safe)))
        air = (R.ALPHA_PED * pop * r_f + R.ALPHA_VEH * traf * r_f * 0.5
               + R.ALPHA_PROP * norm_vb * decay_k + R.ALPHA_NOISE * norm_ns * math.exp(-0.05 * z)) * 60.0
        occ = R.gaussian_blur((height >= z).astype(np.float32), sigma=0.8)
        tensor[k] = (1.0 - occ) * air + occ * R.C_MAX
    grid = np.ascontiguousarray(np.transpose(tensor, (2, 1, 0))[::STEP, ::STEP, ::STEP], dtype=np.float32) / 100.0
    return grid


def main():
    sc, vb, ns, height, traf = load_layers()
    base_gamma = R.GAMMA
    base_eta = R.ETA
    names = list(base_gamma.keys())
    rng = np.random.default_rng(20261105)
    records = []
    for i in range(N_SAMPLES):
        gamma = {n: base_gamma[n]["0800"] * float(1.0 + rng.uniform(-0.2, 0.2)) for n in names}
        eta = base_eta["0800"] * float(1.0 + rng.uniform(-0.2, 0.2))
        grid = build_slice(sc, vb, ns, height, traf, gamma, eta)
        planner = PathPlanners(grid, GRID_RES, seed=0)
        p_dist, _, n_dist = planner.astar_distance(START, GOAL)
        p_risk, _, n_risk = planner.risk_astar(START, GOAL)
        m_dist = planner.calc_metrics(p_dist)
        m_risk = planner.calc_metrics(p_risk)
        rec = dict(sample=i,
                   rc_dist=float(m_dist["rc"]), rc_risk=float(m_risk["rc"]),
                   pl_dist=float(m_dist["pl_m"]), pl_risk=float(m_risk["pl_m"]),
                   nodes_dist=int(n_dist), nodes_risk=int(n_risk),
                   reduction=float((m_dist["rc"] - m_risk["rc"]) / m_dist["rc"] * 100.0))
        records.append(rec)
        print("sample %2d  RC %.1f -> %.1f  reduction %.1f%%" % (i, rec["rc_dist"], rec["rc_risk"], rec["reduction"]), flush=True)

    red = np.array([r["reduction"] for r in records])
    summary = dict(n=N_SAMPLES,
                   mean=float(red.mean()), median=float(np.median(red)),
                   p5=float(np.percentile(red, 5)), p95=float(np.percentile(red, 95)),
                   min=float(red.min()), max=float(red.max()),
                   always_better=bool((red > 0).all()))
    json.dump(dict(summary=summary, records=records), open(OUT, "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
