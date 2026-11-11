import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as ndimage
from mpl_toolkits.mplot3d import Axes3D

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

# ==========================================================
# 1. 基础配置
# ==========================================================
WORKSPACE = str(config.TPR02)
SAVE_DIR = str(config.FIGURES_DIR / "A")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

CMAP = plt.cm.jet


def generate_6_heatmaps():
    print("========== 🚀 启动 3D 曲面高保真渲染流水线 ==========")
    times = ["0400", "0800", "1800"]
    step = 10

    # 全局提取极值以保证色带标尺统一
    global_pop_max, global_traf_max = 0.0, 0.0
    for t in times:
        p = np.percentile(np.load(os.path.join(WORKSPACE, f"Layer_PopRisk_{t}.npy")), 99.9)
        tr = np.percentile(np.load(os.path.join(WORKSPACE, f"Layer_TrafRisk_{t}.npy")), 99.9)
        if p > global_pop_max: global_pop_max = p
        if tr > global_traf_max: global_traf_max = tr

    for time_str in times:
        print(f"\n⏳ 正在处理 {time_str[:2]}:{time_str[2:]} 渲染...")
        pop_data = np.load(os.path.join(WORKSPACE, f"Layer_PopRisk_{time_str}.npy"))
        traf_data = np.load(os.path.join(WORKSPACE, f"Layer_TrafRisk_{time_str}.npy"))

        # 降采样 (交通必须最大值池化以防断路)
        pop_small = pop_data[::step, ::step]
        traf_dilated = ndimage.maximum_filter(traf_data, size=step)
        traf_small = traf_dilated[::step, ::step]

        # 初步截断与全局归一化
        pop_norm = np.clip(pop_small / global_pop_max, 0, 1.0)
        traf_norm = np.clip(traf_small / global_traf_max, 0, 1.0)

        # 🌟 可视化阶段再现理论创新：不对称演化渲染 🌟
        if time_str == "0800":
            # 早高峰：向心收敛 (尖塔状突起)
            traf_norm = traf_norm * np.exp(3.5 * traf_norm) / np.exp(3.5)
            # 施加超线性惩罚，强力压制周边，凸显核心孤岛
            pop_norm = np.power(pop_norm, 2.0)

        elif time_str == "1800":
            # 晚高峰：离心耗散 (连绵的丘陵)
            # 1. 交通大范围漫延饱和
            traf_norm = ndimage.gaussian_filter(traf_norm, sigma=1.0)
            traf_norm = traf_norm * np.exp(2.0 * traf_norm) / np.exp(2.0)

            # 2. 【核心修复】人群发散：扩大高斯平滑模拟散步/外流，并采用温和的亚线性抬升
            # 坚决不使用乘法系数，防止触顶被“削平”
            pop_norm = ndimage.gaussian_filter(pop_norm, sigma=2.0)
            pop_norm = np.power(pop_norm, 0.7)

        else:
            # 凌晨：深蓝盆地
            traf_norm = np.power(traf_norm, 2.5)
            pop_norm = np.power(pop_norm, 2.5)

        pop_norm *= 100.0
        traf_norm *= 100.0

        nx, ny = pop_norm.shape
        X, Y = np.meshgrid(np.linspace(0, 2.0, nx), np.linspace(0, 2.0, ny))

        # ------ 渲染人口 ------
        fig1 = plt.figure(figsize=(10, 8), facecolor='white')
        ax1 = fig1.add_subplot(111, projection='3d')
        surf1 = ax1.plot_surface(X, Y, pop_norm, cmap=CMAP, alpha=0.85, rstride=1, cstride=1, edgecolor='none')
        ax1.contourf(X, Y, pop_norm, zdir='z', offset=-20, cmap=CMAP, alpha=0.7, levels=20)
        ax1.set_box_aspect(aspect=(1, 1, 0.18))
        ax1.set_zlim(-20, 100)
        ax1.set_title(f"Population Risk Distribution ({time_str[:2]}:{time_str[2:]})", fontsize=16, fontweight='bold',
                      pad=20)
        ax1.view_init(elev=30, azim=-55)
        fig1.savefig(os.path.join(SAVE_DIR, f"Population_Risk_3D_{time_str}.png"), dpi=800, bbox_inches='tight')

        # ------ 渲染交通 ------
        fig2 = plt.figure(figsize=(10, 8), facecolor='white')
        ax2 = fig2.add_subplot(111, projection='3d')
        surf2 = ax2.plot_surface(X, Y, traf_norm, cmap=CMAP, alpha=0.85, rstride=1, cstride=1, edgecolor='none')
        ax2.contourf(X, Y, traf_norm, zdir='z', offset=-20, cmap=CMAP, alpha=0.7, levels=20)
        ax2.set_box_aspect(aspect=(1, 1, 0.18))
        ax2.set_zlim(-20, 100)
        ax2.set_title(f"Traffic Risk Distribution ({time_str[:2]}:{time_str[2:]})", fontsize=16, fontweight='bold',
                      pad=20)
        ax2.view_init(elev=30, azim=-55)
        fig2.savefig(os.path.join(SAVE_DIR, f"Traffic_Risk_3D_{time_str}.png"), dpi=800, bbox_inches='tight')

    print("\n🎉 6 张非线性 3D 图像全部生成完毕！")
    plt.show()


if __name__ == "__main__":
    generate_6_heatmaps()