# -*- coding: utf-8 -*-
"""屏幕标尺: 置顶无边框半透明窗，QPainter 自绘像素刻度，可拖动/换向/调长度。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QWidget

THICK = 34
MIN_LEN, MAX_LEN, STEP = 100, 2000, 50
BG = QColor(255, 243, 196, 210)
INK = QColor(91, 74, 0)
EDGE = QColor(201, 162, 39)


class RulerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                            Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.vertical = False
        self.length = 600
        self._drag = None
        self._apply_geometry()
        self.move(120, 120)

    def _apply_geometry(self):
        if self.vertical:
            self.setFixedSize(THICK, self.length)
        else:
            self.setFixedSize(self.length, THICK)

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(BG)
        p.setPen(QPen(EDGE, 1))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)

        p.setPen(INK)
        p.setFont(QFont("Consolas", 8))
        for i in range(0, self.length + 1, 10):
            major = i % 100 == 0
            mid = i % 50 == 0
            tick = THICK - 4 if major else (THICK - 10 if mid else THICK - 16)
            if self.vertical:
                p.drawLine(0, i, tick, i)
                if major:
                    p.save()
                    p.translate(THICK - 4, i + 2)
                    p.rotate(90)
                    p.drawText(0, 0, str(i))
                    p.restore()
            else:
                p.drawLine(i, 0, i, tick)
                if major:
                    p.drawText(i + 2, THICK - 6, str(i))

        # 关闭 / 换向标记
        p.setPen(QColor(176, 0, 32))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        if self.vertical:
            p.drawText(8, 16, "×")
            p.setPen(INK); p.setFont(QFont("Segoe UI", 10))
            p.drawText(8, 32, "⇄")
        else:
            p.drawText(6, 22, "×")
            p.setPen(INK); p.setFont(QFont("Segoe UI", 10))
            p.drawText(24, 22, "⇄")

    # ---------- 鼠标 ----------
    def mousePressEvent(self, event):
        self._drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self.move(event.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, event):
        x, y = event.position().x(), event.position().y()
        if x <= 18 and y <= 18:
            self.close(); return
        if ((not self.vertical and 18 < x <= 34 and y <= 20) or
                (self.vertical and x <= 20 and 18 < y <= 34)):
            self._toggle_orientation()

    def _toggle_orientation(self):
        self.vertical = not self.vertical
        self._apply_geometry()
        self.update()

    # ---------- 键盘 ----------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self._set_length(self.length + STEP)
        elif event.key() == Qt.Key_Minus:
            self._set_length(self.length - STEP)
        else:
            super().keyPressEvent(event)

    def _set_length(self, value):
        self.length = max(MIN_LEN, min(MAX_LEN, value))
        self._apply_geometry()
        self.update()
