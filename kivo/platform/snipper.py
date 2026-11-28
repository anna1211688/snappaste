# -*- coding: utf-8 -*-
"""截图覆盖层: 全屏半透明框选，鼠标拖拽产生选区，Esc 取消，完成回调矩形。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget

from ..ui.theme import Theme
from . import snip_geometry as sg

MASK_COLOR = QColor(0, 0, 0, 90)
BORDER_COLOR = QColor("#1673D1")


class SnipperOverlay(QWidget):
    def __init__(self, theme: Theme, on_pick, on_cancel, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.on_pick = on_pick
        self.on_cancel = on_cancel
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                            Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self._start = None
        self._end = None
        self._rect = None

    def begin(self, geometry):
        self.setGeometry(geometry)
        self._start = None; self._end = None; self._rect = None
        self.showFullScreen()
        self.raise_()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            p = e.position().toPoint()
            self._start = p; self._end = p

    def mouseMoveEvent(self, e):
        if self._start is not None:
            self._end = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self._start is None:
            return
        self._end = e.position().toPoint()
        rect = self._build_rect()
        self._start = None; self._end = None
        if rect and sg.valid_selection(rect):
            self.hide()
            self.on_pick(rect)
        else:
            self._rect = None; self.update()

    def _build_rect(self):
        if self._start is None or self._end is None:
            return None
        l, t, r, b = sg.normalize_rect(
            self._start.x(), self._start.y(), self._end.x(), self._end.y())
        rect = sg.clamp_rect((l, t, r, b), self.width(), self.height())
        self._rect = rect
        return rect

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
            self.on_cancel()
        else:
            super().keyPressEvent(e)

    def paintEvent(self, _e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self._build_rect() if self._start is not None else self._rect
        painter.fillRect(self.rect(), MASK_COLOR)
        if not rect:
            return
        l, t, r, b = rect
        sel = QRect(QPoint(l, t), QPoint(r, b))
        # 选区挖空（透明），重画该区域
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(sel, Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        pen = QPen(BORDER_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(sel.adjusted(1, 1, -1, -1))
        # 尺寸标签
        w, h = sg.rect_size(rect)
        painter.setFont(self.theme.font("sm"))
        label = f"{w} × {h}"
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(sel.left(), max(0, sel.top() - 8), label)
