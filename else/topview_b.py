import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.ticker as ticker
import warnings

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

# 忽略全 NaN 切片计算时的系统警告
warnings.filterwarnings('ignore')

WORKSPACES = {
    "Low": str(config.TPR02),
    "Medium": str(config.TPR03),
    "High": str(config.TPR04)
}
SAVE_DIR = str(config.FIGURES_DIR / "A")
os.makedirs(SAVE_DIR, exist_ok=True)

NX, NY = 1000, 1000
FACTOR = 10  # 2m -> 20m 降维因子


def render_maps():
    print("========== 🚀 启动 18:00 硬核像素级渲染 ==========")
    map_data_cache = {}
    global_vmax = 0.0
    global_vmin = 100.0

    for density_name, ws_path in WORKSPACES.items():
        tensor_path = os.path.join(ws_path, "env_tensor_4D_Final.npy")
        if not os.path.exists(tensor_path):
            print(f"  ❌ 找不到张量，跳过: {tensor_path}")
            continue

        # 1. 提取 18:00 时段
        env_tensor = np.load(tensor_path)[2]

        # 2. 【核心修复】将建筑物及边缘高光彻底设为 NaN (虚空)
        # 空气风险极少超过 38，将所有 >= 38 的建筑边缘污染全部剔除
        air_tensor = np.where(env_tensor >= 38.0, np.nan, env_tensor)

        # 3. 沿 Z 轴投影，获取纯空气柱最大风险 (如果整根柱子都是建筑，则依然是 NaN)
        proj_2m = np.nanmax(air_tensor, axis=0)

        # 4. 【神级降维】使用 nanmean 聚合到 20m
        # 只计算纯空气的平均风险，马路高值绝不被稀释，建筑残影绝不扩张！
        reshaped = proj_2m.reshape(NY // FACTOR, FACTOR, NX // FACTOR, FACTOR)
        proj_20m = np.nanmean(reshaped, axis=(1, 3))

        # 5. 填平虚空：将纯建筑物的方块(NaN)填充为底层底噪(例如4.0，在Jet中呈现深蓝深渊)
        proj_20m = np.nan_to_num(proj_20m, nan=4.0)

        # 🌟 核心调色逻辑：只提取真正的空气部分来计算分位数
        valid_air = proj_20m[proj_20m > 4.5]
        if len(valid_air) > 0:
            # 放弃 99.9%，改用 92% 分位数！这会砍掉极少数的“变态高分”孤岛
            # 让 15~20 分的主干道也能顶到色带的红黄色域，整体画面瞬间升温！
            vmax_val = np.percentile(valid_air, 92)
        else:
            vmax_val = 15.0

        vmin_val = np.min(proj_20m)
        if vmax_val > global_vmax: global_vmax = vmax_val
        if vmin_val < global_vmin: global_vmin = vmin_val

        map_data_cache[density_name] = proj_20m
        print(f"  ✅ {density_name} 清洗降维完毕。当前稳健 Vmax: {vmax_val:.2f}")

    if not map_data_cache:
        return

    # 进一步强制压低全局上限，把上限从之前的 36 压低到 22 左右
    display_vmax = min(global_vmax, 22.0)
    display_vmin = max(global_vmin, 2.0)
    print(f"\n🌍 锁定全局色带: [{display_vmin:.2f}, {display_vmax:.2f}] (画面已升温!)")

    x_20m = np.linspace(0, 2000, 100)
    y_20m = np.linspace(0, 2000, 100)
    X, Y = np.meshgrid(x_20m, y_20m)

    for density, data_20m in map_data_cache.items():
        print(f"⏳ 正在生成 {density} 地图...")

        # ========== 1. 3D 曲面图 (像素风) ==========
        fig_3d = plt.figure(figsize=(10, 8), facecolor='white')
        ax_3d = fig_3d.add_subplot(111, projection='3d')

        surf = ax_3d.plot_surface(X, Y, data_20m, cmap='jet', vmin=display_vmin, vmax=display_vmax,
                                  linewidth=0, antialiased=False, alpha=0.95)
        ax_3d.contourf(X, Y, data_20m, zdir='z', offset=0, cmap='jet',
                       vmin=display_vmin, vmax=display_vmax, alpha=0.5, levels=30)

        ax_3d.set_zlim(0, 40)
        ax_3d.set_xlabel('X (m)', fontweight='bold', labelpad=10)
        ax_3d.set_ylabel('Y (m)', fontweight='bold', labelpad=10)
        ax_3d.view_init(elev=35, azim=-55)

        fig_3d.savefig(os.path.join(SAVE_DIR, f"3D_Risk_{density}.png"), dpi=400, bbox_inches='tight')
        plt.close(fig_3d)

        # ========== 2. 2D 俯视图 (带辅助网格) ==========
        fig_2d, ax_2d = plt.subplots(figsize=(10, 10), facecolor='white')

        im = ax_2d.imshow(data_20m, cmap='jet', origin='lower', extent=[0, 2000, 0, 2000],
                          vmin=display_vmin, vmax=display_vmax, interpolation='nearest')

        ax_2d.set_xlim(0, 2000)
        ax_2d.set_ylim(0, 2000)
        ax_2d.set_xlabel('X (m)', fontsize=16, fontweight='bold', labelpad=15)
        ax_2d.set_ylabel('Y (m)', fontsize=16, fontweight='bold', labelpad=15)
        ax_2d.tick_params(axis='both', which='major', labelsize=12)

        ax_2d.xaxis.set_major_locator(ticker.MultipleLocator(200))
        ax_2d.yaxis.set_major_locator(ticker.MultipleLocator(200))
        ax_2d.xaxis.set_minor_locator(ticker.MultipleLocator(20))
        ax_2d.yaxis.set_minor_locator(ticker.MultipleLocator(20))
        ax_2d.grid(which='major', color='black', linestyle='-', linewidth=0.6, alpha=0.5)

        cbar = fig_2d.colorbar(im, ax=ax_2d, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label('Discrete Air Block Risk (Smoothed 20m x 20m)', fontsize=14, fontweight='bold')

        fig_2d.savefig(os.path.join(SAVE_DIR, f"2D_Risk_{density}.png"), dpi=400, bbox_inches='tight')
        plt.close(fig_2d)

    print("🎉 所有硬核科学图表渲染完毕！噩梦结束，快去查看图库！")


if __name__ == "__main__":
    render_maps()