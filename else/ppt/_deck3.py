# -*- coding: utf-8 -*-
"""Rebuild pages 5-16 in place: new contributions, new experiment layout, prose style."""
import os
import shutil

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

P = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版_美化.pptx")
BAK = P.replace(".pptx", "_旧版.pptx")
if not os.path.exists(BAK):
    shutil.copy2(P, BAK)

FIG = str(config.PROJECT_DIR / "中文版" / "figs")
AS = str(config.PROJECT_DIR / "ppt" / "assets")
FW = str(config.PROJECT_DIR / "ppt" / "框架图_分层版.png")

BLUE = RGBColor(0x2D, 0x2D, 0xB9)
TEAL = RGBColor(0x0E, 0x8A, 0x6E)
INK = RGBColor(0x1B, 0x2A, 0x4A)
GREY = RGBColor(0x33, 0x33, 0x33)
MUTED = RGBColor(0x83, 0x8D, 0x9E)
CARD = RGBColor(0xF4, 0xF8, 0xFA)
EDGE = RGBColor(0xD9, 0xE4, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"

prs = Presentation(P)
W = prs.slide_width
LAYOUT = [l for l in prs.slide_masters[0].slide_layouts if l.name.strip() == "仅标题"][0]

sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
closing = ids[-1]
for el in ids[4:-1]:
    prs.part.drop_rel(el.get(qn("r:id")))
    sldIdLst.remove(el)


def style(run, size, bold=False, color=GREY):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)


def slide(title):
    s = prs.slides.add_slide(LAYOUT)
    s.shapes.title.text = title
    for p in s.shapes.title.text_frame.paragraphs:
        p.alignment = PP_ALIGN.LEFT
        for r in p.runs:
            style(r, 27, True, BLUE)
    return s


def txt(s, x, y, w, h, text, size=13, color=GREY, bold=False, align=PP_ALIGN.LEFT, spacing=1.4):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = ln
        style(r, size, bold, color)
    return tb


def pic(s, path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def size_of(path):
    return Image.open(path).size


def place(s, path, x, y, w):
    iw, ih = size_of(path)
    h = w * ih / iw
    pic(s, path, x, y, w=w, h=h)
    return h


def card(s, x, y, w, h, fill=CARD, edge=EDGE, radius=0.05):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid()
    b.fill.fore_color.rgb = fill
    b.line.color.rgb = edge
    b.shadow.inherit = False
    b.adjustments[0] = radius


def frame(s, num):
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.95), Inches(1.9), Inches(11.4), Inches(0.02))
    ln.fill.solid(); ln.fill.fore_color.rgb = EDGE; ln.line.fill.background(); ln.shadow.inherit = False
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.62), Inches(2.0), Inches(0.05), Inches(4.85))
    bar.fill.solid(); bar.fill.fore_color.rgb = TEAL; bar.line.fill.background(); bar.shadow.inherit = False
    ft = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.0), Inches(7.14), W, Inches(0.36))
    ft.fill.solid(); ft.fill.fore_color.rgb = RGBColor(0xF6, 0xF8, 0xFA); ft.line.fill.background()
    ft.shadow.inherit = False
    txt(s, 0.95, 7.19, 9.0, 0.26, "面向无人机路径规划的三维城市动态风险建模方法", size=8.5, color=MUTED)
    txt(s, 11.4, 7.19, 1.3, 0.26, "%02d" % num, size=9, color=MUTED, bold=True, align=PP_ALIGN.RIGHT)


# ======================================================= 5 总体框架
s = slide("总体框架：从数据到评价的完整链路")
h = place(s, FW, 0.95, 2.0, 6.85)
txt(s, 8.1, 2.05, 4.5, 2.0,
    "整个流程分三段。左侧是数据输入：建筑轮廓决定三维障碍与地类，人口栅格与出行曲线提供地面活动强度。",
    size=12.5)
txt(s, 8.1, 3.55, 4.5, 2.2,
    "中间是风险场构建：语义推断给出五类地类，人口按时段重分配，致死、财产与噪声三类风险归一化后融合为四维张量。",
    size=12.5)
txt(s, 8.1, 5.15, 4.5, 1.8,
    "右侧是规划与评价：四种算法在同一风险场上搜索，结果汇总为累计风险、飞越暴露与路径代价，用于横向比较。",
    size=12.5)
frame(s, 5)

