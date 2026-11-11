# -*- coding: utf-8 -*-
"""Rebuild paper-1 talk on the DHU opening-report template."""
import copy
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

TPL = os.environ.get("PPW_DECK_TEMPLATE", str(config.PROJECT_DIR / "开题报告模板.pptx"))
FIG = str(config.PROJECT_DIR / "中文版" / "figs")
OUT = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版.pptx")

BLUE = RGBColor(0x2D, 0x2D, 0xB9)
TEAL = RGBColor(0x00, 0x99, 0x77)
TEAL_L = RGBColor(0xAA, 0xE2, 0xCA)
GREY = RGBColor(0x33, 0x33, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PALE = RGBColor(0xF2, 0xF8, 0xF6)

prs = Presentation(TPL)
W, H = prs.slide_width, prs.slide_height
LAYOUT_TITLE_ONLY = None
for l in prs.slide_masters[0].slide_layouts:
    if l.name.strip() == "仅标题":
        LAYOUT_TITLE_ONLY = l
assert LAYOUT_TITLE_ONLY is not None


def style(run, size, bold=False, color=GREY):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def tbox(slide, x, y, w, h, lines, size=18, color=GREY, bold=False,
         align=PP_ALIGN.LEFT, spacing=1.3):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        style(r, size, bold, color)
    return tb


def pic(slide, name, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(os.path.join(FIG, name), Inches(x), Inches(y), **kw)


def cap(slide, x, y, w, text):
    tbox(slide, x, y, w, 0.32, [text], size=11, color=RGBColor(0x77, 0x77, 0x77),
         align=PP_ALIGN.CENTER)


def content_slide(title):
    s = prs.slides.add_slide(LAYOUT_TITLE_ONLY)
    s.shapes.title.text = title
    for p in s.shapes.title.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(30)
            r.font.bold = True
            r.font.color.rgb = BLUE
    return s


def bullet_block(s, x, y, w, h, items, size=17, gap=9):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.35
        p.space_after = Pt(gap)
        r1 = p.add_run()
        r1.text = "■ "
        style(r1, size - 3, False, TEAL)
        r2 = p.add_run()
        r2.text = it
        style(r2, size, False, GREY)
    return tb


# ---------------------------------------------------------------- cover
from copy import deepcopy
s1 = prs.slides[0]
for sh in s1.shapes:
    if not sh.has_text_frame:
        continue
    t = sh.text_frame.text.strip()
    if t == "基于研究":
        sh.top = Inches(1.50)
        sh.height = Inches(1.45)
        tf = sh.text_frame
        p1 = tf.paragraphs[0]
        p1.runs[0].text = "面向无人机路径规划的"
        p1.runs[0].font.size = Pt(34)
        newp = deepcopy(p1._p)
        p1._p.addnext(newp)
        tf.paragraphs[1].runs[0].text = "三维城市动态风险建模方法"
        tf.paragraphs[1].runs[0].font.size = Pt(34)
    elif t.startswith("汇报人"):
        sh.text_frame.paragraphs[0].runs[0].text = "汇报人：韩文熙"
    elif t.startswith("大连海事大学硕士"):
        sh.text_frame.paragraphs[0].runs[0].text = "大连海事大学  学术交流报告"

# ---------------------------------------------------------------- agenda
s2 = prs.slides[1]
agenda = ["   一、研究背景与问题", "   二、四维风险场构建", "   三、规划方法与实验", "   四、结果与讨论"]
gi = 0
for sh in s2.shapes:
    if sh.shape_type == 6:
        for sub in sh.shapes:
            if sub.has_text_frame and sub.text_frame.text.strip():
                sub.text_frame.text = ""
                r = sub.text_frame.paragraphs[0].add_run()
                r.text = agenda[gi]
                style(r, 22, True, BLUE)
        gi += 1

# ---------------------------------------------------------------- closing kept, slide 4 removed
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
dup = ids[3]
_rid = dup.get(qn('r:id'))
prs.part.drop_rel(_rid)          # remove the part, not only the reference
sldIdLst.remove(dup)             # drop duplicate closing slide
closing_id = ids[2]              # keep this one for the end

# ---------------------------------------------------------------- content
# 1 背景
s = content_slide("研究背景：城市低空运行的双重约束")
bullet_block(s, 0.95, 2.05, 6.2, 4.6, [
    "低空经济成为国家战略性新兴产业，城市低空作业快速增长",
    "物流、巡检、应急救援等任务向高密度城区延伸",
    "无人机必须同时回答：会不会撞建筑？会不会伤到人？",
    "与高空不同，城市低空航迹的正下方就是人口与财产",
    "风险不是常数——随人口流动与交通活动在一天内变化",
], size=16)
pic(s, "figure2.png", 7.35, 2.15, w=5.3)
cap(s, 7.35, 6.55, 5.3, "无人机运行与三类地面风险")

# 2 问题
s = content_slide("问题：现有方法的三处不足")
cards = [("① 静态风险图", "只反映某一时刻的暴露，\n忽略人口与交通的日内迁移"),
         ("② 距离主导代价", "风险被折算为固定惩罚项，\n空间结构被抹平"),
         ("③ 风险维度单一", "多只考虑碰撞概率，\n财产与噪声被忽略")]
for i, (h, d) in enumerate(cards):
    x = 0.9 + i * 4.05
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.15), Inches(3.7), Inches(2.35))
    c.fill.solid()
    c.fill.fore_color.rgb = PALE
    c.line.color.rgb = TEAL_L
    c.shadow.inherit = False
    c.adjustments[0] = 0.07
    tbox(s, x + 0.22, 2.32, 3.3, 0.45, [h], size=19, color=BLUE, bold=True)
    tbox(s, x + 0.22, 2.9, 3.3, 1.4, d.split("\n"), size=14, color=GREY, spacing=1.35)
arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(3.4), Inches(4.75), Inches(6.5), Inches(0.4))
arrow.fill.solid()
arrow.fill.fore_color.rgb = TEAL
arrow.line.fill.background()
tbox(s, 0.9, 5.35, 11.6, 1.1,
     ["结果：风险表达与真实暴露之间存在系统性偏差，", "规划器优化的其实是一个并不存在的风险分布。"],
     size=18, color=TEAL, bold=True, align=PP_ALIGN.CENTER, spacing=1.4)

# 3 贡献
s = content_slide("本文工作：四项贡献")
contrib = [("① 四维风险场", "总量守恒的时空风险表达：三维空间 + 时间"),
           ("② 三类风险融合", "致死、财产、噪声统一到归一化代价场"),
           ("③ 到达时刻取风险", "风险按航路点到达时刻取用，时间维度进入规划"),
           ("④ 控制变量对比", "A* 与 Risk-A* 同码不同代价；PSO 与 RRT* 覆盖其他范式")]
y = 2.05
for i, (h, d) in enumerate(contrib):
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.95), Inches(y), Inches(0.08), Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()
    tbox(s, 1.2, y - 0.02, 3.0, 0.45, [h], size=18, color=BLUE, bold=True)
    tbox(s, 4.3, y, 8.2, 0.8, [d], size=15, color=GREY, spacing=1.25)
    y += 1.15

# 4 框架
s = content_slide("总体技术框架")
steps = ["语义推断", "人口基底", "时序重分配", "风险融合", "路径规划", "暴露评价"]
x = 0.75
for i, st in enumerate(steps):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.75), Inches(1.62), Inches(0.9))
    b.fill.solid()
    b.fill.fore_color.rgb = BLUE if i < 4 else TEAL
    b.line.fill.background()
    b.shadow.inherit = False
    b.adjustments[0] = 0.18
    p = b.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = st
    style(r, 14, True, WHITE)
    if i < 5:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.66), Inches(3.08), Inches(0.28), Inches(0.24))
        a.fill.solid()
        a.fill.fore_color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
        a.line.fill.background()
    x += 1.99
tbox(s, 0.95, 4.05, 5.4, 2.0,
     ["输入", "OpenStreetMap 建筑轮廓", "WorldPop 人口栅格", "三时段出行强度曲线"],
     size=14, color=GREY, spacing=1.5)
