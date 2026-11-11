import os
import numpy as np

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

# ==========================================================
# 1. 基础配置
# ==========================================================
WORKSPACE = str(config.TPR02)
# 定义什么是“高风险” (例如：全局风险数据的 90% 分位以上)
THRESHOLD_PERCENTILE = 90


def calculate_metrics():
    times = ["0400", "0800", "1800"]
    stats = {}

    for t in times:
        # 实时读取并相加获取总风险
        pop_data = np.load(os.path.join(WORKSPACE, f"Layer_PopRisk_{t}.npy"))
        traf_data = np.load(os.path.join(WORKSPACE, f"Layer_TrafRisk_{t}.npy"))
        total_data = pop_data + traf_data

        # 计算高风险阈值 (基于 0400 时刻的基准阈值，或者每个时刻独立计算)
        # 如果你想体现风险变化，建议使用 0400 的阈值作为固定基准
        if t == "0400":
            global_threshold = np.percentile(total_data, THRESHOLD_PERCENTILE)

        # 统计超过阈值的栅格数量
        high_risk_count = np.sum(total_data > global_threshold)
        stats[t] = high_risk_count
        print(f"[{t}] 高风险栅格数量: {high_risk_count}")

    # 计算 08:00 相对于 04:00 的增长率 (XX%)
    growth_rate_08 = ((stats["0800"] - stats["0400"]) / stats["0400"]) * 100

    # 计算 18:00 相比 04:00 的增加量 (XX)
    increase_18 = stats["1800"] - stats["0400"]

    print("-" * 30)
    print(f"✅ 论文填空数据:")
    print(f"08:00 高风险栅格数量增加: {growth_rate_08:.2f}%")
    print(f"18:00 高风险区域栅格增加: {increase_18} 个")


if __name__ == "__main__":
    calculate_metrics()