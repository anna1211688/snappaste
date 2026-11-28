# -*- coding: utf-8 -*-
"""KIVO 主窗口: 侧边导航 + QStackedWidget 面板切换。各面板逐步替换占位实现。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel,
)

from .theme import Theme, add_shadow
from .components import NavItem, SectionHeader
from ..core.paths import VERSION
from ..core.i18n import tr

# (key, 图标, 文案 i18n key, 分组标题 key 或 None)
NAV_DEF = [
    ("ai", "ai", "nav.ai", None),
    ("voice", "voice", "nav.voice", None),
    ("trans", "translate", "nav.trans", None),
    ("clip", "copy", "nav.clip", None),
    ("phrases", "phrases", "nav.phrases", None),
    ("fx", "fx", "nav.fx", "group.tools"),
    ("clock", "clock", "nav.clock", "group.tools"),
    ("calc", "calc", "nav.calc", "group.tools"),
    ("dl", "download", "nav.dl", "group.tools"),
    ("dev", "star", "nav.dev", "group.tools"),
    ("pomo", "clock", "nav.pomo", "group.tools"),
    ("winman", "gear", "nav.winman", "group.tools"),
    ("batch", "browser", "nav.batch", "group.tools"),
]


class PlaceholderPane(QWidget):
    """面板占位: 显示名称, 后续逐个替换为真实面板。"""

    def __init__(self, label_key: str, theme: Theme):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 26, 28, 26)
        title = QLabel(tr(label_key))
        title.setObjectName("title")
        hint = QLabel(tr("main.placeholder_hint"))
        hint.setObjectName("mutedLabel")
        cl.addWidget(title)
        cl.addWidget(hint)
        cl.addStretch()
        outer.addWidget(card)


class MainWindow(QWidget):
    def __init__(self, theme: Theme, services=None):
        super().__init__()
        self.theme = theme
        self.services = services or {}
        self.setObjectName("root")
        self.setWindowTitle(tr("app.title"))
        self.resize(1200, 800)
        self._nav_items = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        root.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        self._panes = {}
        for key, _ic, label, _grp in NAV_DEF:
            pane = self._make_pane(key, label)
            self._panes[key] = pane
            self.stack.addWidget(pane)
        root.addWidget(self.stack, 1)

        # 默认显示剪贴板 (与 Tkinter 版本一致)
        self.select("clip")

    # ---------- 侧边栏 ----------
    def _build_sidebar(self):
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(208)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 14, 10, 12)
        sl.setSpacing(4)

        for key, icon, label, group in NAV_DEF:
            if group:
                prev = NAV_DEF[NAV_DEF.index((key, icon, label, group)) - 1]
                if prev[3] != group:
                    head = SectionHeader(tr(group))
                    sl.addWidget(head)
            item = NavItem(key, icon, tr(label))
            item.clicked.connect(lambda _=False, k=key: self.select(k))
            self._nav_items[key] = item
            sl.addWidget(item)

        sl.addStretch()

        # 分隔线
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedHeight(1)
        sl.addWidget(line)

        settings_item = NavItem("settings", "gear", tr("common.settings"))
        settings_item.clicked.connect(lambda: self.open_settings())
        self._nav_items["settings"] = settings_item
        sl.addWidget(settings_item)

        ver = QLabel(f"v{VERSION} · © KIVO")
        ver.setObjectName("verLabel")
        sl.addWidget(ver)
        return side

    # ---------- 面板 ----------
    def _make_pane(self, key, label):
        custom = self.services.get("pane_factory")
        if custom:
            pane = custom(key)
            if pane is not None:
                return pane
        return PlaceholderPane(label, self.theme)

    def select(self, key):
        if key not in self._panes:
            return
        for k, item in self._nav_items.items():
            item.setChecked(k == key)
        self.stack.setCurrentWidget(self._panes[key])
        self._current = key

    def open_settings(self):
        for k, item in self._nav_items.items():
            item.setChecked(k == "settings")
        factory = self.services.get("settings_factory")
        if not factory:
            return
        if getattr(self, "_settings_win", None) is None:
            win = factory()
            win.setWindowTitle(tr("common.settings"))
            win.resize(720, 780)
            self._settings_win = win
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()
