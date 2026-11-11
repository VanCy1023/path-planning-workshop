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

warnings.filterwarnings('ignore')

SAVE_DIR = str(config.FIGURES_DIR / "A" / "c_ablation")
FACTOR = 10  # 2m -> 20m 降维
NX, NY = 1000, 1000


def render_3d_ablation_heatmaps():
    print("========== 🚀 启动消融实验 3D 热力图独立渲染 ==========")

    files = {
        "Static": "tensor_c_static.npy",
        "Pop": "tensor_c_pop.npy",
        "Full": "tensor_c_full.npy"
    }

    map_data_cache = {}
    valid_risks = []

    for key, filename in files.items():
        tensor_path = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(tensor_path):
            print(f"❌ 找不到张量: {filename}")
            continue

        env_tensor = np.load(tensor_path)
        # 剔除建筑阻挡
        air_tensor = np.where(env_tensor >= 90.0, np.nan, env_tensor)
        proj_2m = np.nanmax(air_tensor, axis=0)

        reshaped = proj_2m.reshape(NY // FACTOR, FACTOR, NX // FACTOR, FACTOR)
        proj_20m = np.nanmean(reshaped, axis=(1, 3))
        proj_20m = np.nan_to_num(proj_20m, nan=0.0)

        map_data_cache[key] = proj_20m
        valid_risks.extend(proj_20m[proj_20m > 1.0])

    if not map_data_cache:
        return

    # 全局色带，95% 截断异常值，防止全红
    display_vmax = np.percentile(valid_risks, 95)
    display_vmin = 0.0

    x = np.linspace(0, 2000, NX // FACTOR)
    y = np.linspace(0, 2000, NY // FACTOR)
    X, Y = np.meshgrid(x, y)

    # 🌟 生成原生 3D 曲面图，完全无标题
    for key, data in map_data_cache.items():
        fig = plt.figure(figsize=(10, 8), facecolor='white')
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(X, Y, data, cmap='jet', vmin=display_vmin, vmax=display_vmax,
                               linewidth=0, antialiased=False, alpha=0.95)
        # 底部阴影
        ax.contourf(X, Y, data, zdir='z', offset=-5, cmap='jet',
                    vmin=display_vmin, vmax=display_vmax, alpha=0.5, levels=30)

        ax.set_zlim(-5, display_vmax * 1.2)
        ax.set_xlabel('X (m)', fontweight='bold', labelpad=10)
        ax.set_ylabel('Y (m)', fontweight='bold', labelpad=10)
        ax.set_zlabel('Risk Level', fontweight='bold', labelpad=10)
        ax.view_init(elev=35, azim=-55)

        # 保存图片，完全去标题
        save_path = os.path.join(SAVE_DIR, f"3D_Heatmap_{key}.png")
        fig.savefig(save_path, dpi=400, bbox_inches='tight')
        plt.close(fig)
        print(f"🎉 成功生成 3D 热力图: {save_path}")


if __name__ == "__main__":
    render_3d_ablation_heatmaps()