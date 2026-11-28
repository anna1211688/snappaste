# -*- coding: utf-8 -*-
"""KIVO 图标模块: 统一线性符号图标, 经 QSvgRenderer 矢量渲染, 支持任意尺寸与着色。"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import Qt, QByteArray, QRect, QPoint
from PySide6.QtGui import QIcon, QIconEngine, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from .icon_paths import ICON_PATHS

# 未选中/默认态使用中性冷灰, 久看不刺眼
DEFAULT_COLOR = "#5B6B7E"
_STROKE_WIDTH = 2
_RAW_SIZE = 32

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="{color}" '
    'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
    '{body}</svg>'
)

# 工具 (主色, 浅底) 配色, 用于 IconBadge 等彩色图标底
_TOOL_TINTS = {
    "copy": ("#1D7FE0", "#DCEEFF"),
    "phrases": ("#DE8A00", "#FDEEC9"),
    "translate": ("#1F9D66", "#D8F3E3"),
    "ai": ("#7C5CFC", "#E7E1FF"),
    "fx": ("#0CA6A0", "#D2F1EF"),
    "clock": ("#5B6EE1", "#E0E4FC"),
    "calc": ("#EE5B7F", "#FDE0E8"),
    "download": ("#F06423", "#FEE3D3"),
    "gear": ("#5B7A99", "#E2EBF3"),
    "star": ("#E8A13A", "#FCEFD2"),
    "voice": ("#D9446E", "#FCE0E8"),
    "browser": ("#7A6CF0", "#E8E5FF"),
    "project": ("#3E86D8", "#DFECFB"),
}


def has_icon(name: str) -> bool:
    return name in ICON_PATHS


def _svg_bytes(name: str, color: str) -> QByteArray:
    body = ICON_PATHS[name]
    svg = _SVG_TEMPLATE.format(color=color, width=_STROKE_WIDTH, body=body)
    return QByteArray(svg.encode("utf-8"))


class _SvgIconEngine(QIconEngine):
    """按需以矢量方式渲染 SVG 图标, 任意尺寸/设备像素比都清晰。"""

    def __init__(self, name: str, color: str):
        super().__init__()
        self._name = name
        self._color = color
        self._renderer = QSvgRenderer(_svg_bytes(name, color))

    def paint(self, painter, rect, mode, state):
        painter.save()
        if mode == QIcon.Disabled:
            painter.setOpacity(0.4)
        self._renderer.render(painter, rect)
        painter.restore()

    def clone(self):
        return _SvgIconEngine(self._name, self._color)

    def pixmap(self, size, mode, state):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        self.paint(p, QRect(QPoint(0, 0), size), mode, state)
        p.end()
        return pm


def _raw_pixmap(name: str, color: str = DEFAULT_COLOR,
                size: int = _RAW_SIZE) -> QPixmap:
    renderer = QSvgRenderer(_svg_bytes(name, color))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    renderer.render(p, QRect(0, 0, size, size))
    p.end()
    return pm


@lru_cache(maxsize=None)
def icon(name: str) -> QIcon:
    if not has_icon(name):
        raise KeyError(f"未知图标: {name}")
    return QIcon(_SvgIconEngine(name, DEFAULT_COLOR))


@lru_cache(maxsize=None)
def tinted_icon(name: str, color: str) -> QIcon:
    """返回指定颜色的图标 (用于选中态/深色背景)。"""
    if not has_icon(name):
        raise KeyError(f"未知图标: {name}")
    return QIcon(_SvgIconEngine(name, color))


def tool_colors(name: str):
    """返回 (主色, 浅底) 工具配色。"""
    return _TOOL_TINTS.get(name, ("#007AFF", "#E9F2FF"))


def load_tray_icon():
    """托盘图标 (PIL 图, pystray 需要): 从 KIVO.ico 取 64px; 失败返回 None。"""
    import os
    ico = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "KIVO.ico")
    try:
        from PIL import Image
        return Image.open(ico).convert("RGBA").resize((64, 64))
    except Exception:
        return None
