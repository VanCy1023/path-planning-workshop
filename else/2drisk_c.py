import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

# 忽略潜在的空切片计算警告
warnings.filterwarnings('ignore')

# 确保读取和保存路径正确
SAVE_DIR = str(config.FIGURES_DIR / "A" / "c_ablation")
FACTOR = 10  # 2m分辨率 -> 20m分辨率 的降采样因子，使图像更平滑宏观
NX, NY = 1000, 1000


def render_ablation_heatmaps():
    print("========== 🚀 启动消融实验 2D 热力图独立渲染 (自适应定标版) ==========")

    # 对应前面步骤生成的三张张量文件
    files = {
        "Static": "tensor_c_static.npy",
        "Pop": "tensor_c_pop.npy",
        "Full": "tensor_c_full.npy"
    }

    map_data_cache = {}
    valid_risks_all = []

    # =========================================================
    # 第一阶段：全局扫描，提取真正的有效空气风险用于计算色带上限
    # =========================================================
    for key, filename in files.items():
        tensor_path = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(tensor_path):
            print(f"❌ 警告: 找不到文件 {filename}，请先运行张量生成脚本。")
            continue

        env_tensor = np.load(tensor_path)

        # 1. 剔除建筑：实体建筑的代价设为 100.0，用 90 作为截断阈值保留纯空气危险场
        air_tensor = np.where(env_tensor >= 90.0, np.nan, env_tensor)

        # 2. 沿 Z 轴自上而下投影，获取每个 (x,y) 柱体上的最大风险
        proj_2m = np.nanmax(air_tensor, axis=0)

        # 3. 降采样平滑处理 (2m -> 20m)
        reshaped = proj_2m.reshape(NY // FACTOR, FACTOR, NX // FACTOR, FACTOR)
        proj_20m = np.nanmean(reshaped, axis=(1, 3))

        # 填补纯建筑投影导致的虚空为 0.0 (底层深蓝)
        proj_20m = np.nan_to_num(proj_20m, nan=0.0)
        map_data_cache[key] = proj_20m

        # 收集有效风险点（去除底噪）用于后续分位数计算
        valid_pixels = proj_20m[proj_20m > 1.0]
        if len(valid_pixels) > 0:
            valid_risks_all.extend(valid_pixels)

    if not map_data_cache:
        print("❌ 未加载到任何有效数据，程序终止。")
        return

    # =========================================================
    # 第二阶段：计算自适应色带并统一定标
    # =========================================================
    # 🌟 核心：使用 95% 分位数作为统一色带上限。
    # 这能完美砍掉 Full 场景中极少数数值破百的交叉口异常值，防止画面被拉扯得“全蓝”或“死红”。
    display_vmax = np.percentile(valid_risks_all, 95)
    display_vmin = 0.0
    print(f"🌍 扫描完毕！锁定消融组统一直观色带: [0.00, {display_vmax:.2f}]")

    # =========================================================
    # 第三阶段：输出三张分开的、无标题的高清科研热力图
    # =========================================================
    for key, data in map_data_cache.items():
        fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')

        # 使用统一定标 (vmin, vmax) 绘图
        im = ax.imshow(data, cmap='jet', origin='lower', extent=[0, 2000, 0, 2000],
                       vmin=display_vmin, vmax=display_vmax, interpolation='nearest')

        # 坐标轴与网格设置
        ax.set_xlim(0, 2000)
        ax.set_ylim(0, 2000)
        ax.set_xlabel('X (m)', fontsize=18, fontweight='bold', labelpad=15)
        ax.set_ylabel('Y (m)', fontsize=18, fontweight='bold', labelpad=15)
        ax.tick_params(axis='both', which='major', labelsize=14)

        ax.xaxis.set_major_locator(ticker.MultipleLocator(500))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(500))
        ax.grid(which='major', color='black', linestyle='-', linewidth=0.6, alpha=0.3)

        # 添加颜色条 (Colorbar)
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=14)
        cbar.set_label('Discrete Air Block Risk', fontsize=16, fontweight='bold')

        # 🌟 满足要求：不设置 title，保存为独立文件
        save_path = os.path.join(SAVE_DIR, f"2D_Ablation_{key}.png")
        fig.savefig(save_path, dpi=400, bbox_inches='tight')
        plt.close(fig)
        print(f"🎉 已成功生成 2D 独立热力图: {save_path}")


if __name__ == "__main__":
    render_ablation_heatmaps()