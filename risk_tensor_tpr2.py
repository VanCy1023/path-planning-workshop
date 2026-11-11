import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.warp import reproject, Resampling
import os
import math
from scipy.ndimage import gaussian_filter
import warnings

import config  # noqa: E402

warnings.filterwarnings('ignore')

WORKSPACE = str(config.TPR02)
BLD_SHP_PATH = str(config.VECTOR_DIR / "TPR02" / "osm" / "2" / "buildings_recovered_v2_proj_ready.shp")
ROAD_SHP_PATH = str(config.VECTOR_DIR / "TPR02" / "osm" / "2" / "roads_proj_ready.shp")
# 统一使用同一份全城人口数据，保证基准一致
POP_TIF_PATH = str(config.VECTOR_DIR / "TPR03" / "chn_pd_2020_1km.tif")

TARGET_CRS = "EPSG:32651"
GRID_RES = 2.0
NX, NY, NZ = 1000, 1000, 75
CELL_SIZE = 2.0

SEM_OPEN = 0
SEM_COMMERCIAL = 1
SEM_OFFICE = 2
SEM_PUBLIC = 3
SEM_RESIDENTIAL = 4

def prepare_spatial_data():
    print("[1/4] 正在加载低密度区域矢量数据...")
    bld_gdf = gpd.read_file(BLD_SHP_PATH)
    road_gdf = gpd.read_file(ROAD_SHP_PATH)

    minx, miny, maxx, maxy = road_gdf.total_bounds
    center_x, center_y = (minx + maxx) / 2, (miny + maxy) / 2
    box_minx, box_maxy = center_x - 1000, center_y + 1000

    transform = rasterio.transform.from_origin(box_minx, box_maxy, GRID_RES, GRID_RES)
    out_shape = (NY, NX)

    print("[2/4] 正在栅格化物理与社会属性...")
    shapes_height, shapes_sc, shapes_vb, shapes_ns, shapes_sem = [], [], [], [], []
    for _, row in bld_gdf.iterrows():
        geom = row['geometry']
        shapes_height.append((geom, float(row['HEIGHT'])))
        shapes_sc.append((geom, float(row['Sc'])))
        shapes_vb.append((geom, float(row['Bld_Value'])))
        shapes_ns.append((geom, float(row['Noise_S'])))

        sem_str = str(row['Inferred_T']).lower()
        if 'commercial' in sem_str: sem_val = SEM_COMMERCIAL
        elif 'office' in sem_str or 'industrial' in sem_str: sem_val = SEM_OFFICE
        elif 'public' in sem_str: sem_val = SEM_PUBLIC
        else: sem_val = SEM_RESIDENTIAL
        shapes_sem.append((geom, sem_val))

    arr_height = rasterize(shapes_height, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
    # 🌟 关键：空地背景依然是 0.01（无屋顶庇护=致死率高），但建筑已经有了正确的 Sc
    arr_sc = rasterize(shapes_sc, out_shape=out_shape, transform=transform, fill=0.01, dtype='float32')
    arr_vb = rasterize(shapes_vb, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
    arr_ns = rasterize(shapes_ns, out_shape=out_shape, transform=transform, fill=0, dtype='float32')
    arr_sem = rasterize(shapes_sem, out_shape=out_shape, transform=transform, fill=SEM_OPEN, dtype='uint8')

    print("[3/4] 正在栅格化道路网络与限速通行能力...")
    shapes_road = []
    for _, row in road_gdf.iterrows():
        if row['Q_veh'] > 0:
            geom = row['geometry'].buffer(8.0)
            shapes_road.append((geom, float(row['Q_veh'])))

    arr_road = rasterize(shapes_road, out_shape=out_shape, transform=transform, fill=0, dtype='float32')

    print("[4/4] 正在加载并对齐二维人口分布阵列...")
    arr_pop = np.zeros(out_shape, dtype='float32')
    with rasterio.open(POP_TIF_PATH) as src:
        reproject(
            source=rasterio.band(src, 1), destination=arr_pop,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=transform, dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear
        )
    arr_pop = np.nan_to_num(arr_pop, nan=0.0) / 250000.0

    np.save(os.path.join(WORKSPACE, "Layer_Height.npy"), arr_height)
    return arr_height, arr_sc, arr_vb, arr_ns, arr_sem, arr_road, arr_pop

def simulate_dynamics(arr_pop, arr_road, arr_sem, time_hour):
    gamma_pop = {
        SEM_COMMERCIAL: {4: 0.1, 8: 0.8, 18: 1.5},
        SEM_OFFICE: {4: 0.1, 8: 1.5, 18: 0.5},
        SEM_PUBLIC: {4: 0.1, 8: 1.2, 18: 0.8},
        SEM_RESIDENTIAL: {4: 1.2, 8: 0.6, 18: 0.9},
        SEM_OPEN: {4: 0.2, 8: 1.0, 18: 1.2}
    }
    eta_pop = {SEM_COMMERCIAL: 0.4, SEM_OFFICE: 0.1, SEM_PUBLIC: 0.2, SEM_RESIDENTIAL: 0.3, SEM_OPEN: 1.0}

    p_dyn = np.zeros_like(arr_pop)
    for sem_type in gamma_pop.keys():
        mask = (arr_sem == sem_type)
        if np.any(mask):
            p_dyn[mask] = arr_pop[mask] * gamma_pop[sem_type].get(time_hour, 1.0) * eta_pop[sem_type]
    p_dyn = gaussian_filter(p_dyn, sigma=15)

    attr_veh = {SEM_COMMERCIAL: 1.0, SEM_OFFICE: 1.2, SEM_PUBLIC: 0.8, SEM_RESIDENTIAL: 0.5, SEM_OPEN: 0.0}
    attr_map = np.zeros_like(arr_road)
    for sem_type, val in attr_veh.items():
        attr_map[arr_sem == sem_type] = val

    attr_map[arr_road > 0] = np.maximum(attr_map[arr_road > 0], 1.5)
    w_t = {4: 0.1, 8: 1.0, 18: 0.85}
    traffic_pot = gaussian_filter(attr_map, sigma=20) * w_t.get(time_hour, 1.0)

    r_veh = (traffic_pot + 0.2) * arr_road
    r_veh = gaussian_filter(r_veh, sigma=6.0)

    return p_dyn, r_veh

def generate_4d_tensor():
    print("========== 🚀 启动低密度区域 4D 风险张量融合 ==========")
    arr_height, arr_sc, arr_vb, arr_ns, arr_sem, arr_road, arr_pop = prepare_spatial_data()

    ALPHA_PED, ALPHA_VEH, ALPHA_PROP, ALPHA_NOISE = 0.4, 0.3, 0.2, 0.1
    C_MAX, M_U, G = 100.0, 3.0, 9.81
    R_D, RHO_A, S_HIT, BETA = 1.0, 1.225, 0.5, 34.0
    MU_BLD, SIGMA_BLD = 3.2264, 0.5818

    E_imp_list, prop_decay_list = np.zeros(NZ), np.zeros(NZ)
    for k in range(NZ):
        z_h = (k + 1) * CELL_SIZE
        term = (R_D * S_HIT * RHO_A) / M_U
        v_imp_sq = (2 * M_U * G) / (R_D * S_HIT * RHO_A) * (1.0 - math.exp(-z_h * term))
        E_imp_list[k] = 0.5 * M_U * v_imp_sq
        if z_h <= math.exp(MU_BLD):
            prop_decay_list[k] = 1.0
        else:
            prop_decay_list[k] = (1.0 / (z_h * SIGMA_BLD * math.sqrt(2 * math.pi))) * math.exp(
                -((math.log(z_h) - MU_BLD) ** 2) / (2 * SIGMA_BLD ** 2))
    prop_decay_list /= np.max(prop_decay_list)

    time_stamps = [("0400", 0, 4), ("0800", 1, 8), ("1800", 2, 18)]
    env_tensor_4d = np.zeros((3, NZ, NY, NX), dtype=np.float32)

    global_vb_max = np.percentile(arr_vb, 99.9) if arr_vb.max() > 0 else 1.0
    global_ns_max = np.percentile(arr_ns, 99.9) if arr_ns.max() > 0 else 1.0

    print("\n⏳ 正在执行时空张量切片压制...")
    for t_name, t_idx, t_hour in time_stamps:
        print(f"  -> 处理 {t_name} 时段...")
        p_dyn, r_veh = simulate_dynamics(arr_pop, arr_road, arr_sem, t_hour)

        pop_max_robust = np.percentile(p_dyn, 99.9) + 1e-6
        traf_max_robust = np.percentile(r_veh, 99.9) + 1e-6

        norm_pop = np.clip(p_dyn / pop_max_robust, 0, 1.0)
        norm_traf = np.clip(r_veh / traf_max_robust, 0, 1.0)
        norm_vb = np.clip(arr_vb / global_vb_max, 0, 1.0)
        norm_ns = np.clip(arr_ns / global_ns_max, 0, 1.0)

        # 🌟 100% 对齐原版代码的非线性逻辑
        if t_hour in [8, 18]:
            kappa_traf = 2.5
            norm_traf = norm_traf * np.exp(kappa_traf * norm_traf) / np.exp(kappa_traf)
            lambda_pop = 0.5
            norm_pop = np.power(norm_pop, 1.0 + lambda_pop)
        else:
            norm_traf = np.power(norm_traf, 1.8)
            norm_pop = np.power(norm_pop, 1.2)

        for k in range(NZ):
            z_h = (k + 1) * CELL_SIZE
            R_f_p = 1.0 / (1.0 + np.sqrt(
                BETA * np.power((BETA / max(E_imp_list[k], 0.001)), (1.0 / np.clip(arr_sc, 0.01, 1.0)))))

            cost_ped = norm_pop * R_f_p
            # 🌟 核心修复：引入您的直觉“车辆搭载率”与“拥堵排队密度” (用乘数 2.0 代替错误的 0.5 削弱)
            cost_veh = norm_traf * R_f_p * 2.0
            cost_prop = norm_vb * prop_decay_list[k]
            cost_noise = norm_ns * math.exp(-0.05 * z_h)

            air_risk = (ALPHA_PED * cost_ped + ALPHA_VEH * cost_veh + ALPHA_PROP * cost_prop + ALPHA_NOISE * cost_noise) * 60.0

            raw_mask = (arr_height >= z_h).astype(float)
            occupancy_ratio = gaussian_filter(raw_mask, sigma=0.8)
            env_tensor_4d[t_idx, k, :, :] = (1.0 - occupancy_ratio) * air_risk + occupancy_ratio * C_MAX

    out_path = os.path.join(WORKSPACE, "env_tensor_4D_Final.npy")
    np.save(out_path, env_tensor_4d)
    print(f"🎉 低密度张量重铸成功！底层数据逻辑已与高/中密度 100% 同步！")

if __name__ == "__main__":
    generate_4d_tensor()