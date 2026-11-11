import numpy as np
import os
import math
from scipy.ndimage import gaussian_filter

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

# ==========================================================
# 1. 基础环境与常量配置
# ==========================================================
WORKSPACE = str(config.TPR02)

CELL_SIZE = 2
NX, NY, NZ = 1000, 1000, 50

ALPHA_PED = 0.4
ALPHA_VEH = 0.3
ALPHA_PROP = 0.2
ALPHA_NOISE = 0.1
C_MAX = 100.0

M_U, G = 3.0, 9.81
R_D, RHO_A, S_HIT = 1.0, 1.225, 0.5
BETA = 34.0
MU_BLD, SIGMA_BLD = 3.2264, 0.5818

print("\n🚀 [Step 4] 启动 4D 风险张量融合 (引入不对称时空演化与社会动力学机制)...")

# ==========================================================
# 2. 加载静态层并提取全局动态极值
# ==========================================================
height_array = np.load(os.path.join(WORKSPACE, "Layer_Height.npy"))
sc_array = np.clip(np.load(os.path.join(WORKSPACE, "Layer_Shelter_Sc.npy")), 0.01, 1.0)
vb_array = np.load(os.path.join(WORKSPACE, "Layer_Property_Vb.npy"))
ns_array = np.load(os.path.join(WORKSPACE, "Layer_Noise_Ns.npy"))

time_stamps = [("0400", 0), ("0800", 1), ("1800", 2)]

global_pop_max, global_traf_max = 0.0, 0.0
for time_str, _ in time_stamps:
    p_arr = np.load(os.path.join(WORKSPACE, f"Layer_PopRisk_{time_str}.npy"))
    t_arr = np.load(os.path.join(WORKSPACE, f"Layer_TrafRisk_{time_str}.npy"))
    p_max_robust = np.percentile(p_arr, 99.9)
    t_max_robust = np.percentile(t_arr, 99.9)
    if p_max_robust > global_pop_max: global_pop_max = p_max_robust
    if t_max_robust > global_traf_max: global_traf_max = t_max_robust

global_vb_max = np.percentile(vb_array, 99.9) if vb_array.max() > 0 else 1.0
global_ns_max = np.percentile(ns_array, 99.9) if ns_array.max() > 0 else 1.0

# 预计算高度演变
E_imp_list = np.zeros(NZ)
prop_decay_list = np.zeros(NZ)
for k in range(NZ):
    z_h = (k + 1) * CELL_SIZE
    term = (R_D * S_HIT * RHO_A) / M_U
    v_imp_sq = (2 * M_U * G) / (R_D * S_HIT * RHO_A) * (1.0 - math.exp(-z_h * term))
    E_imp_list[k] = 0.5 * M_U * v_imp_sq
    if z_h <= math.exp(MU_BLD):
        prop_decay_list[k] = 1.0
    else:
        pdf = (1.0 / (z_h * SIGMA_BLD * math.sqrt(2 * math.pi))) * \
              math.exp(-((math.log(z_h) - MU_BLD) ** 2) / (2 * SIGMA_BLD ** 2))
        prop_decay_list[k] = pdf
prop_decay_list /= np.max(prop_decay_list)

# ==========================================================
# 3. 4D 张量融合 (应用不对称非线性算子)
# ==========================================================
env_tensor_4d = np.zeros((3, NZ, NY, NX), dtype=np.float32)

for time_str, t_idx in time_stamps:
    print(f"     ⏳ 正在处理 {time_str} 时段融合...")
    pop_2d = np.load(os.path.join(WORKSPACE, f"Layer_PopRisk_{time_str}.npy"))
    traf_2d = np.load(os.path.join(WORKSPACE, f"Layer_TrafRisk_{time_str}.npy"))

    norm_pop = np.clip(pop_2d / global_pop_max, 0, 1.0)
    norm_traf = np.clip(traf_2d / global_traf_max, 0, 1.0)

    # 🌟 核心理论创新：分时段不对称演化
    if time_str == "0800":
        # 早高峰：向心收敛与室内庇护
        # 交通：主干道局部尖锐拥堵，指数激增极大
        norm_traf = norm_traf * np.exp(3.5 * norm_traf) / np.exp(3.5)
        # 人口：超线性惩罚，压制本底，突显办公核心区孤岛尖峰
        norm_pop = np.power(norm_pop, 2.0)

    elif time_str == "1800":
        # 晚高峰：离心耗散与休闲暴露
        # 交通：路网大范围漫延饱和。先做空间扩散，再施加中等激增
        traf_diffused = gaussian_filter(norm_traf, sigma=1.5)
        norm_traf = traf_diffused * np.exp(2.0 * traf_diffused) / np.exp(2.0)
        # 人口：亚线性放大，模拟大面积的下班散步/就餐等泛在室外暴露
        norm_pop = np.clip(np.power(norm_pop, 0.6) * 1.5, 0, 1.0)

    else:  # 0400 凌晨
        # 极致平坦，强力抑制基底
        norm_traf = np.power(norm_traf, 2.5)
        norm_pop = np.power(norm_pop, 2.5)

    norm_vb = np.clip(vb_array / global_vb_max, 0, 1.0)
    norm_ns = np.clip(ns_array / global_ns_max, 0, 1.0)

    for k in range(NZ):
        z_h = (k + 1) * CELL_SIZE
        R_f_p = 1.0 / (1.0 + np.sqrt(BETA * np.power((BETA / max(E_imp_list[k], 0.001)), (1.0 / sc_array))))

        cost_ped = norm_pop * R_f_p
        cost_veh = norm_traf * R_f_p * 0.5
        cost_prop = norm_vb * prop_decay_list[k]
        cost_noise = norm_ns * math.exp(-0.05 * z_h)

        air_risk = (ALPHA_PED * cost_ped + ALPHA_VEH * cost_veh +
                    ALPHA_PROP * cost_prop + ALPHA_NOISE * cost_noise) * 60.0

        raw_mask = (height_array >= z_h).astype(float)
        occupancy_ratio = gaussian_filter(raw_mask, sigma=0.8)

        layer_cost = (1.0 - occupancy_ratio) * air_risk + occupancy_ratio * C_MAX
        env_tensor_4d[t_idx, k, :, :] = layer_cost

output_npy = os.path.join(WORKSPACE, "env_tensor_4D_Final.npy")
np.save(output_npy, env_tensor_4d)
print(f"\n🎉 完美融合！不对称时序特征（向心收敛 vs 离心泛在暴露）已注入！")