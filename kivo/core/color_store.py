# -*- coding: utf-8 -*-
"""取色器数据层: 颜色转换与历史管理（纯函数）。"""
from __future__ import annotations

import json
import re

COLOR_HISTORY_MAX = 24
_HEX_RE = re.compile(r"[0-9A-Fa-f]{6}")


def normalize_hex(h):
    return ("#" + (h or "").lstrip("#")).upper()


def hex_to_rgb(h):
    s = (h or "").lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if not _HEX_RE.fullmatch(s):
        return None
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        hh = ss = 0
    else:
        d = mx - mn
        ss = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            hh = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            hh = (b - r) / d + 2
        else:
            hh = (r - g) / d + 4
        hh /= 6
    return round(hh * 360), round(ss * 100), round(l * 100)


def color_formats(hexv):
    rgb = hex_to_rgb(hexv)
    if rgb is None:
        return None
    hh, ss, ll = rgb_to_hsl(*rgb)
    return {
        "hex": normalize_hex(hexv),
        "rgb": f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
        "hsl": f"hsl({hh}, {ss}%, {ll}%)",
    }


def parse_history(raw):
    try:
        data = json.loads(raw) if raw else []
        return [normalize_hex(h) for h in data if hex_to_rgb(h)][:COLOR_HISTORY_MAX]
    except (ValueError, TypeError):
        return []


def add_to_history(history, hexv):
    hexv = normalize_hex(hexv)
    if hex_to_rgb(hexv) is None:
        return history
    hist = [x for x in history if x != hexv]
    hist.insert(0, hexv)
    return hist[:COLOR_HISTORY_MAX]