tbox(s, 6.6, 4.05, 5.7, 2.0,
     ["输出", "四维风险张量 T(x, y, z, t)", "风险感知航迹与累计风险", "飞越人口暴露量"],
     size=14, color=GREY, spacing=1.5)
tbox(s, 0.95, 6.35, 11.4, 0.5, ["空间范围 2 km × 2 km × 150 m，2 m 体素；规划栅格 10 m（5×5×5 聚合）"],
     size=12, color=RGBColor(0x77, 0x77, 0x77), align=PP_ALIGN.CENTER)

# 5 语义
s = content_slide("四维风险场（一）：建筑形态学的语义推断")
bullet_block(s, 0.95, 2.05, 5.2, 4.6, [
    "输入特征：原始地类、建筑数量、高度、占地面积",
    "规则链：高度 ≥20 m 且 N_f ≥15 → 商业",
    "　　　　S_b ≥2500 m² 且 N_f ≥10 → 工业",
    "　　　　S_b ≥500 m² 且 1≤N_f≤3 → 住宅",
    "输出五类地类，为人口与风险提供锚点",
], size=15)
pic(s, "figure1.png", 6.5, 2.0, h=4.7)
cap(s, 6.5, 6.75, 6.0, "基于规则的建筑语义属性推断流程")

# 6 人口与时序
s = content_slide("四维风险场（二）：人口基底与时序重分配")
tbox(s, 0.95, 2.0, 5.6, 0.4, ["人口基底"], size=17, color=BLUE, bold=True)
tbox(s, 0.95, 2.4, 5.8, 0.5, ["P_base = w(type) · min(H/3, 30)"], size=19, color=TEAL, bold=True)
tbox(s, 0.95, 3.0, 5.8, 0.9, ["w(type)：地类权重；H：建筑高度", "层数越高、地类越密集，基底人口越大"],
     size=14, color=GREY, spacing=1.35)
tbox(s, 0.95, 4.0, 5.6, 0.4, ["时段重分配（总量守恒）"], size=17, color=BLUE, bold=True)
tbox(s, 0.95, 4.45, 5.9, 2.3,
     ["P(x, y, t) = P_base(x, y) · γ(class, t) · η(t)",
      "γ：功能区之间的迁移系数，按区域总量归一化",
      "η(t) = 0.35（04:00）/ 1.00（08:00）/ 0.85（18:00）"],
     size=14, color=GREY, spacing=1.5)
pic(s, "figure8.png", 7.15, 2.1, w=5.5)
cap(s, 7.15, 6.55, 5.5, "三个时段的人口暴露分量")

# 7 风险建模
s = content_slide("风险代价建模：从物理过程到归一化代价")
bullet_block(s, 0.95, 2.05, 4.9, 4.4, [
    "致死风险：坠落运动学 → 撞击动能 → 致死概率",
    "财产风险：单位面积价值 × 受损范围",
    "噪声风险：声压级衰减 × 受影响人口",
    "融合权重 0.4 / 0.3 / 0.2 / 0.1",
    "归一化到 [0,1]，建筑体元不可通行",
], size=14)
pic(s, "figure3.png", 6.05, 2.0, w=3.1)
cap(s, 6.05, 3.45, 3.1, "高度剖面与垂直离散")
pic(s, "figure5.png", 9.4, 2.0, w=3.1)
cap(s, 9.4, 3.45, 3.1, "财产损失风险分布")
pic(s, "figure4.png", 6.05, 3.95, w=3.1)
cap(s, 6.05, 5.4, 3.1, "坠落运动学示意")
pic(s, "figure6.png", 9.4, 3.95, w=3.1)
cap(s, 9.4, 5.4, 3.1, "噪声影响代价分布")

