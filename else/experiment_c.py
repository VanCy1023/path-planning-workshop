import numpy as np
import os
import time
import matplotlib.pyplot as plt

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402
from algorithms import PathPlanners  # 请确保 algorithms.py 位于同级目录

SAVE_DIR = str(config.FIGURES_DIR / "A" / "c_ablation")
os.makedirs(SAVE_DIR, exist_ok=True)

COLORS = {
    'Dijkstra': 'black',
    'Risk-A*': 'purple',
    'Cost-A*': 'orange',
    'EDA-CostA*': 'red',
    'RRT*': 'blue'
}


def plot_3d_ablation_trajectory(paths_dict, start_phys, goal_phys, scaled_res, key_name):
    """渲染单一地图的三维纯净航迹图，不带标题，无建筑"""
    fig = plt.figure(figsize=(9, 7), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=35, azim=-55)

    for algo_name, path in paths_dict.items():
        if not path: continue
        pts = np.array(path) * scaled_res

        # 视觉样式100%匹配上组实验
        if algo_name == 'Dijkstra':
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                    color=COLORS[algo_name], linewidth=2.5, alpha=1.0, zorder=2)
        elif algo_name == 'Cost-A*':
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                    color=COLORS[algo_name], linewidth=2.5, zorder=4)
        elif algo_name == 'EDA-CostA*':
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                    color=COLORS[algo_name], linewidth=2.5, zorder=5)
        else:
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                    color=COLORS.get(algo_name, 'b'), linewidth=2.0, zorder=3)

    ax.scatter(start_phys[0], start_phys[1], start_phys[2], c='lime', marker='^', s=150, zorder=6)
    ax.scatter(goal_phys[0], goal_phys[1], goal_phys[2], c='gold', marker='*', s=200, zorder=6)

    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 2000)
    ax.set_zlim(0, 150)

    ax.set_xlabel("X (m)", labelpad=10)
    ax.set_ylabel("Y (m)", labelpad=10)
    ax.set_zlabel("Z (m)", labelpad=6, verticalalignment='bottom')
    ax.tick_params(axis='z', pad=4)

    # 无标题，图例放置左上角
    ax.legend(loc='upper left', bbox_to_anchor=(-0.15, 0.95), fontsize=11)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, f"3D_Trajectory_{key_name}.png")
    plt.savefig(save_path, dpi=400, bbox_inches='tight')
    plt.close(fig)
    print(f"🎉 独立 3D 航迹图保存成功: {save_path}")


def main():
    print("========== 🚀 动态风险底图消融对比实验 (控制变量) ==========")
    SPACE_STEP = 5
    ORIGINAL_RES = 2.0
    SCALED_RES = ORIGINAL_RES * SPACE_STEP

    start_orig = (100, 100, 5)
    goal_orig = (900, 850, 60)

    start_scaled = (start_orig[0] // SPACE_STEP, start_orig[1] // SPACE_STEP, start_orig[2] // SPACE_STEP)
    goal_scaled = (goal_orig[0] // SPACE_STEP, goal_orig[1] // SPACE_STEP, goal_orig[2] // SPACE_STEP)

    start_phys = (start_orig[0] * ORIGINAL_RES, start_orig[1] * ORIGINAL_RES, start_orig[2] * ORIGINAL_RES)
    goal_phys = (goal_orig[0] * ORIGINAL_RES, goal_orig[1] * ORIGINAL_RES, goal_orig[2] * ORIGINAL_RES)

    tensors_to_test = [
        ("Static", "tensor_c_static.npy"),
        ("Pop", "tensor_c_pop.npy"),
        ("Full", "tensor_c_full.npy")
    ]

    for key_name, filename in tensors_to_test:
        print(f"\n" + "=" * 90)
        print(f" ⏳ 正在进行实验组: {key_name}")
        print("=" * 90)

        tensor_path = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(tensor_path):
            print(f"❌ 找不到张量 {filename}，跳过！")
            continue

        env_tensor_4d = np.load(tensor_path)
        # 如果保存的是 3D 张量 (NZ, NY, NX)
        if len(env_tensor_4d.shape) == 3:
            current_risk_tensor = np.transpose(env_tensor_4d, (2, 1, 0))
        # 兼容之前 4D 的格式
        elif len(env_tensor_4d.shape) == 4:
            current_risk_tensor = np.transpose(env_tensor_4d[2], (2, 1, 0))

        reduced_tensor = current_risk_tensor[::SPACE_STEP, ::SPACE_STEP, ::SPACE_STEP]

        planner = PathPlanners(reduced_tensor, grid_res=SCALED_RES)
        algorithms = {
            "Dijkstra": planner.dijkstra,
            "Risk-A*": planner.risk_astar,
            "Cost-A*": planner.cost_astar,
            "EDA-CostA*": planner.eda_cost_astar,
            "RRT*": planner.rrt_star
        }

        print(
            f"{'算法名称':<15} | {'路径长度(m)':<12} | {'风险代价(RC)':<12} | {'平滑度(SM)':<10} | {'耗时(s)':<10} | {'扩展节点数'}")
        print("-" * 95)

        paths_dict = {}
        for algo_name, search_func in algorithms.items():
            t0 = time.time()
            try:
                path, _, nodes = search_func(start_scaled, goal_scaled)
                t1 = time.time()
                if path:
                    paths_dict[algo_name] = path
                    pl, rc, sm = planner.calc_metrics(path)
                    print(f"{algo_name:<15} | {pl:<12.2f} | {rc:<12.2f} | {sm:<10.2f} | {t1 - t0:<10.2f} | {nodes}")
                else:
                    print(f"{algo_name:<15} | 规划失败 (未找到可行解)")
            except Exception as e:
                print(f"{algo_name:<15} | 运行出错: {str(e)}")

        plot_3d_ablation_trajectory(paths_dict, start_phys, goal_phys, SCALED_RES, key_name)


if __name__ == "__main__":
    main()