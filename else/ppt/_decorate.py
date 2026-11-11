# -*- coding: utf-8 -*-
"""Add layout structure and filler elements to the sparse slides."""
import os
import shutil

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

SRC = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版.pptx")
BAK = SRC.replace(".pptx", "_备份.pptx")
OUT = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版_美化.pptx")

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)

prs = Presentation(SRC)
BLUE = RGBColor(0x2D, 0x2D, 0xB9)
TEAL = RGBColor(0x00, 0x99, 0x77)
CARD = RGBColor(0xF4, 0xF8, 0xFA)
EDGE = RGBColor(0xD9, 0xE4, 0xEE)
GREY = RGBColor(0x44, 0x44, 0x44)
MUTED = RGBColor(0x8A, 0x94, 0xA6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

RUNNING = "面向无人机路径规划的三维城市动态风险建模方法"


def txt(slide, x, y, w, h, text, size=12, color=GREY, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return tb


def card(slide, x, y, w, h, title, body, accent=TEAL, fill=CARD):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = EDGE
    box.shadow.inherit = False
    box.adjustments[0] = 0.08
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y + 0.16), Inches(0.06), Inches(h - 0.32))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False
    txt(slide, x + 0.18, y + 0.1, w - 0.32, 0.3, title, size=12, color=accent, bold=True)
    txt(slide, x + 0.18, y + 0.4, w - 0.32, h - 0.5, body, size=11.5, color=GREY)


def kpi(slide, x, y, w, h, value, label, color=TEAL):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = CARD
    box.line.color.rgb = EDGE
    box.shadow.inherit = False
    box.adjustments[0] = 0.12
    txt(slide, x, y + 0.08, w, 0.45, value, size=22, color=color, bold=True, align=PP_ALIGN.CENTER)
    txt(slide, x, y + 0.55, w, 0.3, label, size=10, color=MUTED, align=PP_ALIGN.CENTER)


def footer(slide, num):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.0), Inches(7.14), prs.slide_width, Inches(0.36))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(0xF6, 0xF8, 0xFA)
    line.line.fill.background()
    line.shadow.inherit = False
    txt(slide, 0.95, 7.19, 9.0, 0.26, RUNNING, size=8.5, color=MUTED)
    txt(slide, 11.4, 7.19, 1.3, 0.26, "%02d" % num, size=9, color=MUTED, bold=True, align=PP_ALIGN.RIGHT)


def divider(slide):
    ln = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.95), Inches(1.94), Inches(11.43), Inches(0.02))
    ln.fill.solid()
    ln.fill.fore_color.rgb = EDGE
    ln.line.fill.background()
    ln.shadow.inherit = False


def spine(slide):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.62), Inches(2.05), Inches(0.05), Inches(4.85))
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()
    bar.shadow.inherit = False


def vbars(slide, x, y, w, h, items, maxv=None):
    """Vertical bar chart drawn with shapes."""
    maxv = maxv or max(v for _, v in items)
    n = len(items)
    gap = w / (n * 1.9)
    bw = (w - gap * (n + 1)) / n
    for i, (label, v) in enumerate(items):
        bh = max(0.12, (h - 0.55) * v / maxv)
        bx = x + gap + i * (bw + gap)
        by = y + (h - 0.55) - bh
        b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(bx), Inches(by), Inches(bw), Inches(bh))
        b.fill.solid()
        b.fill.fore_color.rgb = TEAL
        b.line.fill.background()
        b.shadow.inherit = False
        b.adjustments[0] = 0.1
        txt(slide, bx - 0.1, by - 0.3, bw + 0.2, 0.25, "%.1f" % v, size=10, color=TEAL,
            bold=True, align=PP_ALIGN.CENTER)
        txt(slide, bx - 0.15, y + h - 0.5, bw + 0.3, 0.25, label, size=9.5, color=MUTED, align=PP_ALIGN.CENTER)


slides = list(prs.slides)

for idx in range(2, 20):          # slides 3..20
    slider = slides[idx]
    divider(slider)
    spine(slider)

# ---- 3 背景
s = slides[2]
card(s, 0.95, 5.65, 6.05, 1.25, "核心矛盾",
     "风险随人口与交通在一天内流动，而现有规划却按一张静态风险图来做权衡。")