# ======================================================= 6 贡献一：地物推断
s = slide("贡献一：由建筑形态学推断城市地类")
place(s, os.path.join(AS, "t6.png"), 0.95, 2.05, 6.5)
txt(s, 0.95, 4.95, 6.5, 2.0,
    "城市尺度上难以获得逐栋的用地属性，而地类恰恰决定了人口按什么权重分布，也决定了风险计算的底图。"
    "本文不依赖额外调查数据，仅用建筑高度 H、建筑数量 N_f 与占地面积 S_b 三个可直接从轮廓数据得到的特征，"
    "按规则链把建筑划入商业、工业、公共、住宅与其他五类，为后续人口分配提供语义锚点。",
    size=12)
place(s, os.path.join(FIG, "figure1.png"), 7.75, 2.05, 3.5)
txt(s, 7.75, 5.75, 4.6, 1.3,
    "人工抽检 50 栋建筑，46 栋判定正确（92%）；4 处误判均为底层商业、上层住宅的混合用地。",
    size=11.5, color=TEAL, bold=True)
frame(s, 6)

# ======================================================= 7 贡献二：人车流
s = slide("贡献二：人口与交通的时空模型")
h1 = place(s, os.path.join(FIG, "figure8.png"), 0.95, 2.0, 5.8)
txt(s, 0.95, 2.0 + h1 + 0.04, 5.8, 0.3, "人口暴露分量（三个时段）", size=10.5, color=MUTED)
h2 = place(s, os.path.join(FIG, "figure9.png"), 0.95, 2.0 + h1 + 0.42, 5.8)
txt(s, 0.95, 2.0 + h1 + 0.42 + h2 + 0.04, 5.8, 0.3, "交通风险分量（三个时段）", size=10.5, color=MUTED)
place(s, os.path.join(AS, "f_base.png"), 7.35, 2.05, 4.9)
place(s, os.path.join(AS, "f_time.png"), 7.35, 3.15, 4.9)
txt(s, 7.35, 4.15, 5.0, 2.7,
    "人口基底按地类权重与层数生成，而不是把人口均匀铺在地面上。更关键的是时段重分配："
    "迁移系数 γ 只负责把人口在各功能区之间搬运，重分配前后总量严格守恒，误差小于 1e-6，"
    "再乘以外出活动系数 η(t)。交通风险则沿路网聚集，用路侧缓冲与双峰时段曲线刻画。",
    size=11.5)
frame(s, 7)

# ======================================================= 8 贡献三：风险场
s = slide("贡献三：多源风险融合的四维风险场")
place(s, os.path.join(FIG, "figure7.png"), 0.95, 2.0, 6.4)
txt(s, 0.95, 4.05, 6.4, 0.3, "三个时段的二维风险场切片", size=10.5, color=MUTED)
place(s, os.path.join(AS, "f_cost.png"), 0.95, 4.5, 6.2)
txt(s, 0.95, 5.25, 6.4, 1.6,
    "三类风险的物理机理不同：致死风险来自坠落动能，财产风险与建筑价值相关，噪声风险随距离衰减。"
    "本文先各自归一化到 [0,1]，再按可解释的权重融合为单一代价场，并叠加时间维得到四维风险张量。",
    size=11.5)
place(s, os.path.join(FIG, "figure2.png"), 7.7, 2.0, 4.9)
txt(s, 7.7, 4.75, 4.9, 1.8,
    "建筑体元设为不可通行，风险只在可飞行的空域中定义；权重可按任务偏好调整，例如夜间任务提高噪声项比重。",
    size=11.5)
frame(s, 8)

# ======================================================= 9 贡献四：到达时刻
s = slide("贡献四：按到达时刻取用风险的规划")
card(s, 0.95, 2.0, 6.4, 4.3, fill=WHITE)
txt(s, 1.15, 2.1, 6.0, 0.35, "航路点与风险切片的对应关系", size=12, color=BLUE, bold=True)

pts = [(1.9, 4.9), (3.4, 4.2), (4.9, 4.7)]
for i in range(len(pts) - 1):
    ln = s.shapes.add_connector(1, Inches(pts[i][0]), Inches(pts[i][1]),
                                Inches(pts[i + 1][0]), Inches(pts[i + 1][1]))
    ln.line.color.rgb = TEAL
    ln.line.width = Pt(1.75)
