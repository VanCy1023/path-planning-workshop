"""Central path configuration.

Every script resolves its input/output locations through this module so the
repository stays portable.  Nothing below depends on the original machine.

Environment overrides
---------------------
PPW_DATA_DIR      root of the input data          (default: <repo>/data)
PPW_RESULTS_DIR   root of the experiment output   (default: <repo>/results)
PPW_PROJECT_DIR   original manuscript workspace   (only else/ppt/* needs it)

Expected input layout (not shipped with the repository, see data/README.md)::

    <PPW_DATA_DIR>/
        TPR02/            Layer_*.npy, env_tensor_4D_v2.npy
        TPR03/            same
        TPR04/            same
        ablation/         env_tensor_abl_{static,pop,full}.npy
        vectors/
            TPR02/osm/2/...
            TPR03/...
            TPR04/...
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

DATA_DIR = Path(os.environ.get("PPW_DATA_DIR", REPO_ROOT / "data")).expanduser().resolve()
RESULTS_DIR = Path(os.environ.get("PPW_RESULTS_DIR", REPO_ROOT / "results")).expanduser().resolve()
FIGURES_DIR = REPO_ROOT / "figures"
TABLES_DIR = REPO_ROOT / "tables"

# Only the archived slide scripts under else/ppt use this one.
PROJECT_DIR = Path(os.environ.get("PPW_PROJECT_DIR", REPO_ROOT.parent / "revision")).expanduser().resolve()

# ---------------------------------------------------------------- data roots
TPR02 = DATA_DIR / "TPR02"
TPR03 = DATA_DIR / "TPR03"
TPR04 = DATA_DIR / "TPR04"
ABLATION_DIR = DATA_DIR / "ablation"
VECTOR_DIR = DATA_DIR / "vectors"

AREAS = {"Low": TPR02, "Medium": TPR03, "High": TPR04}
TENSOR_NAME = "env_tensor_4D_v2.npy"


def ensure_out_dirs() -> None:
    """Create the output folders if a fresh checkout is missing them."""
    for d in (RESULTS_DIR, FIGURES_DIR, TABLES_DIR):
        d.mkdir(parents=True, exist_ok=True)
