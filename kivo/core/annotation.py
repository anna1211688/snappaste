# -*- coding: utf-8 -*-
"""标注数据层: 标注操作构造、PIL 渲染、撤销重做栈（纯逻辑，可独立测试）。"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SHAPE_TOOLS = ("rect", "ellipse", "line", "arrow", "mosaic", "blur")
ALL_TOOLS = SHAPE_TOOLS + ("pen", "text", "seq")
PALETTE = ("#FF0000", "#FFD800", "#00B050", "#0070FF", "#000000", "#FFFFFF")
DEFAULT_COLOR = "#FF0000"
WIDTH_MIN, WIDTH_MAX = 1, 20
DEFAULT_WIDTH = 3

_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}
_FONT_PATH = None


def clamp_width(w):
    try:
        w = int(w)
    except Exception:
        return DEFAULT_WIDTH
    return max(WIDTH_MIN, min(WIDTH_MAX, w))


def load_font(size):
    global _FONT_PATH
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    if _FONT_PATH is None:
        _FONT_PATH = ""
        for path in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                     "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            if os.path.exists(path):
                _FONT_PATH = path
                break
    font = None
    if _FONT_PATH:
        try:
            font = ImageFont.truetype(_FONT_PATH, size)
        except Exception:
            font = None
    if font is None:
        font = ImageFont.load_default()
    if len(_FONT_CACHE) < 64:
        _FONT_CACHE[size] = font
    return font


def norm_box(box):
    x1, y1, x2, y2 = (int(v) for v in box)
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def make_shape_op(tool, box, color, width):
    if tool not in SHAPE_TOOLS:
        return None
    return {"type": tool, "box": norm_box(box), "color": color,
            "width": clamp_width(width)}


def make_pen_op(points, color, width):
    pts = [(int(x), int(y)) for x, y in points]
    if len(pts) < 2:
        return None
    return {"type": "pen", "points": pts, "color": color,
            "width": clamp_width(width)}


def make_text_op(at, text, color, width):
    text = str(text or "")
    if not text:
        return None
    return {"type": "text", "at": (int(at[0]), int(at[1])), "text": text,
            "color": color, "width": clamp_width(width)}


def make_seq_op(at, n, color, width):
    return {"type": "seq", "at": (int(at[0]), int(at[1])), "n": int(n),
            "color": color, "width": clamp_width(width)}


def fx_region(region, kind):
    """马赛克/模糊，强度随区域短边自适应。"""
    w, h = region.size
    if kind == "mosaic":
        block = max(16, min(40, min(w, h) // 8))
        small = region.resize((max(1, w // block), max(1, h // block)), Image.NEAREST)
        return small.resize((w, h), Image.NEAREST)
    r = max(10, min(32, min(w, h) // 8))
    return region.filter(ImageFilter.GaussianBlur(r)).filter(ImageFilter.GaussianBlur(r))


def render_ops(base, ops):
    """把操作列表画到图上，返回新图。"""
    img = base.convert("RGB").copy()
    d = ImageDraw.Draw(img)
    for op in ops:
        t, c, w = op["type"], op["color"], op["width"]
        if t == "rect":
            d.rectangle(op["box"], outline=c, width=w)
        elif t == "ellipse":
            d.ellipse(op["box"], outline=c, width=w)
        elif t == "line":
            d.line(op["box"], fill=c, width=w)
        elif t == "pen" and len(op["points"]) > 1:
            d.line(op["points"], fill=c, width=w, joint="curve")
        elif t == "arrow":
            x1, y1, x2, y2 = op["box"]
            d.line(op["box"], fill=c, width=w)
            ang = math.atan2(y2 - y1, x2 - x1)
            L = 10 + w * 2
            for da in (2.8, -2.8):
                d.line([x2, y2, x2 + L * math.cos(ang + da),
                        y2 + L * math.sin(ang + da)], fill=c, width=w)
        elif t == "text":
            d.text(op["at"], op["text"], fill=c, font=load_font(14 + w * 3))
        elif t == "seq":
            x, y = op["at"]
            r = 11 + w * 2
            n = str(op["n"])
            d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline="white", width=2)
            f = load_font(int(r * 1.15))
            try:
                bb = d.textbbox((0, 0), n, font=f)
                d.text((x - (bb[2] - bb[0]) / 2 - bb[0],
                        y - (bb[3] - bb[1]) / 2 - bb[1]), n, fill="white", font=f)
            except Exception:
                d.text((x - 4, y - 6), n, fill="white", font=f)
        elif t in ("blur", "mosaic"):
            x1, y1, x2, y2 = (int(v) for v in op["box"])
            if x2 - x1 > 4 and y2 - y1 > 4:
                region = img.crop((x1, y1, x2, y2))
                img.paste(fx_region(region, t), (x1, y1))
                d = ImageDraw.Draw(img)
    return img


class OpStack:
    """撤销/重做栈。"""

    def __init__(self):
        self.ops = []
        self.undone = []

    def add(self, op):
        if op is None:
            return False
        self.ops.append(op)
        self.undone.clear()
        return True

    def undo(self):
        if not self.ops:
            return False
        self.undone.append(self.ops.pop())
        return True

    def redo(self):
        if not self.undone:
            return False
        self.ops.append(self.undone.pop())
        return True

    def clear(self):
        self.ops.clear()
        self.undone.clear()

    def next_seq_number(self):
        return 1 + sum(1 for o in self.ops if o["type"] == "seq")
