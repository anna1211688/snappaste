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
from ...core.i18n import tr


class WinmanPanel(QWidget):
    def __init__(self, theme: Theme, wm: WindowManager | None = None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.wm = wm or WindowManager()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(14)

        title = QLabel(tr("winman.title"))
        title.setObjectName("hero")
        outer.addWidget(title)

        hint = QLabel(tr("winman.hint"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        if not IS_WINDOWS:
            warn = QLabel(tr("winman.win_only"))
            warn.setObjectName("mutedLabel")
            outer.addWidget(warn)

        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=16, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        groups = [
            [("winman.topmost", lambda h: self.wm.toggle_topmost(h)),
             ("winman.op80", lambda h: self.wm.set_opacity(h, 204)),
             ("winman.op60", lambda h: self.wm.set_opacity(h, 153)),
             ("winman.opaque", lambda h: self.wm.set_opacity(h, 255))],
            [("winman.left", lambda h: self.wm.snap(h, "left")),
             ("winman.right", lambda h: self.wm.snap(h, "right")),
             ("winman.center", lambda h: self.wm.snap(h, "center"))],
        ]
        for group in groups:
            row = QHBoxLayout()
            for text, fn in group:
                b = SecondaryButton(tr(text))
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
            show_toast(self, tr("winman.none"))
            return
        try:
            fn(hwnd)
        except OSError:
            show_toast(self, tr("winman.failed"))
