import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import os
import math
from scipy.ndimage import gaussian_filter
import warnings

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

warnings.filterwarnings('ignore')

SAVE_DIR = str(config.FIGURES_DIR / "A" / "c_ablation")
os.makedirs(SAVE_DIR, exist_ok=True)

BLD_SHP_PATH = str(config.VECTOR_DIR / "TPR04" / "buildings.shp")
TARGET_CRS = "EPSG:32651"
GRID_RES, NX, NY, NZ, CELL_SIZE = 2.0, 1000, 1000, 75, 2.0


def generate_static_tensor():
    print("========== 🚀 [消融组1] 启动纯静态风险张量生成 ==========")
    bld_gdf = gpd.read_file(BLD_SHP_PATH).to_crs(TARGET_CRS)
    minx, miny, maxx, maxy = bld_gdf.total_bounds
    center_x, center_y = (minx + maxx) / 2, (miny + maxy) / 2
    transform = rasterio.transform.from_origin(center_x - 1000, center_y + 1000, GRID_RES, GRID_RES)
    out_shape = (NY, NX)

    shapes_height, shapes_sc, shapes_vb, shapes_ns = [], [], [], []
    for _, row in bld_gdf.iterrows():
        geom = row['geometry']
        area = geom.area
        floors = float(row.get('FLOORS', 0) if 'FLOORS' in row else 0)
        height = float(row.get('HEIGHT', 0) if 'HEIGHT' in row else 0)
        if height == 0: height = max(15.0, floors * 3.0)
        if floors == 0: floors = max(1, int(height / 3.0))

        osm_type = str(row.get('type', '')).lower() + str(row.get('fclass', '')).lower()
        if 'commercial' in osm_type or 'retail' in osm_type or height >= 50 or floors >= 15:
            sc, vb, ns = 1.0, 1.0, 0.4
        elif area > 2500 and floors <= 3:
            sc, vb, ns = 0.5, 0.7, 0.2
        elif 'school' in osm_type or 'hospital' in osm_type or 'public' in osm_type or (
                800 < area <= 2500 and 3 <= floors <= 6):
            sc, vb, ns = 0.9, 0.9, 1.0
        elif area <= 300 and floors <= 3:
            sc, vb, ns = 0.7, 0.4, 0.8
        else:
            sc, vb, ns = 0.8, 0.6, 0.9

        shapes_height.append((geom, height))
        shapes_sc.append((geom, sc))
        shapes_vb.append((geom, vb))
        shapes_ns.append((geom, ns))

    arr_height = rasterize(shapes_height, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
    arr_sc = rasterize(shapes_sc, out_shape=out_shape, transform=transform, fill=0.01, dtype='float32')
    arr_vb = rasterize(shapes_vb, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
    arr_ns = rasterize(shapes_ns, out_shape=out_shape, transform=transform, fill=0, dtype='float32')

    ALPHA_PED, ALPHA_VEH, ALPHA_PROP, ALPHA_NOISE = 0.4, 0.3, 0.2, 0.1
    C_MAX, M_U, G, R_D, RHO_A, S_HIT, BETA = 100.0, 3.0, 9.81, 1.0, 1.225, 0.5, 34.0
    MU_BLD, SIGMA_BLD = 3.2264, 0.5818

    E_imp_list, prop_decay_list = np.zeros(NZ), np.zeros(NZ)
    for k in range(NZ):
        z_h = (k + 1) * CELL_SIZE
        v_imp_sq = (2 * M_U * G) / (R_D * S_HIT * RHO_A) * (1.0 - math.exp(-z_h * (R_D * S_HIT * RHO_A) / M_U))
        E_imp_list[k] = 0.5 * M_U * v_imp_sq
        if z_h <= math.exp(MU_BLD):
            prop_decay_list[k] = 1.0
        else:
            prop_decay_list[k] = (1.0 / (z_h * SIGMA_BLD * math.sqrt(2 * math.pi))) * math.exp(
                -((math.log(z_h) - MU_BLD) ** 2) / (2 * SIGMA_BLD ** 2))
    prop_decay_list /= np.max(prop_decay_list)

    env_tensor = np.zeros((NZ, NY, NX), dtype=np.float32)
    norm_vb = np.clip(arr_vb / (np.percentile(arr_vb, 99.9) + 1e-6), 0, 1.0)
    norm_ns = np.clip(arr_ns / (np.percentile(arr_ns, 99.9) + 1e-6), 0, 1.0)

    for k in range(NZ):
        z_h = (k + 1) * CELL_SIZE
        cost_ped, cost_veh = 0.0, 0.0
        cost_prop = norm_vb * prop_decay_list[k]
        cost_noise = norm_ns * math.exp(-0.05 * z_h)

        air_risk = (
                               ALPHA_PED * cost_ped + ALPHA_VEH * cost_veh + ALPHA_PROP * cost_prop + ALPHA_NOISE * cost_noise) * 60.0
        raw_mask = (arr_height >= z_h).astype(float)
        occupancy_ratio = gaussian_filter(raw_mask, sigma=0.8)
        env_tensor[k, :, :] = (1.0 - occupancy_ratio) * air_risk + occupancy_ratio * C_MAX

    out_path = os.path.join(SAVE_DIR, "tensor_c_static.npy")
    np.save(out_path, env_tensor)
    print(f"🎉 纯静态张量保存至: {out_path}")


if __name__ == "__main__":
    generate_static_tensor()