for i, (x, y) in enumerate(pts):
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x - 0.16), Inches(y - 0.16), Inches(0.32), Inches(0.32))
    o.fill.solid(); o.fill.fore_color.rgb = TEAL; o.line.fill.background(); o.shadow.inherit = False
    txt(s, x - 0.35, y + 0.2, 0.9, 0.3, "t%d" % (i + 1), size=11, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

for i, yy in enumerate([3.35, 4.35, 5.35]):
    card(s, 5.55, yy, 1.55, 0.7, fill=RGBColor(0xEA, 0xF3, 0xEF), edge=TEAL)
    txt(s, 5.55, yy + 0.19, 1.55, 0.35, "T(t%d)" % (i + 1), size=11, color=TEAL,
        bold=True, align=PP_ALIGN.CENTER)
    ln = s.shapes.add_connector(1, Inches(pts[i][0] + 0.2), Inches(pts[i][1]),
                                Inches(5.5), Inches(yy + 0.35))
    ln.line.color.rgb = MUTED
    ln.line.width = Pt(1.0)
    ln.line.dash_style = 3
txt(s, 1.15, 5.85, 6.0, 0.4, "每个节点只取自己到达时刻的那一片", size=11, color=MUTED)

txt(s, 7.75, 2.05, 4.7, 4.4,
    "静态风险图在出发时刻算一次，整条航迹都用它；但无人机飞到第三个航路点时，地面的人口分布已经变了。"
    "本文的改法是把风险表成时间的函数，搜索扩展到一个节点时，取该节点预计到达时刻 t 对应的风险切片参与代价计算。"
    "这样时间维度进入搜索本身，而不是等到事后评价才被提及。"
    "规划器因此可以在“早飞穿过高风险区”与“绕行延长航程”之间做真正的时间权衡。",
    size=12.5)
frame(s, 9)

# ======================================================= 10-13 experiments
def fit_table(path, max_w, avail_h):
    iw, ih = size_of(path)
    ar = iw / ih
    w = min(max_w, avail_h * ar)
    return w, w / ar


def experiment(num, title, fig, cap1, tab, cap2, summary, fw=5.2, tw=6.3):
    s = slide(title)
    hf = place(s, fig, 0.95, 1.98, fw)
    txt(s, 0.95, 1.98 + hf + 0.04, fw + 0.4, 0.28, cap1, size=10, color=MUTED)
    ytab = 1.98 + hf + 0.42
    tw, ht = fit_table(tab, tw, 6.95 - ytab - 0.3)
    place(s, tab, 0.95, ytab, tw)
    txt(s, 0.95, ytab + ht + 0.04, max(tw, 4.4), 0.28, cap2, size=10, color=MUTED)
    txt(s, 7.55, 2.0, 4.95, 4.7, summary, size=12)
    frame(s, num)
    return s


experiment(10, "实验一：三个时段的风险代价与路径代价",
           os.path.join(FIG, "figure12.png"), "图：沿轨迹的累计风险曲线",
           os.path.join(AS, "t1.png"), "表：三个时段、两种算法的规划结果",
           "三个时段各规划一次，Risk-A* 的累计风险分别为 39.7、155.3 和 142.4，"
           "对应 A* 的 127.5、230.4 和 221.2，降幅 68.9%、32.6% 与 35.6%。"
           "路径长度只从 2256 m 增加到 2287 m 左右，增幅不足 4.1%，单位长度风险 RC/L 同步下降到原来的三分之一到三分之二。"
           "04:00 的收益最大，因为此时风险集中在少数斑块，绕行成本低；08:00 人口整体抬升、风险面趋于平坦，降幅随之收窄。",
           fw=5.0, tw=6.4)

experiment(11, "实验二：城市密度对规划收益的影响",
           os.path.join(FIG, "figure13.png"), "图：三种城市密度下的规划轨迹",
           os.path.join(AS, "t2.png"), "表：三种密度、两种算法的规划结果",
           "同一方法搬到低、中、高三种密度城区，累计风险由 221.2、221.5、516.9 分别降到 142.4、126.7 和 203.4，"
           "降幅依次为 35.6%、42.8% 与 60.7%。高密度区 A* 的累计风险是低密度区的两倍多，"
           "而 Risk-A* 只上升到 1.4 倍，说明风险感知规划在密集城区更能抑制风险随密度增长的趋势。"
           "代价是路径长度从 2251 m 延长到 2343 m，仍控制在 4% 出头。",
           fw=5.0, tw=6.4)

experiment(12, "实验三：风险因素消融的结果",
           os.path.join(FIG, "figure14.png"), "图：不同风险配置下的风险场与轨迹",
           os.path.join(AS, "t3.png"), "表：三种配置、两种算法的规划结果",
           "把风险场逐项拆开看：只保留建筑避障时，A* 的累计风险仅 64.6，Risk-A* 甚至降到 0.3，"
           "说明这类规划几乎不触及地面风险；加入人口项后升至 166.5 和 97.0，再加入交通项达到 221.2 与 142.4。"
           "人口与交通两项合计解释了 99.4% 的风险量，可见本文风险场的作用主要来自人口与交通的时空建模，"
           "而消融实验也验证了每个分量都在起作用。",
           fw=5.0, tw=6.4)

# ---------------- 实验四：时间与参数 ----------------
s = slide("实验四：出发时刻、飞行速度与参数扰动的影响")
place(s, os.path.join(FIG, "figure15.png"), 0.95, 1.98, 4.6)
txt(s, 0.95, 4.72, 5.1, 0.28, "图：60 组参数扰动下的风险降幅分布", size=10, color=MUTED)
tw, ht = fit_table(os.path.join(AS, "t4.png"), 6.5, 6.95 - 5.05 - 0.3)
place(s, os.path.join(AS, "t4.png"), 0.95, 5.05, tw)
txt(s, 0.95, 5.05 + ht + 0.04, 6.5, 0.28, "表：权重上浮与蒙特卡洛的结果", size=10, color=MUTED)
txt(s, 7.55, 2.0, 4.95, 4.8,
    "先看时间：同一任务把出发时刻从 08:00 提前到 06:00，累计风险由 203.6 降到 140.2，降幅 31.1%，"
    "与换算法带来的收益同一量级；而在一次短程飞行内部按到达时刻取风险，风险只变化 0.92%，"
    "速度从 5 m/s 提到 20 m/s 也只带来 0.4%–1.7% 的差别——时间维度的价值在“何时起飞”。"
    "再看参数：把风险权重整体上浮 25%，两个时段的风险升到 193.1 与 183.7，但 Risk-A* 依旧低于 A*；"
    "60 组随机扰动下降幅落在 26.7%–35.4%，中位 31.4%，全部优于 A*。结论方向不随参数取值改变。",
    size=11.5)
frame(s, 13)

# ======================================================= 14 结论与展望
s = slide("结论与展望")
txt(s, 0.95, 1.98, 3.0, 0.34, "结论", size=14, color=TEAL, bold=True)
items = [
    ("（1）风险场的时空结构不可忽略。",
     "总量守恒的四维风险场能够刻画人口与交通在一日之内的迁移；若按固定时刻建图，代价场会系统性偏离真实暴露，"
     "规划结果看似最优，实际并不对应最低风险。"),
    ("（2）风险感知规划的收益随城市密度上升。",
     "三个时段累计风险分别降低 68.9%、32.6% 与 35.6%，飞越人口暴露降低 20.0%，路径仅增长不超过 4.1%；"
     "三种密度下降幅由 35.6% 增至 60.7%，密集城区收益最明显。"),
    ("（3）时间维度的作用在出发时刻而非航程内部。",
     "改变出发时刻可使风险变化 31.1%，而航程内的风险漂移仅 0.92%、速度影响 0.4%–1.7%，"
     "说明管控的关键在于时段调度，而不是更细的时间切片。"),
]
y = 2.35
for head, body in items:
    txt(s, 0.95, y, 7.3, 0.3, head, size=11.5, color=BLUE, bold=True)
    txt(s, 0.95, y + 0.3, 7.3, 0.8, body, size=10.5, color=GREY, spacing=1.25)
    y += 1.12

card(s, 8.55, 2.0, 3.95, 4.75, fill=RGBColor(0xEA, 0xF3, 0xEF), edge=TEAL)
txt(s, 8.75, 2.1, 3.6, 0.32, "展望", size=14, color=TEAL, bold=True)
txt(s, 8.75, 2.5, 3.6, 4.1,
    "本文的框架是可扩展的。同一建模流程可以推广到更多城市与更多时段，检验方法在不同城市结构下的可迁移性；"
    "重分配系数与外出系数可由实测客流与交通数据标定，模型结构无需改动；"
    "在横截面上还可以计入风场、动态障碍与通信约束，使规划结果更接近真实运行环境；"
    "并进一步由单机离线规划走向多机协同与在线重规划。",
    size=10.5, color=GREY, spacing=1.3)
frame(s, 14)

sldIdLst.remove(closing)
sldIdLst.append(closing)

prs.save(P)
print("saved in place:", P, "slides:", len(prs.slides))
