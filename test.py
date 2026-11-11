import numpy as np
import time
import matplotlib.pyplot as plt
from algorithms import PathPlanners


def run_mini_test():
    print(">>> 正在生成微型测试环境 (100x100x30) ...")
    # 1. 构造一个微型风险张量
    grid = np.zeros((100, 100, 30))

    # 放置一面巨大的高风险墙，挡在起点和终点中间
    grid[45:55, 20:80, :] = 50.0

    # 在墙中间开一个小洞，设定为中等风险 (15.0)
    # (贪婪的 Cost-A* 会为了缩短直线距离从这里抄近路)
    grid[45:55, 45:55, :] = 15.0

    # 墙外两端 (Y<20 或 Y>80) 是绝对安全的 0 风险，但需要绕很远的路
    # (保守的 Dijkstra 宁可绕远路也会走这边)

    start = (10, 50, 15)
    goal = (90, 50, 15)

    print(">>> 初始化规划器...")
    planner = PathPlanners(grid, grid_res=2.0)

    print(">>> [1] 运行 Dijkstra (绝对保守，宁可绕远路也要 0 风险)...")
    path_d, t_d, n_d = planner.dijkstra(start, goal)
    print(f"    耗时: {t_d:.3f}s, 节点数: {n_d}, 长度: {len(path_d)}")

    print(">>> [2] 运行 Cost-A* (极度贪婪 W=5.0，为了近路敢穿中等风险区)...")
    path_c, t_c, n_c = planner.cost_astar(start, goal)
    print(f"    耗时: {t_c:.3f}s, 节点数: {n_c}, 长度: {len(path_c)}")

    # --- 绘图 ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=50, azim=-60)

    # 仅画出有风险的区域，降低密度以便观察
    x, y, z = np.where(grid == 50.0)
    ax.scatter(x[::10], y[::10], z[::10], c='r', alpha=0.1, s=5, label='High Risk Wall')

    x2, y2, z2 = np.where(grid == 15.0)
    ax.scatter(x2[::2], y2[::2], z2[::2], c='orange', alpha=0.2, s=5, label='Medium Risk Hole')

    if path_d:
        pts = np.array(path_d)
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], 'k-', linewidth=4, label='Dijkstra (Safe Detour)')
    if path_c:
        pts = np.array(path_c)
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], 'orange', linewidth=3, label='Cost-A* (Direct Shortcut)')

    ax.scatter(*start, c='lime', marker='^', s=150, zorder=10)
    ax.scatter(*goal, c='gold', marker='*', s=150, zorder=10)

    ax.set_title("Mini Test: Dijkstra vs Cost-A* (Trajectory Separation)")
    ax.legend()

    plt.savefig("Mini_Test_Separation.png", dpi=200)
    print(">>> 🎉 图像已保存为 Mini_Test_Separation.png (请检查两根线是否彻底分开了！)")

   # 强制弹出图片窗口
    plt.show()

if __name__ == "__main__":
    run_mini_test()