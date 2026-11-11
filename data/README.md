# 输入数据说明

本目录**不包含**任何数据文件，`.gitignore` 已将其全部排除。原因有两点：

1. 体积：一个 `env_tensor_4D_v2.npy` 就是 `3 × 75 × 1000 × 1000 float32`，
   约 **858 MB**，远超 GitHub 单文件 100 MB 的限制；
2. 来源：建筑轮廓、路网、人口栅格等派生自第三方数据产品，不便直接再分发。

## 期望的目录结构

把数据放到 `PPW_DATA_DIR` 指向的目录（默认就是本目录 `data/`）：

```
data/
├── TPR02/                      # 低密度区（高新园区）
│   ├── Layer_PopRisk_{0400,0800,1800}.npy
│   ├── Layer_TrafRisk_{0400,0800,1800}.npy
│   ├── Layer_Shelter_Sc.npy
│   ├── Layer_Property_Vb.npy
│   ├── Layer_Noise_Ns.npy
│   ├── Layer_Height.npy
│   ├── env_tensor_4D_Final.npy   # risk_tensor_tpr2.py 的产物
│   └── env_tensor_4D_v2.npy      # rebuild_risk_model.py 的产物（论文所用）
├── TPR03/                      # 中密度区（和平广场）
│   └── …同上
├── TPR04/                      # 高密度区（中山广场）
│   └── …同上
├── ablation/
│   ├── env_tensor_abl_static.npy
│   ├── env_tensor_abl_pop.npy
│   └── env_tensor_abl_full.npy
└── vectors/                    # 原始矢量/栅格，仅重建张量时需要
    ├── TPR02/
    │   ├── osm/2/buildings_recovered_v2_proj_ready.shp
    │   ├── osm/2/roads_proj_ready.shp
    │   └── …
    ├── TPR03/
    │   ├── buildings_proj_ready.shp
    │   ├── roads_proj_ready.shp
    │   ├── chn_pd_2020_1km.tif
    │   └── …
    └── TPR04/
        ├── buildings_proj_ready.shp
        ├── roads_proj_ready.shp
        └── …
```

## 三种获取方式

1. **已有数据**：设置环境变量指向它即可，代码不用改

   ```bash
   # Windows (PowerShell)
   $env:PPW_DATA_DIR = "D:\my\risk_data"
   # Linux / macOS
   export PPW_DATA_DIR=/data/risk
   ```

2. **从原始矢量重建**（需要 `vectors/` 下的 shapefile 与人口栅格）：

   ```bash
   python risk_tensor_tpr2.py     # -> TPR02/Layer_*.npy, env_tensor_4D_Final.npy
   python risk_tensor_tpr3.py
   python risk_tensor_tpr4.py
   python rebuild_risk_model.py   # -> env_tensor_4D_v2.npy
   python build_ablation.py       # -> ablation/env_tensor_abl_*.npy
   ```

3. **只做小规模验证**：不需要任何数据，直接 `python test.py`（在内存里构造
   100×100×30 的合成风险场）。

## 说明

- 张量约定：`(时间, 高度层, y, x)`，2 m 网格，75 层；数值 0–100，其中建筑
  遮挡处为 `100`，`algorithms.RISK_OBSTACLE = 0.995` 是在 `/100` 归一化后
  判定障碍的阈值。
- 规划时用 `STEP = 5` 粗化到 10 m 网格（`150 × 150 × 15`），见
  `run_experiments.py`。
