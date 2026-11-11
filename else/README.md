# else/ — 归档脚本

这里放的是**不属于论文主流程**、但以后可能还会用到的脚本。它们不参与
`run_experiments.py` → `make_*.py` 的复现链路，删除也不会影响论文结果的复现。

所有这些脚本都通过 `config.py` 取路径。它们被移出仓库根目录后，仍在文件开头
插入了两行 `sys.path` 引导代码，因此可以直接运行：

```bash
python else/wsweep.py
```

---

## 探索性分析与出图

| 脚本 | 用途 | 产出 |
|---|---|---|
| `note.py` | 四维风险张量融合的**早期原型**（v0），已被 `rebuild_risk_model.py` 取代。保留它是因为"分时段不对称演化"的写法（早高峰超线性、晚高峰扩散）值得留档 | — |
| `experiment_a.py` | 单区域内四种规划器的 3D 航迹对比 | `figures/A/*.png` |
| `experiment_b.py` | 低/中/高三个密度区的航迹对比 | `figures/A/*.png` |
| `experiment_c.py` | 消融三组（static / +pop / full）的航迹对比 | `figures/A/*.png` |
| `density_a.py` | 三个时段的 3D 风险曲面渲染（6 张图） | `figures/A/*.png` |
| `a_calculate.py` | 按分位数阈值统计高风险栅格数量，用于正文里的数字 | 控制台 |
| `2drisk_c.py` | 消融实验的 2D 热力图（统一色标） | `figures/A/c_ablation/*.png` |
| `3drisk_c.py` | 消融实验的 3D 风险面 | `figures/A/c_ablation/*.png` |
| `topview_b.py` | 三个密度区 18:00 的俯视渲染 | `figures/A/*.png` |
| `tpr3_1.py` | 消融组 1：纯静态风险张量（**v1 实现**，已被 `build_ablation.py` 取代） | `data/ablation/*.npy` |
| `tpr3_2.py` | 消融组 2：静态 + 人口动态（v1） | 同上 |
| `tpr3_3.py` | 消融组 3：全要素（v1） | 同上 |

> `tpr3_1/2/3.py` 与根目录的 `build_ablation.py` 结果等价，但后者复用
> `rebuild_risk_model.py` 的算子，三组张量共享同一个尺度。复现论文请用
> `build_ablation.py`。

## 敏感性扫描

| 脚本 | 用途 | 产出 |
|---|---|---|
| `v_sweep.py` | 步行速度 `v` 对"时间一致性"指标（RC 数组化 vs 快照）的影响 | 控制台 |
| `v_sweep2.py` | 出发时刻 `t0` × 速度 `v` 的二维扫描 | 控制台 |
| `wsweep.py` | 加权 A* 的启发式膨胀系数 `w` 的速度—风险权衡 | `results/wsweep.json` |

## 结果速查

| 脚本 | 用途 |
|---|---|
| `_peek2.py` | 把 `results/time.json`、`density.json` 按规划器汇总成一张表打印出来（中位数节点数、耗时、路径长度、风险代价），写论文时核对数字用 |

## ppt/ — 汇报材料生成

这套脚本按顺序构成一条链，只对**原始论文工程**有效（依赖 `revision/ppt/`
下的模板与素材，这些文件不在本仓库内）。路径由 `config.PROJECT_DIR` 提供：

```bash
set PPW_PROJECT_DIR=D:\path\to\revision     # 指向原工程的 revision 目录
```

| 脚本 | 用途 |
|---|---|
| `_framework7.py` | 框架图（分层版），最终采用的一版 |
| `_flow_cn3.py` | 地类推断流程图（中文），最终采用的一版 |
| `_assets3.py` | 汇报用的三线表图片（由 `results/*.json` 的真实数字生成） |
| `_ppt1_tpl.py` | 基于开题报告模板重建论文汇报 PPT（模板路径可用 `PPW_DECK_TEMPLATE` 覆盖） |
| `_decorate.py` | 对模板版 PPT 做统一美化 |
| `_deck3.py` | 在美化版 PPT 上逐页填充正文与图片 |
| `_slide5b.py` | 单独重做某一页（替换/重排） |
| `make_notes_docx.py` | 由 PPT 逐页导出讲解稿 docx |

依赖：`python-pptx`、`python-docx`、`Pillow`（见根目录 `requirements.txt`
中被注释掉的那几行）。

---

## 已删除的脚本

以下文件在整理时删除（原工程 `revision/code/` 中仍完整保留）：

- `_framework.py`、`_framework2~6.py`、`_flow_cn.py`、`_flow_cn2.py`、
  `_assets.py`、`_assets2.py`、`_deck2.py`、`_ppt1.py`、`_slide5.py`
  —— 都是同一脚本的迭代中间版本，功能被上表中的"最终版"覆盖；
- `_patch_cls.py`、`_patch_deck.py` —— 直接改写其他源码文件的临时补丁脚本；
- `_shp.py` —— 临时查看 shapefile 坐标系的一行脚本；
- `_tpl_front.txt`、`_tpl_head.txt` —— PPT 版式文本草稿。