# 8 规划
s = content_slide("规划方法：让时间进入搜索")
tbox(s, 0.95, 2.0, 5.6, 0.4, ["两种代价函数，同一套搜索代码"], size=16, color=BLUE, bold=True)
box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.95), Inches(2.45), Inches(5.7), Inches(1.05))
box.fill.solid()
box.fill.fore_color.rgb = PALE
box.line.color.rgb = TEAL_L
box.shadow.inherit = False
tbox(s, 1.15, 2.55, 5.3, 0.9,
     ["A*：f = g + h（仅距离）", "Risk-A*：f = g + h + λ·C_risk，λ = 1"],
     size=14, color=GREY, spacing=1.4)
tbox(s, 0.95, 3.65, 5.6, 0.4, ["关键细节：风险按到达时刻取用"], size=16, color=TEAL, bold=True)
bullet_block(s, 0.95, 4.1, 5.7, 2.2, [
    "每扩展一个节点，取其到达时刻对应的风险切片",
    "而非整条航迹统一使用出发时刻的风险场",
    "使时间维度在搜索过程中真正起作用",
], size=14)
tbox(s, 6.95, 2.0, 5.4, 0.4, ["另两种搜索范式"], size=16, color=BLUE, bold=True)
bullet_block(s, 6.95, 2.45, 5.4, 2.2, [
    "PSO：48 粒子 × 140 代，控制点参数化",
    "RRT*：8000 次采样，10 个随机种子",
    "目的：验证结论不依赖单一搜索机制",
], size=14)
tbox(s, 6.95, 4.55, 5.4, 1.8,
     ["评价指标", "累计风险 RC、单位长度风险 RC/L、路径长度 PL",
      "扩展节点数、成功率、最大转角"],
     size=14, color=GREY, spacing=1.45)

# 9 实验设置
s = content_slide("实验设置")
rows = [("研究区域", "大连三处城区，2 km × 2 km × 150 m"),
        ("时段", "04:00（低活动）/ 08:00（早高峰）/ 18:00（晚高峰）"),
        ("城市密度", "低密度 / 中密度 / 高密度"),
        ("分辨率", "2 m 体素；5×5×5 聚合为 10 m 规划栅格"),
        ("对比算法", "A*、Risk-A*、PSO、RRT*"),
        ("评价指标", "RC、RC/L、PL、扩展节点数、成功率、最大转角")]
y = 2.05
for i, (k, v) in enumerate(rows):
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.95), Inches(y), Inches(11.4), Inches(0.68))
    band.fill.solid()
    band.fill.fore_color.rgb = PALE if i % 2 == 0 else WHITE
    band.line.fill.background()
    tbox(s, 1.2, y + 0.14, 2.3, 0.42, [k], size=15, color=BLUE, bold=True)
    tbox(s, 3.5, y + 0.14, 8.6, 0.42, [v], size=14, color=GREY)
    y += 0.74

