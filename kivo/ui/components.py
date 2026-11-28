# -*- coding: utf-8 -*-
"""KIVO 通用组件库。所有组件用 objectName 挂应用级 QSS, 不内联样式。"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QLineEdit, QCheckBox, QGraphicsOpacityEffect,
)

from . import icons as iconlib
from .theme import add_shadow, RADIUS, SPACING, Theme


# ---------- 容器 ----------
class Card(QFrame):
    """圆角卡片, 可选阴影。"""

    def __init__(self, shadow: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        if shadow:
            add_shadow(self)


class HLine(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.HLine)


# ---------- 按钮 ----------
class PrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("primary")
        self.setCursor(Qt.PointingHandCursor)


class SecondaryButton(QPushButton):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("secondary")
        self.setCursor(Qt.PointingHandCursor)


class DangerButton(QPushButton):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("danger")
        self.setCursor(Qt.PointingHandCursor)


class GhostButton(QPushButton):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("ghost")
        self.setCursor(Qt.PointingHandCursor)


class IconButton(QPushButton):
    """纯图标按钮。"""

    def __init__(self, icon_name: str, size: int = 22, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("iconBtn")
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(iconlib.icon(icon_name))
        self.setIconSize(QSize(size, size))
        self.setFixedSize(36, 36)


# ---------- 图标底 ----------
class IconBadge(QWidget):
    """圆角方形图标底 (列表行/工具入口用)。"""

    def __init__(self, icon_name: str, side: int = 38, radius: int = RADIUS["md"],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._side = side
        self._radius = radius
        self.setFixedSize(side, side)
        main_color, soft = iconlib.tool_colors(icon_name)
        self._main = QColor(main_color)
        self._soft = QColor(soft)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self._soft)
        p.drawRoundedRect(self.rect(), self._radius, self._radius)
        pm = iconlib._raw_pixmap(self._icon_name)
        want = int(self._side * 0.58)
        pm = pm.scaled(want, want, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # 着色为主色
        tinted = QPixmap(pm.size())
        tinted.fill(Qt.transparent)
        tp = QPainter(tinted)
        tp.drawPixmap(0, 0, pm)
        tp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        tp.fillRect(tinted.rect(), self._main)
        tp.end()
        x = (self.width() - want) // 2
        y = (self.height() - want) // 2
        p.drawPixmap(x, y, tinted)
        p.end()


# ---------- 文字 ----------
class SectionHeader(QLabel):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("sectionHead")


class MutedLabel(QLabel):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("mutedLabel")


# ---------- 开关 ----------
class Switch(QCheckBox):
    """iOS 风格开关 (自绘胶囊 + 圆点)。"""

    def __init__(self, checked: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("switch")
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 28)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        on = self.isChecked()
        track = QColor(self._track_color(on))
        p.setBrush(track)
        p.drawRoundedRect(self.rect(), 14, 14)
        r = 12
        cx = (self.width() - r - 3) if on else 3
        cy = (self.height() - r) // 2
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(cx, cy, r, r)
        p.end()

    def _track_color(self, on: bool) -> str:
        # 由主题注入; 默认系统绿
        return getattr(self, "_on_color", "#34C759") if on else getattr(self, "_off_color", "#E5E5EA")


# ---------- 标签 ----------
class Chip(QFrame):
    """胶囊标签。"""

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("chip")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        self._label = QLabel(text)
        self._label.setObjectName("chipText")
        lay.addWidget(self._label)


# ---------- 搜索框 ----------
class SearchInput(QLineEdit):
    def __init__(self, placeholder: str = "搜索", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("search")
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)


# ---------- 列表行 ----------
class ListRow(QFrame):
    """通用列表行: 图标底 + 标题/副标题 + 右侧控件。"""

    clicked = Signal()

    def __init__(self, icon_name: Optional[str], title: str, subtitle: str = "",
                 clickable: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("listRow")
        self.setCursor(Qt.PointingHandCursor if clickable else Qt.ArrowCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(12)
        if icon_name:
            lay.addWidget(IconBadge(icon_name))
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("rowTitle")
        text_box.addWidget(self.title)
        if subtitle:
            self.subtitle = QLabel(subtitle)
            self.subtitle.setObjectName("rowSubtitle")
            text_box.addWidget(self.subtitle)
        lay.addLayout(text_box, 1)
        self._right = QHBoxLayout()
        self._right.setSpacing(6)
        lay.addLayout(self._right)

    def add_right(self, w: QWidget):
        self._right.addWidget(w)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ---------- 导航项 ----------
class NavItem(QPushButton):
    """侧边导航项 (图标 + 文字, 选中态)。"""

    def __init__(self, key: str, icon_name: str, label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("navItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(iconlib.icon(icon_name))
        self.setIconSize(QSize(20, 20))
        self.setText(label)
        self.setMinimumHeight(40)


# ---------- 聊天气泡 ----------
class ChatBubble(QFrame):
    def __init__(self, text: str, user: bool, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("userBubble" if user else "botBubble")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setObjectName("userText" if user else "botText")
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        lay.addWidget(label)
