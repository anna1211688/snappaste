# -*- coding: utf-8 -*-
"""弹窗基类与轻提示。

Dialog: 圆角无边框模态弹窗, 带标题栏/关闭按钮/阴影, 内容由子类填充。
Toast:  自动消失的轻提示。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsOpacityEffect,
)

from ..theme import add_shadow
from ..icons import icon


class Dialog(QDialog):
    """圆角无边框弹窗基类。"""

    def __init__(self, parent: QWidget, title: str = "", width: int = 440):
        super().__init__(parent)
        self.setObjectName("modalRoot")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(width)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)  # 给阴影留空间

        self.modal = QFrame()
        self.modal.setObjectName("modal")
        add_shadow(self.modal, blur=30, dy=10, alpha=55)
        outer.addWidget(self.modal)

        ml = QVBoxLayout(self.modal)
        ml.setContentsMargins(22, 18, 22, 22)
        ml.setSpacing(14)

        # 标题栏
        head = QHBoxLayout()
        head.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("title")
        head.addWidget(self.title_label)
        head.addStretch()
        close = QPushButton()
        close.setObjectName("iconBtn")
        close.setFixedSize(30, 30)
        close.setCursor(Qt.PointingHandCursor)
        close.setIcon(icon("close"))
        close.clicked.connect(self.reject)
        head.addWidget(close)
        ml.addLayout(head)

        # 内容容器 (子类用 self.body 填充)
        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        ml.addLayout(self.body)

        # 按钮区 (子类用 self.add_button 或直接操作)
        self.button_row = QHBoxLayout()
        self.button_row.addStretch()
        self.button_row.setSpacing(10)
        ml.addLayout(self.button_row)

    def add_button(self, button: QPushButton, accept: bool = False):
        self.button_row.addWidget(button)
        if accept:
            button.clicked.connect(self.accept)

    def center_on_parent(self):
        if self.parent() is None:
            return
        pr = self.parent().window().frameGeometry()
        self.move(pr.center() - self.rect().center())

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        # 淡入
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim


class Toast(QFrame):
    """居中轻提示, 自动消失。"""

    def __init__(self, parent: QWidget, text: str):
        super().__init__(parent)
        self.setObjectName("toast")
        add_shadow(self, blur=18, dy=4, alpha=60)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 10, 18, 10)
        label = QLabel(text)
        label.setObjectName("toastText")
        lay.addWidget(label)

        self._eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._eff.setOpacity(0.0)
        self.adjustSize()

    def show_center(self):
        if self.parent() is not None:
            pw = self.parent().size()
            self.move((pw.width() - self.width()) // 2,
                      int(pw.height() * 0.42))
        self.show()
        self._fade(0.0, 1.0, 150, on_done=self._wait)

    def _wait(self):
        QTimer.singleShot(1500, lambda: self._fade(1.0, 0.0, 220, on_done=self.close))

    def _fade(self, start: float, end: float, dur: int, on_done=None):
        anim = QPropertyAnimation(self._eff, b"opacity", self)
        anim.setDuration(dur)
        anim.setStartValue(start)
        anim.setEndValue(end)
        if on_done:
            anim.finished.connect(on_done)
        anim.start()
        self._anim = anim


def show_toast(parent: QWidget, text: str) -> Toast:
    t = Toast(parent, text)
    t.show_center()
    return t
