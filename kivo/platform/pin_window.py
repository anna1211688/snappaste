# -*- coding: utf-8 -*-
"""贴图窗口: 无边框置顶，显示图片，可拖动/滚轮缩放/右键菜单/双击关闭。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QLabel, QMenu, QApplication, QVBoxLayout,
)

from ..ui.theme import Theme
from ..core.i18n import tr

MIN_SCALE = 0.1
MAX_SCALE = 4.0


class PinWindow(QWidget):
    def __init__(self, theme: Theme, pixmap: QPixmap, on_close=None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._orig = pixmap
        self._scale = 1.0
        self.on_close = on_close
        self._drag_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                            Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(1, 1, 1, 1)
        self.image_label = QLabel()
        self.image_label.setObjectName("pinImage")
        lay.addWidget(self.image_label)
        self._render()

    def _render(self):
        w = max(20, int(self._orig.width() * self._scale))
        h = max(20, int(self._orig.height() * self._scale))
        self.image_label.setPixmap(
            self._orig.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.adjustSize()

    def scale_at(self, factor):
        self._scale = min(MAX_SCALE, max(MIN_SCALE, self._scale * factor))
        self._render()

    def set_opacity(self, pct):
        self.setWindowOpacity(pct)

    def rotate(self):
        from PySide6.QtGui import QTransform
        self._orig = self._orig.transformed(QTransform().rotate(-90))
        self._render()

    def copy_to_clipboard(self):
        QApplication.clipboard().setPixmap(self._orig)

    # ---------- 鼠标 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def wheelEvent(self, e):
        factor = 1.1 if e.angleDelta().y() > 0 else 0.9
        self.scale_at(factor)

    def mouseDoubleClickEvent(self, _e):
        self.close_pin()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.addAction(tr("pin.rotate"), self.rotate)
        alpha = menu.addMenu(tr("pin.opacity"))
        for pct in (100, 80, 60, 40):
            alpha.addAction(f"{pct}%", lambda p=pct / 100: self.set_opacity(p))
        menu.addAction(tr("pin.copy_img"), self.copy_to_clipboard)
        menu.addSeparator()
        menu.addAction(tr("pin.close"), self.close_pin)
        menu.exec(e.globalPos())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_pin()
        else:
            super().keyPressEvent(e)

    def close_pin(self):
        self.hide()
        if self.on_close:
            self.on_close(self)
