import numpy as np
import os
import time
import matplotlib.pyplot as plt

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402
from algorithms import PathPlanners

# ==========================================
# 1. 实验环境与路径配置
# ==========================================
WORKSPACES = {
    "Low": str(config.TPR02),  # 高新园区 (低密度)
    "Medium": str(config.TPR03),  # 和平广场 (中密度)
    "High": str(config.TPR04)  # 中山广场 (高密度)
}

SAVE_DIR = str(config.FIGURES_DIR / "A")
os.makedirs(SAVE_DIR, exist_ok=True)

COLORS = {
    'Dijkstra': 'black',
    'Risk-A*': 'purple',
    'Cost-A*': 'orange',
    'EDA-CostA*': 'red',
    'RRT*': 'blue'  # 已修正为纯蓝色
}


def plot_pure_trajectory(paths, start_phys, goal_phys, scaled_res, density_name):
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=35, azim=-55)

    for algo_name, path in paths.items():
        if path:
            pts = np.array(path) * scaled_res

            # 视觉分离处理：处理 Dijkstra 和 Cost-A* 完全重合的问题
            if algo_name == 'Dijkstra':
                # 加粗纯黑色底带 (透明度为0即 alpha=1.0)
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                        color=COLORS[algo_name], linewidth=2.5




                        , alpha=1.0, zorder=2)
            elif algo_name == 'Cost-A*':
                # 正常线宽，嵌在纯黑底带中
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                        color=COLORS[algo_name], linewidth=2.5, zorder=4)
            elif algo_name == 'EDA-CostA*':
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                        color=COLORS[algo_name], linewidth=2.5, zorder=5)
            else:
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                        color=COLORS.get(algo_name, 'b'), linewidth=2.0, zorder=3)

    # 绘制起终点
    ax.scatter(start_phys[0], start_phys[1], start_phys[2], c='lime', marker='^', s=150, zorder=6)
    ax.scatter(goal_phys[0], goal_phys[1], goal_phys[2], c='gold', marker='*', s=200, zorder=6)

    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 2000)
    ax.set_zlim(0, 150)

    # 解决 Z 轴数字被遮挡的问题：增加 labelpad 和 tick padding
    ax.set_xlabel("X (m)", labelpad=10)
    ax.set_ylabel("Y (m)", labelpad=10)
    ax.set_zlabel("Z (m)", labelpad=6, verticalalignment='bottom')
    ax.tick_params(axis='z', pad=4)

    # 🌟 重点优化：将图例整体上移，放置在左上角的安全空白区，彻底防止遮挡航迹
    ax.legend(loc='upper left', bbox_to_anchor=(-0.15, 0.95), fontsize=11)

    save_path = os.path.join(SAVE_DIR, f"Experiment2_Trajectory_{density_name}.png")
    plt.savefig(save_path, dpi=400, bbox_inches='tight')
    plt.close(fig)
    print(f"🎉 纯净版3D航迹图已保存: {save_path}")


def main():
    print("========== 🚀 跨密度城市环境多算法航迹对比实验 ==========")

    SPACE_STEP = 5
    ORIGINAL_RES = 2.0
    SCALED_RES = ORIGINAL_RES * SPACE_STEP

    start_orig = (100, 100, 5)
    goal_orig = (900, 850, 60)

    start_scaled = (start_orig[0] // SPACE_STEP, start_orig[1] // SPACE_STEP, start_orig[2] // SPACE_STEP)
    goal_scaled = (goal_orig[0] // SPACE_STEP, goal_orig[1] // SPACE_STEP, goal_orig[2] // SPACE_STEP)

    start_phys = (start_orig[0] * ORIGINAL_RES, start_orig[1] * ORIGINAL_RES, start_orig[2] * ORIGINAL_RES)
    goal_phys = (goal_orig[0] * ORIGINAL_RES, goal_orig[1] * ORIGINAL_RES, goal_orig[2] * ORIGINAL_RES)

    # 仅测试 18:00 (晚高峰) 时段，索引为 2
    T_IDX = 2

    for density_name, ws_path in WORKSPACES.items():
        print(f"\n" + "=" * 80)
        print(f" ⏳ 正在测试地图密度: {density_name} (路径: {ws_path})")
        print("=" * 80)

        tensor_path = os.path.join(ws_path, "env_tensor_4D_Final.npy")
        if not os.path.exists(tensor_path):
            print(f"❌ 警告: 找不到环境张量文件 {tensor_path}，跳过此密度地图。")
            continue

        env_tensor_4d = np.load(tensor_path)

        current_risk_tensor = np.transpose(env_tensor_4d[T_IDX], (2, 1, 0))
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
        print("-" * 90)

        paths_dict = {}

        for algo_name, search_func in algorithms.items():
            print(f"⚙️ 正在计算 {algo_name:<13} ... ", end="", flush=True)
            t0 = time.time()
            try:
                path, _, nodes = search_func(start_scaled, goal_scaled)
                t1 = time.time()

                if path:
                    paths_dict[algo_name] = path
                    pl, rc, sm = planner.calc_metrics(path)
                    print(f"\r{algo_name:<15} | {pl:<12.2f} | {rc:<12.2f} | {sm:<10.2f} | {t1 - t0:<10.2f} | {nodes}")
                else:
                    print(f"\r{algo_name:<15} | 规划失败 (未找到可行解)")
            except Exception as e:
                print(f"\r{algo_name:<15} | 运行出错: {str(e)}")

        plot_pure_trajectory(paths_dict, start_phys, goal_phys, SCALED_RES, density_name)


if __name__ == "__main__":
    main()