# -*- coding: utf-8 -*-
"""Build the per-slide speaker notes as a Word document."""
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

OUT = str(config.PROJECT_DIR / "ppt" / "汇报摘要_逐页.docx")

BLUE = RGBColor(0x2D, 0x2D, 0xB9)
GREY = RGBColor(0x33, 0x33, 0x33)
MUTED = RGBColor(0x77, 0x80, 0x8F)
FONT = "微软雅黑"

NOTES = [
    ("第 1 页　封面", "封面", [
        "各位老师上午好，我汇报的题目是《面向无人机路径规划的三维城市动态风险建模方法》。",
        "这项工作由我和几位同学共同完成，指导教师是付先平教授。",
    ]),
    ("第 2 页　目录", "目录", [
        "汇报分四部分：研究背景与问题、四维风险场的构建、规划方法与实验、结果与结论。",
        "重点放在第二部分和第三部分，因为方法上的改动和实验证据都在那里。",
    ]),
    ("第 3 页　研究背景", "研究背景", [
        "无人机正从郊区、试验空域进入人口密集的城市建成区，作业高度通常只有几十米到一百多米。",
        "这个高度带恰好覆盖城市人口活动最集中的空间层，航迹正下方就是街道、住宅和商圈。",
        "因此城市低空运行必须同时回答两个问题：会不会撞上建筑，以及坠落时会不会伤到地面的人。",
    ]),
    ("第 4 页　现有方法的问题", "现有方法的问题", [
        "围绕城市低空的路径规划已有不少工作，但在风险的使用方式上存在三处简化。",
        "一是只用某一时刻的风险图并沿用于全程；二是把风险折算成固定的距离惩罚项；三是只考虑碰撞概率，忽略财产与噪声。",
        "三者叠加的结果是，规划所依据的代价场无法反映真实暴露，优化结果与实际风险之间存在偏差。",
    ]),
    ("第 5 页　总体框架", "总体框架", [
        "整体流程分三段：左侧是数据输入，建筑轮廓、人口栅格与出行曲线进入建模环节。",
        "中间是风险场构建，语义推断给出五类地类，人口按时段重分配，三类风险归一化后融合为四维张量。",
        "右侧是规划与评价，四种算法在同一风险场上搜索，结果汇总为累计风险、飞越暴露与路径代价。",
    ]),
    ("第 6 页　贡献一：地类推断", "贡献一：地类推断", [
        "城市尺度上很难拿到逐栋的用地属性，而地类恰恰决定了人口按什么权重分布。",
        "本文不依赖额外调查，只用建筑高度、建筑数量和占地面积三个可从轮廓数据直接得到的特征，按规则链把建筑划成五类。",
        "人工抽检 50 栋，其中 46 栋判断正确，正确率 92%，四处误判都是底层商业、上层住宅的混合用地。",
    ]),
    ("第 7 页　贡献二：人口与交通", "贡献二：人口与交通", [
        "人口基底按地类权重与建筑层数生成，而不是把人口均匀铺在地面上。",
        "更关键的是时段重分配：迁移系数只负责把人口在各功能区之间搬运，重分配前后总量严格守恒，误差小于十的负六次方。",
        "交通风险则沿路网聚集，用路侧缓冲与早晚双峰曲线刻画，两类风险的空间形态明显不同。",
    ]),
    ("第 8 页　贡献三：四维风险场", "贡献三：四维风险场", [
        "三类风险的物理机理不同：致死来自坠落动能，财产与建筑价值相关，噪声随距离衰减。",
        "本文先各自归一化到零一区间，再按可解释的权重融合为单一代价场，并叠加时间维得到四维风险张量。",
        "这样得到的不是一张图，而是一个随空间与时间连续变化的场。",
    ]),
    ("第 9 页　贡献四：到达时刻取风险", "贡献四：到达时刻取风险", [
        "静态风险图在出发时刻算一次，整条航迹都用它；但无人机飞到第三个航路点时，地面的人口分布已经变了。",
        "本文把风险表成时间的函数，搜索扩展到一个节点时，取该节点预计到达时刻对应的风险切片参与代价计算。",
        "时间维度由此进入搜索本身，规划器可以在“早飞穿过高风险区”与“绕行延长航程”之间做真正的时间权衡。",
    ]),
    ("第 10 页　实验一：三个时段", "实验一：三个时段", [
        "三个时段各规划一次，Risk-A* 的累计风险分别是 39.7、155.3 和 142.4，对应 A* 的 127.5、230.4 和 221.2。",
        "降幅依次为 68.9%、32.6% 与 35.6%，而路径长度只从 2256 米增加到 2287 米左右，增幅不足 4.1%。",
        "凌晨收益最大，因为此时风险集中在少数斑块，绕行成本低；早高峰人口整体抬升、风险面趋于平坦，降幅随之收窄。",
    ]),
    ("第 11 页　实验二：城市密度", "实验二：城市密度", [
        "同一方法搬到低、中、高三种密度城区，累计风险分别降低 35.6%、42.8% 与 60.7%。",
        "高密度区 A* 的累计风险是低密度区的两倍多，而 Risk-A* 只上升到 1.4 倍，说明风险感知规划能抑制风险随密度增长的势头。",
        "代价是路径长度从 2251 米延长到 2343 米，仍控制在 4% 出头。",
    ]),
    ("第 12 页　实验三：消融", "实验三：消融", [
        "把风险场逐项拆开看：只保留建筑避障时，A* 的累计风险只有 64.6，说明这类规划几乎不触及地面风险。",
        "加入人口项后升到 166.5，再加入交通项达到 221.2；后两项合计解释了 99.4% 的风险量。",
        "可见本文风险场的作用主要来自人口与交通的时空建模，而不是更精细的几何避障。",
    ]),
    ("第 13 页　实验四：时间与参数", "实验四：时间与参数", [
        "同一任务把出发时刻从八点提前到六点，累计风险由 203.6 降到 140.2，降幅 31.1%，与换算法带来的收益同一量级。",
        "而一次短程飞行内部按到达时刻取风险，风险只变化 0.92%，速度提高三倍也只带来 0.4% 到 1.7% 的差别。",
        "把风险权重整体上浮 25%，Risk-A* 依旧低于 A*；60 组随机扰动下降幅落在 26.7% 到 35.4% 之间，全部优于 A*。",
    ]),
    ("第 14 页　结论与展望", "结论与展望", [
        "结论有三条：风险场的时空结构不可忽略；风险感知规划的收益随密度上升；时间维度的作用在出发时刻而非航程内部。",
        "展望方面，这套框架可以推广到更多城市与时段，时段参数可由实测客流标定，还可以计入风场、动态障碍与通信约束，并走向多机协同。",
    ]),
    ("第 15 页　致谢", "致谢", [
        "我的汇报到这里，感谢各位老师，请批评指正。",
    ]),
]

doc = Document()

style = doc.styles["Normal"]
style.font.name = FONT
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

h = doc.add_heading(level=0)
run = h.add_run("汇报摘要（逐页）")
run.font.name = FONT
run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
run.font.color.rgb = BLUE

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = sub.add_run("论文：面向无人机路径规划的三维城市动态风险建模方法　｜　汇报人：韩文熙　｜　共 15 页")
r.font.size = Pt(9.5)
r.font.color.rgb = MUTED
r.font.name = FONT
r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

for title, en, lines in NOTES:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(title)
    r1.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = BLUE
    r1.font.name = FONT
    r1._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)


    for line in lines:
        q = doc.add_paragraph(line)
        q.paragraph_format.space_after = Pt(3)
        q.paragraph_format.line_spacing = 1.35
        q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run_ in q.runs:
            run_.font.name = FONT
            run_.font.size = Pt(10.5)
            run_.font.color.rgb = GREY
            run_._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

doc.save(OUT)

# verify
d = Document(OUT)
paras = [p.text for p in d.paragraphs if p.text.strip()]
print("saved", OUT)
print("paragraphs:", len(paras))
print("first:", paras[0])
print("last:", paras[-1])
print("size KB:", os.path.getsize(OUT) // 1024)