# ---- 6 框架：给输入/输出加面板
s = slides[5]
for x in (0.78, 6.45):
    p = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(3.92), Inches(5.75), Inches(2.15))
    p.fill.solid()
    p.fill.fore_color.rgb = CARD
    p.line.color.rgb = EDGE
    p.shadow.inherit = False
    p.adjustments[0] = 0.08
    sp = p._element
    spTree = sp.getparent()
    spTree.remove(sp)
    spTree.insert(2, sp)

# ---- 7 语义：右下补“输出”
s = slides[6]
card(s, 0.95, 5.55, 5.25, 1.30, "输出",
     "商业 / 工业 / 公共 / 住宅 / 其他 五类地类，\n为人口分配与风险计算提供语义锚点。", accent=BLUE)

# ---- 8 人口：右侧补 η(t) 小表
s = slides[7]
card(s, 7.15, 4.20, 5.4, 2.15, "时段系数 η(t)",
     "04:00　0.35　（夜间，活动低）\n08:00　1.00　（早高峰，基准）\n18:00　0.85　（晚高峰，略低）", accent=BLUE)

# ---- 9 风险：左下补权重条形
s = slides[8]
txt(s, 0.95, 5.25, 4.9, 0.3, "融合权重", size=12, color=BLUE, bold=True)
vbars(s, 0.95, 5.6, 4.8, 1.25, [("致死", 0.4), ("财产", 0.3), ("噪声", 0.2), ("其他", 0.1)])

# ---- 10 规划：底部一句话
s = slides[9]
card(s, 0.95, 5.75, 5.7, 0.95, "关键区别",
     "把风险的时间维度放进搜索过程，而不是等到事后评价再回头补算。")

# ---- 13 人口/交通：两处缺口补说明卡
s = slides[12]
card(s, 0.95, 4.15, 5.4, 1.15, "人口暴露",
     "随时段整体抬升，08:00 达峰值；空间上与住宅、公共设施重合。")
card(s, 7.0, 4.15, 5.4, 1.15, "交通风险",
     "集中在路网与商业节点，18:00 峰值范围最大。", accent=BLUE)

# ---- 14 轨迹：两处缺口补说明卡
s = slides[13]
card(s, 0.95, 4.10, 5.9, 1.05, "俯视",
     "Risk-A* 绕开高风险斑块，路径更长但穿过低风险区。")
card(s, 7.1, 4.10, 5.3, 1.05, "侧视",
     "高度维持在 10–120 m，未靠爬升回避风险。", accent=BLUE)

# ---- 15 累计风险：图下三个 KPI
s = slides[14]
for i, (v, l) in enumerate([("−68.9%", "04:00"), ("−32.6%", "08:00"), ("−35.6%", "18:00")]):
    kpi(s, 0.95 + i * 2.4, 4.45, 2.2, 0.95, v, l)

# ---- 16 密度：图下三个 KPI
s = slides[15]
for i, (v, l) in enumerate([("−35.6%", "低密度"), ("−42.8%", "中密度"), ("−60.7%", "高密度")]):
    kpi(s, 0.95 + i * 2.5, 4.55, 2.3, 0.95, v, l)

# ---- 17 消融：图下柱状
s = slides[16]
txt(s, 0.9, 3.98, 6.2, 0.3, "累计风险 RC", size=12, color=BLUE, bold=True)
vbars(s, 0.9, 4.28, 6.2, 1.15, [("仅静态", 64.6), ("+人口", 166.5), ("完整", 221.2)], maxv=221.2)

# ---- 18 时间：右侧补对比说明
s = slides[17]
card(s, 7.0, 4.25, 5.4, 0.95, "量级对比",
     "出发时刻的影响 31.1%，是航程内漂移 0.92% 的 30 余倍。")

# ---- 20 讨论：左下补适用边界
s = slides[19]
card(s, 0.95, 4.75, 5.5, 1.25, "适用边界",
     "人口为公开栅格；时段曲线可替换为实测客流，方法不变。", accent=BLUE)

for i in range(2, 20):
    footer(slides[i], i + 1)

prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides))
