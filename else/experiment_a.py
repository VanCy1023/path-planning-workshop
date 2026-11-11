import numpy as np
import os
import time
import matplotlib.pyplot as plt

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402
from algorithms import PathPlanners

# 请确保此处与您生成张量的工作空间路径一致
WORKSPACE = str(config.TPR02)


def plot_individual_paths(all_paths, start_phys, goal_phys, scaled_res=10.0):
    """
    分别为每个时段绘制纯 3D 航迹图并单独保存
    """
    print("\n>>> 正在渲染独立航迹对比图...")

    # 论文算法标准配色
    colors = {
        'Dijkstra': 'black',
        'Risk-A*': 'purple',
        'Cost-A*': 'orange',
        'EDA-CostA*': 'red',
        'RRT*': 'blue'  # 已修正为纯蓝色
    }

    for t_name, paths in all_paths.items():
        fig = plt.figure(figsize=(8, 6))  # 单独一张图的尺寸
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=35, azim=-55)

        # 绘制该时段下各算法的航迹
        for algo_name, path in paths.items():
            if path:
                # 将降采样网格坐标还原为物理坐标 (m)
                pts = np.array(path) * scaled_res
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], label=algo_name,
                        color=colors.get(algo_name, 'b'), linewidth=2.5)

        # 绘制起终点
        ax.scatter(start_phys[0], start_phys[1], start_phys[2], c='lime', marker='^', s=150, zorder=5)
        ax.scatter(goal_phys[0], goal_phys[1], goal_phys[2], c='gold', marker='*', s=200, zorder=5)

        ax.set_zlim(0, 150)  # 限制高度

        # 移除大标题小标题，保留坐标轴说明
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")

        # 缩小图例尺寸
        ax.legend(loc='upper left', fontsize=10)

        # 保存为独立图片，替换掉文件名中的特殊字符如冒号
        safe_t_name = t_name.replace(':', '')
        save_path = os.path.join(WORKSPACE, f"Experiment_4_Trajectory_{safe_t_name}.png")
        plt.savefig(save_path, dpi=400, bbox_inches='tight')
        print(f"🎉 航迹图已单独保存至: {save_path}")

        # 释放内存
        plt.close(fig)


def main():
    print("========== 🚀 城市低空多时序航迹规划对比实验 (极速降维版) ==========")
    tensor_path = os.path.join(WORKSPACE, "env_tensor_4D_Final.npy")

    if not os.path.exists(tensor_path):
        print(f"❌ 找不到风险张量文件: {tensor_path}")
        return

    print(">>> 正在加载 4D 城市风险底座...")
    env_tensor_4d = np.load(tensor_path)

    time_stamps = [("04:00", 0), ("08:00", 1), ("18:00", 2)]

    # 🌟 核心防卡死参数：空间降维倍数 (将 2m 精度抽稀为 10m 精度用于路径搜索)
    SPACE_STEP = 5
    ORIGINAL_RES = 2.0
    SCALED_RES = ORIGINAL_RES * SPACE_STEP

    # 原始网格起终点 (x, y, z)
    start_orig = (100, 100, 5)
    goal_orig = (900, 850, 60)

    # 映射至降维后的规划网格中
    start_scaled = (start_orig[0] // SPACE_STEP, start_orig[1] // SPACE_STEP, start_orig[2] // SPACE_STEP)
    goal_scaled = (goal_orig[0] // SPACE_STEP, goal_orig[1] // SPACE_STEP, goal_orig[2] // SPACE_STEP)

    # 真实的物理坐标 (米) 用于最后画图
    start_phys = (start_orig[0] * ORIGINAL_RES, start_orig[1] * ORIGINAL_RES, start_orig[2] * ORIGINAL_RES)
    goal_phys = (goal_orig[0] * ORIGINAL_RES, goal_orig[1] * ORIGINAL_RES, goal_orig[2] * ORIGINAL_RES)

    print(f"\n📍 真实物理起终点: Start {start_phys}m -> Goal {goal_phys}m")
    print(f"⚡ 启动降维引擎 (分辨率 {SCALED_RES}m), 搜索空间缩小 {SPACE_STEP ** 3} 倍！")

    all_paths = {t_name: {} for t_name, _ in time_stamps}

    for time_name, t_idx in time_stamps:
        print(f"\n" + "=" * 85)
        print(f" ⏳ 当前测试时段: {time_name}")
        print("=" * 85)

        # 1. 提取当前时间切片，转置为 (X, Y, Z)
        current_risk_tensor = np.transpose(env_tensor_4d[t_idx], (2, 1, 0))
        # 2. 空间矩阵降采样切片
        reduced_tensor = current_risk_tensor[::SPACE_STEP, ::SPACE_STEP, ::SPACE_STEP]

        # 传入放大后的分辨率进行评估计算
        planner = PathPlanners(reduced_tensor, grid_res=SCALED_RES)

        algorithms = {
            "Dijkstra": planner.dijkstra,
            "Risk-A*": planner.risk_astar,
            "Cost-A*": planner.cost_astar,
            "EDA-CostA*": planner.eda_cost_astar,
            "RRT*": planner.rrt_star
        }

        print(
            f"{'算法名称':<15} | {'路径长度(m)':<12} | {'风险代价(RC)':<12} | {'平滑度(SM)':<10} | {'实际耗时(s)':<10} | {'扩展节点数'}")
        print("-" * 90)

        for algo_name, search_func in algorithms.items():
            print(f"⚙️ 正在计算 {algo_name:<13} ... ", end="", flush=True)

            t0 = time.time()
            try:
                # 必须传入降维后的起终点
                path, _, nodes = search_func(start_scaled, goal_scaled)
                t1 = time.time()

                if path:
                    all_paths[time_name][algo_name] = path
                    pl, rc, sm = planner.calc_metrics(path)
                    time_cost = t1 - t0
                    print(f"\r{algo_name:<15} | {pl:<12.2f} | {rc:<12.2f} | {sm:<10.2f} | {time_cost:<10.2f} | {nodes}")
                else:
                    print(f"\r{algo_name:<15} | 规划失败 (未找到可行解)")

            except Exception as e:
                print(f"\r{algo_name:<15} | 运行出错: {str(e)}")

    # 独立渲染并保存三个时间段的航迹图
    plot_individual_paths(all_paths, start_phys, goal_phys, scaled_res=SCALED_RES)


if __name__ == "__main__":
    main()