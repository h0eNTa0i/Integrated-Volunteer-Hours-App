# -*- coding: utf-8 -*-
"""轻量级示意图绘制工具（PIL）：框、箭头、泳道、表格，用于软件工程报告插图。"""
from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"

BLUE = "#3B82F6"
PURPLE = "#8B5CF6"
DARK = "#1F2937"
GRAY = "#6B7280"
LINE = "#9CA3AF"
LIGHT_BLUE = "#EFF6FF"
LIGHT_PURPLE = "#F5F3FF"
LIGHT_GRAY = "#F9FAFB"
WHITE = "#FFFFFF"
GREEN = "#10B981"
ORANGE = "#F59E0B"


def f(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except Exception:
        return ImageFont.truetype(FONT, size)


class Canvas:
    def __init__(self, w, h, bg=WHITE, scale=2):
        self.scale = scale
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * scale, h * scale), bg)
        self.d = ImageDraw.Draw(self.img)

    def _box(self, b):
        return tuple(int(v * self.scale) for v in b)

    def text(self, xy, txt, size=20, color=DARK, bold=False, anchor=None):
        self.d.text(self._box(xy), txt, font=f(size * self.scale, bold), fill=color, anchor=anchor)

    def text_center(self, cx, cy, txt, size=20, color=DARK, bold=False):
        self.text((cx, cy), txt, size, color, bold, anchor="mm")

    def rect(self, box, fill=WHITE, outline=LINE, width=2, radius=10):
        self.d.rounded_rectangle(self._box(box), radius=radius * self.scale,
                                 fill=fill, outline=outline, width=width * self.scale)

    def line(self, points, fill=LINE, width=2):
        if len(points) == 4 and isinstance(points[0], (int, float)):
            points = [(points[0], points[1]), (points[2], points[3])]
        self.d.line([self._box(p) for p in points], fill=fill, width=width * self.scale, joint="curve")

    def arrow(self, p1, p2, fill=BLUE, width=2, head=9):
        import math
        self.line([p1, p2], fill=fill, width=width)
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        a = (p2[0] - head * math.cos(ang - 0.5), p2[1] - head * math.sin(ang - 0.5))
        b = (p2[0] - head * math.cos(ang + 0.5), p2[1] - head * math.sin(ang + 0.5))
        self.d.polygon([self._box(p2), self._box(a), self._box(b)], fill=fill)

    def node(self, box, title, sub=None, fill=LIGHT_BLUE, outline=BLUE, tcolor=DARK, size=18, subsize=13):
        self.rect(box, fill=fill, outline=outline, width=2, radius=9)
        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2
        if sub:
            lines = str(sub).split("\n")
            total = size + len(lines) * (subsize + 7) + 6
            ty = (y1 + y2) / 2 - total / 2 + size / 2 + 2
            self.text_center(cx, ty, title, size, tcolor, True)
            sy = ty + size / 2 + 8
            for ln in lines:
                self.text_center(cx, sy + subsize / 2, ln, subsize, GRAY, False)
                sy += subsize + 7
        else:
            self.text_center(cx, (y1 + y2) / 2, title, size, tcolor, True)

    def save(self, path):
        self.img.save(path)


def wrap(text, n):
    """按字符数粗略折行"""
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= n:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out