# 10 风险场
s = content_slide("结果一：风险场的时空结构")
pic(s, "figure7.png", 1.0, 2.0, w=11.3)
cap(s, 1.0, 5.95, 11.3, "三个时段的二维风险场")
tbox(s, 1.0, 6.35, 11.3, 0.6, ["04:00 整体平坦 → 08:00 出现清晰走廊 → 18:00 斑块化、高风险连片"],
     size=15, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

# 11 分量
s = content_slide("结果二：人口暴露与交通风险分量")
pic(s, "figure8.png", 0.95, 2.1, w=5.4)
cap(s, 0.95, 5.55, 5.4, "人口暴露（三维曲面）")
pic(s, "figure9.png", 7.0, 2.1, w=5.4)
cap(s, 7.0, 5.55, 5.4, "交通风险（三维曲面）")
tbox(s, 0.95, 6.0, 11.4, 0.9,
     ["人口暴露随时段整体抬升，交通风险集中在路网与商业节点，两者空间形态明显不同"],
     size=14, color=GREY, align=PP_ALIGN.CENTER)

# 12 轨迹
s = content_slide("结果三：风险感知轨迹")
pic(s, "figure10.png", 0.95, 2.0, w=5.9)
cap(s, 0.95, 5.3, 5.9, "俯视轨迹对比")
pic(s, "figure11.png", 7.1, 2.0, w=5.3)
cap(s, 7.1, 5.3, 5.3, "三维视图")
tbox(s, 0.95, 5.75, 11.4, 1.2,
     ["Risk-A* 主动绕开高风险斑块，高度剖面保持在 10–120 m，未出现大幅爬升——",
      "说明风险下降来自水平绕行，而不是靠“飞得更高”回避风险"],
     size=14, color=GREY, align=PP_ALIGN.CENTER, spacing=1.4)

# 13 累计风险
s = content_slide("结果四：累计风险显著下降")
pic(s, "figure12.png", 0.95, 2.0, w=7.1)
cap(s, 0.95, 5.45, 7.1, "沿轨迹的累计风险曲线")
tbox(s, 8.35, 2.0, 4.2, 0.35, ["时段　　A*　　Risk-A*　　降幅"], size=12, color=BLUE, bold=True)
for i, row in enumerate([("04:00", "127.5", "39.7", "−68.9%"),
                         ("08:00", "230.4", "155.3", "−32.6%"),
                         ("18:00", "221.2", "142.4", "−35.6%")]):
    tbox(s, 8.35, 2.4 + i * 0.5, 4.3, 0.4, ["%s　　%s　　%s　　%s" % row], size=13, color=GREY)
bx = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.3), Inches(4.05), Inches(4.2), Inches(1.9))
bx.fill.solid()
bx.fill.fore_color.rgb = PALE
bx.line.color.rgb = TEAL_L
bx.shadow.inherit = False
tbox(s, 8.5, 4.2, 3.9, 1.7, ["降幅 32.6%–68.9%", "路径长度增幅 ≤ 4.1%", "低谷时段收益最大"],
     size=14, color=TEAL, bold=True, spacing=1.45)

# 14 密度
s = content_slide("结果五：密度越高，收益越大")
pic(s, "figure13.png", 0.95, 2.05, w=7.3)
cap(s, 0.95, 5.6, 7.3, "三种城市密度下的规划轨迹")
tbox(s, 8.55, 2.0, 4.0, 0.35, ["密度　　A*　　Risk-A*　　降幅"], size=12, color=BLUE, bold=True)
for i, row in enumerate([("低密度", "221.2", "142.4", "−35.6%"),
                         ("中密度", "221.5", "126.7", "−42.8%"),
                         ("高密度", "516.9", "203.4", "−60.7%")]):
    tbox(s, 8.55, 2.4 + i * 0.5, 4.2, 0.4, ["%s　　%s　　%s　　%s" % row], size=12, color=GREY)
tbox(s, 8.55, 4.05, 4.2, 2.4,
     ["低密度区风险走廊宽，绕行空间大但收益有限",
      "高密度区斑块密集，绕行代价高、收益也最高",
      "目标越密集，风险感知规划越有价值"],
     size=13, color=GREY, spacing=1.45)

# 15 消融
s = content_slide("结果六：消融实验——哪类风险在起作用")
pic(s, "figure14.png", 0.9, 2.05, w=6.2)
cap(s, 0.9, 5.6, 6.2, "不同风险配置下的风险场与轨迹")
rows = [("配置", "RC", "飞越暴露"), ("仅静态", "64.6", "0.3"),
        ("+ 人口", "166.5", "97.0"), ("完整（含交通）", "221.2", "142.4")]
y = 2.1
for i, row in enumerate(rows):
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.35), Inches(y), Inches(5.0), Inches(0.58))
    band.fill.solid()
    band.fill.fore_color.rgb = BLUE if i == 0 else (PALE if i % 2 else WHITE)
    band.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
    band.shadow.inherit = False
    for j, cell in enumerate(row):
        tbox(s, 7.5 + j * 1.65, y + 0.12, 1.65, 0.35, [cell], size=12,
             color=WHITE if i == 0 else GREY, bold=(i == 0))
    y += 0.60
tbox(s, 7.35, 4.65, 5.1, 2.0,
     ["静态项只解释 29% 的累计风险", "人口与交通合计贡献 99.4%", "只做建筑避障，几乎没有规避地面风险"],
     size=14, color=TEAL, bold=True, spacing=1.5)

