# -*- coding: utf-8 -*-
"""Slide 5: four contribution rows, each with a figure thumbnail on the right."""
import os

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

SRC = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版_美化.pptx")
OUT = str(config.PROJECT_DIR / "ppt" / "论文1_三维动态风险建模_模板版_美化2.pptx")
FIG = str(config.PROJECT_DIR / "中文版" / "figs")

BLUE = RGBColor(0x2D, 0x2D, 0xB9)
TEAL = RGBColor(0x00, 0x99, 0x77)
CARD = RGBColor(0xF4, 0xF8, 0xFA)
EDGE = RGBColor(0xD9, 0xE4, 0xEE)
GREY = RGBColor(0x44, 0x44, 0x44)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation(SRC)
s = prs.slides[4]


def txt(x, y, w, h, text, size=12, color=GREY, bold=False):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.15
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color


# clear the old list, keep title / divider / spine / footer
for sh in list(s.shapes):
    top = (sh.top or 0) / 914400
    h = (sh.height or 0) / 914400
    w = (sh.width or 0) / 914400
    left = (sh.left or 0) / 914400
    if not (1.95 <= top <= 6.6):
        continue
    if h < 0.05:                    # divider
        continue
    if w < 0.06 and left < 0.7:     # spine
        continue
    sh._element.getparent().remove(sh._element)

rows = [
    ("①", "四维风险场", "总量守恒的时空风险表达：三维空间叠加时间维度，风险随人口与交通迁移。", "figure7.png", TEAL),
    ("②", "三类风险融合", "致死、财产与噪声统一到归一化代价场，权重 0.4 / 0.3 / 0.2 / 0.1。", "figure2.png", BLUE),
    ("③", "到达时刻取风险", "风险按航路点到达时刻取用，时间维度进入搜索而非事后评价。", "figure12.png", TEAL),
    ("④", "控制变量对比", "A* 与 Risk-A* 同码不同代价，PSO 与 RRT* 覆盖其他搜索范式。", "figure13.png", BLUE),
]

X0, CW, CH = 0.95, 11.40, 1.02
ys = [2.05, 3.15, 4.25, 5.35]

for (badge, title, body, img, accent), y in zip(rows, ys):
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(X0), Inches(y), Inches(CW), Inches(CH))
    box.fill.solid()
    box.fill.fore_color.rgb = CARD
    box.line.color.rgb = EDGE
    box.shadow.inherit = False
    box.adjustments[0] = 0.10

    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(X0), Inches(y + 0.14), Inches(0.055), Inches(CH - 0.28))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False

    bob = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(X0 + 0.16), Inches(y + 0.14), Inches(0.38), Inches(0.38))
    bob.fill.solid()
    bob.fill.fore_color.rgb = accent
    bob.line.fill.background()
    bob.shadow.inherit = False
    p = bob.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = badge
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = WHITE

    txt(X0 + 0.66, y + 0.13, 2.3, 0.36, title, size=14, color=BLUE, bold=True)
    txt(X0 + 0.68, y + 0.50, 6.1, 0.5, body, size=10.5, color=GREY)

    path = os.path.join(FIG, img)
    iw, ih = Image.open(path).size
    disp_w = 2.55
    disp_h = disp_w * ih / iw
    if disp_h > CH - 0.16:
        disp_h = CH - 0.16
        disp_w = disp_h * iw / ih
    s.shapes.add_picture(path, Inches(X0 + CW - disp_w - 0.16), Inches(y + (CH - disp_h) / 2),
                         width=Inches(disp_w), height=Inches(disp_h))

prs.save(OUT)
print("saved:", OUT)
