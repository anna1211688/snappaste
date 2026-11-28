# -*- coding: utf-8 -*-
"""截图框选几何纯逻辑: 选区归一化、边界裁剪、窗口拾取。"""
from __future__ import annotations

MIN_SELECT = 3  # 小于该像素视为误点，不形成选区


def normalize_rect(x1, y1, x2, y2):
    """任意两个对角点 -> 标准化 (left, top, right, bottom)，容忍反向拖拽。"""
    left, right = sorted((int(x1), int(x2)))
    top, bottom = sorted((int(y1), int(y2)))
    return (left, top, right, bottom)


def clamp_rect(rect, width, height):
    """把矩形裁剪到图像 [0,width]×[0,height] 内。"""
    left, top, right, bottom = rect
    left = max(0, min(left, width))
    right = max(0, min(right, width))
    top = max(0, min(top, height))
    bottom = max(0, min(bottom, height))
    return (left, top, right, bottom)


def rect_size(rect):
    left, top, right, bottom = rect
    return (right - left, bottom - top)


def valid_selection(rect):
    w, h = rect_size(rect)
    return w >= MIN_SELECT and h >= MIN_SELECT


def pick_window(x, y, rects):
    """返回包含 (x,y) 的最小矩形（面积最小者近似最上层），无则 None。"""
    hits = [r for r in rects
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]
            and r[2] > r[0] and r[3] > r[1]]
    if not hits:
        return None
    return min(hits, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
