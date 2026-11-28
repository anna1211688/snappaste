# -*- coding: utf-8 -*-
"""窗口管理面板: 置顶/透明度/分屏按钮，作用于最近的外部前台窗口。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import SecondaryButton
from ..dialogs.base import show_toast
from ...core.winman import WindowManager, IS_WINDOWS


class WinmanPanel(QWidget):
    def __init__(self, theme: Theme, wm: WindowManager | None = None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.wm = wm or WindowManager()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(14)

        title = QLabel("窗口管理")
        title.setObjectName("hero")
        outer.addWidget(title)

        hint = QLabel("先点一下要管理的窗口（让它在前台），再回来点按钮；按钮作用于最近使用的外部窗口。")
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        if not IS_WINDOWS:
            warn = QLabel("窗口管理仅在 Windows 上可用。")
            warn.setObjectName("mutedLabel")
            outer.addWidget(warn)

        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=16, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        groups = [
            [("置顶切换", lambda h: self.wm.toggle_topmost(h)),
             ("半透明 80%", lambda h: self.wm.set_opacity(h, 204)),
             ("半透明 60%", lambda h: self.wm.set_opacity(h, 153)),
             ("恢复不透明", lambda h: self.wm.set_opacity(h, 255))],
            [("左半屏", lambda h: self.wm.snap(h, "left")),
             ("右半屏", lambda h: self.wm.snap(h, "right")),
             ("居中", lambda h: self.wm.snap(h, "center"))],
        ]
        for group in groups:
            row = QHBoxLayout()
            for text, fn in group:
                b = SecondaryButton(text)
                b.setEnabled(IS_WINDOWS)
                b.clicked.connect(lambda _=False, op=fn: self._act(op))
                row.addWidget(b)
            row.addStretch()
            lay.addLayout(row)
        outer.addWidget(card)
        outer.addStretch()

    def _act(self, fn):
        my_hwnd = int(self.window().winId())
        hwnd = self.wm.target_hwnd(foreground_is_self=(
            self.wm.foreground_hwnd() == my_hwnd))
        if not hwnd:
            show_toast(self, "没有可管理的窗口")
            return
        try:
            fn(hwnd)
        except OSError:
            show_toast(self, "操作失败")