# 16 时间
s = content_slide("结果七：时间维度的作用在哪里")
tbox(s, 0.95, 2.0, 5.8, 0.4, ["同一任务，仅改变出发时刻"], size=16, color=BLUE, bold=True)
b1 = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.1), Inches(2.55), Inches(3.8), Inches(0.75))
b1.fill.solid(); b1.fill.fore_color.rgb = RGBColor(0xC8, 0xD8, 0xD2); b1.line.fill.background()
tbox(s, 1.2, 2.7, 3.5, 0.45, ["08:00 出发　RC = 203.6"], size=12, color=WHITE, bold=True)
b2 = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.1), Inches(3.45), Inches(2.55), Inches(0.75))
b2.fill.solid(); b2.fill.fore_color.rgb = TEAL; b2.line.fill.background()
tbox(s, 1.2, 3.6, 2.3, 0.45, ["06:00 出发　140.2"], size=12, color=WHITE, bold=True)
tbox(s, 1.1, 4.4, 5.0, 0.5, ["→ 降幅 31.1%"], size=22, color=TEAL, bold=True)
tbox(s, 7.0, 2.0, 5.4, 0.4, ["同一航程内（按到达时刻取风险）"], size=16, color=BLUE, bold=True)
bullet_block(s, 7.0, 2.55, 5.4, 2.2, [
    "速度 5–20 m/s 变化，风险仅变 0.4%–1.7%",
    "短程任务中航程内的风险漂移可忽略",
], size=14)
tbox(s, 7.0, 3.65, 5.4, 0.4, ["风险变化仅 0.92%"], size=20, color=TEAL, bold=True)
tbox(s, 0.95, 5.45, 11.4, 1.0,
     ["管理含义：城市低空风险管控的关键杠杆是时段调度，而非单纯的飞行速度约束"],
     size=16, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

# 17 稳健性
s = content_slide("稳健性：参数扰动与随机性")
pic(s, "figure15.png", 0.95, 2.1, w=5.9)
cap(s, 0.95, 5.85, 5.9, "参数扰动下的风险降幅分布（60 组）")
bullet_block(s, 7.15, 2.1, 5.3, 4.2, [
    "人口模型参数 ±20% 扰动：结论方向不变",
    "权重 w=1.25：扩展节点由 17.7 万降至约 170",
    "60 组蒙特卡洛：降幅 26.7%–35.4%，中位 31.4%",
    "60/60 组试验中 Risk-A* 均优于 A*",
], size=15)

# 18 讨论与结论
s = content_slide("讨论与结论")
tbox(s, 0.95, 2.0, 5.5, 0.4, ["语义推断可靠性"], size=16, color=BLUE, bold=True)
bullet_block(s, 0.95, 2.45, 5.5, 2.0, [
    "抽检 50 栋，46 栋正确（92%）",
    "4 处误判均为混合用地",
    "误判面积 2109 m²，占 0.35%",
], size=14)
tbox(s, 7.0, 2.0, 5.4, 0.4, ["三条结论"], size=16, color=TEAL, bold=True)
bullet_block(s, 7.0, 2.45, 5.4, 3.6, [
    "四维风险场能刻画人口与交通的日内迁移",
    "累计风险降 32.6%–68.9%，暴露降 20.0%，路径仅增 ≤4.1%",
    "时间维度作用在出发时刻（31.1%），而非航程内漂移（0.92%）",
], size=14)
tbox(s, 0.95, 6.2, 11.4, 0.6, ["下一步：多城市多时段验证；引入风场、动态障碍与多机协同"],
     size=14, color=GREY, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- closing text
for sh in prs.slides[2].shapes:
    if sh.has_text_frame and sh.text_frame.text.strip().startswith("大连海事大学硕士"):
        sh.text_frame.paragraphs[0].runs[0].text = "大连海事大学  学术交流报告"

# ---------------------------------------------------------------- move closing to the end
sldIdLst.remove(closing_id)
sldIdLst.append(closing_id)

prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides))
