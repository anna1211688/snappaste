# -*- coding: utf-8 -*-
"""番茄钟面板: 模式标签 + 大计时 + 控制按钮 + 时长设置。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton
from ..dialogs.base import show_toast
from ...core.pomo_store import PomoStore


class PomoPanel(QWidget):
    def __init__(self, theme: Theme, store: PomoStore | None = None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = store or PomoStore()
        self.store.on_advance = self._on_advance

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.addStretch()

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(self._card())
        wrap.addStretch()
        outer.addLayout(wrap)
        outer.addStretch()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self._sync()

    def _card(self):
        card = QFrame()
        card.setObjectName("pomoCard")
        card.setFixedWidth(420)
        add_shadow(card, blur=24, alpha=28)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(30, 28, 30, 26)
        lay.setSpacing(12)

        self.mode_lab = QLabel("专注中")
        self.mode_lab.setObjectName("pomoMode")
        self.mode_lab.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.mode_lab)

        self.time_lab = QLabel("25:00")
        self.time_lab.setObjectName("pomoTime")
        self.time_lab.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.time_lab)

        brow = QHBoxLayout()
        self.main_btn = PrimaryButton("开始")
        self.main_btn.clicked.connect(self._toggle)
        reset = SecondaryButton("重置")
        reset.clicked.connect(self._reset)
        skip = SecondaryButton("跳过")
        skip.clicked.connect(self._advance)
        brow.addWidget(self.main_btn)
        brow.addWidget(reset)
        brow.addWidget(skip)
        lay.addLayout(brow)

        srow = QHBoxLayout()
        srow.addWidget(QLabel("专注(分钟)"))
        self.focus_edit = QLineEdit(str(self.store.focus_min))
        self.focus_edit.setFixedWidth(60)
        srow.addWidget(self.focus_edit)
        srow.addWidget(QLabel("休息(分钟)"))
        self.break_edit = QLineEdit(str(self.store.break_min))
        self.break_edit.setFixedWidth(60)
        srow.addWidget(self.break_edit)
        apply = SecondaryButton("应用")
        apply.clicked.connect(self._apply)
        srow.addWidget(apply)
        lay.addLayout(srow)
        return card

    def _toggle(self):
        running = self.store.toggle()
        if running:
            self.timer.start()
        else:
            self.timer.stop()
        self._sync()

    def _tick(self):
        self.store.tick()
        self._sync()

    def _reset(self):
        self.timer.stop()
        self.store.reset()
        self._sync()

    def _advance(self):
        self.store.advance()
        self._sync()

    def _apply(self):
        try:
            f = int(self.focus_edit.text())
            b = int(self.break_edit.text())
        except ValueError:
            show_toast(self, "请输入有效分钟数")
            return
        if not self.store.apply_settings(f, b):
            show_toast(self, "请输入有效分钟数")
            return
        show_toast(self, "已应用")
        self._sync()

    def _on_advance(self, mode):
        show_toast(self, "专注中" if mode == "focus" else "休息中")

    def _sync(self):
        self.time_lab.setText(self.store.display())
        self.mode_lab.setText("专注中" if self.store.mode == "focus" else "休息中")
        self.main_btn.setText("暂停" if self.store.running else "开始")
