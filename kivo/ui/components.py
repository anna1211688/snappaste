# -*- coding: utf-8 -*-
"""KIVO 通用组件库。所有组件用 objectName 挂应用级 QSS, 不内联样式。"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QCheckBox,
)

from . import icons as iconlib
from .theme import add_shadow, RADIUS
from ..core.i18n import tr


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
class _TextIconButton(QPushButton):
    """文字 + 可选图标的按钮基类。"""

    OBJECT_NAME = ""
    ICON_COLOR = ""  # 空串表示使用图标默认中性色

    def __init__(self, text: str = "", parent: Optional[QWidget] = None,
                 icon_name: Optional[str] = None, icon_size: int = 16):
        super().__init__(text, parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setCursor(Qt.PointingHandCursor)
        if icon_name:
            if self.ICON_COLOR:
                self.setIcon(iconlib.tinted_icon(icon_name, self.ICON_COLOR))
            else:
                self.setIcon(iconlib.icon(icon_name))
            self.setIconSize(QSize(icon_size, icon_size))


class PrimaryButton(_TextIconButton):
    OBJECT_NAME = "primary"
    ICON_COLOR = "#FFFFFF"


class SecondaryButton(_TextIconButton):
    OBJECT_NAME = "secondary"


class DangerButton(_TextIconButton):
    OBJECT_NAME = "danger"
    ICON_COLOR = "#FFFFFF"


class GhostButton(_TextIconButton):
    OBJECT_NAME = "ghost"


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


class EmptyState(QWidget):
    """统一空状态: 矢量图标 + 标题 + 副标题 + 可选动作按钮。"""

    def __init__(self, icon_name: str, title: str, subtitle: str = "",
                 action_text: str = "", on_action=None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignCenter)
        v.setContentsMargins(20, 36, 20, 36)
        v.setSpacing(8)

        ic = QLabel()
        ic.setAlignment(Qt.AlignCenter)
        ic.setPixmap(iconlib.tinted_icon(icon_name, "#9AA7B8").pixmap(42, 42))
        t1 = QLabel(title)
        t1.setAlignment(Qt.AlignCenter)
        t1.setObjectName("emptyTitle")
        v.addWidget(ic)
        v.addWidget(t1)
        if subtitle:
            t2 = MutedLabel(subtitle)
            t2.setAlignment(Qt.AlignCenter)
            t2.setWordWrap(True)
            v.addWidget(t2)
        if action_text and on_action:
            b = SecondaryButton(action_text, icon_name=icon_name)
            b.clicked.connect(on_action)
            v.addWidget(b)


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
    def __init__(self, placeholder: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("search")
        self.setPlaceholderText(placeholder or tr("common.search"))
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
    """侧边导航项 (图标 + 文字, 选中态图标切换强调色)。"""

    def __init__(self, key: str, icon_name: str, label: str,
                 parent: Optional[QWidget] = None, active_color: str = "#007AFF"):
        super().__init__(parent)
        self.key = key
        self._icon_name = icon_name
        self._active_color = active_color
        self.setObjectName("navItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(iconlib.icon(icon_name))
        self.setIconSize(QSize(20, 20))
        self.setText(label)
        self.setMinimumHeight(40)
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked: bool):
        if checked:
            self.setIcon(iconlib.tinted_icon(self._icon_name, self._active_color))
        else:
            self.setIcon(iconlib.icon(self._icon_name))


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


# ---------- AI 回复操作栏 ----------
class MessageActionBar(QWidget):
    """AI 回复下方的紧凑操作栏: 复制/朗读/点赞/点踩/转发/重新生成。"""

    # (动作键, 图标名, 是否可选中)
    ACTIONS = [
        ("copy", "copy", False),
        ("speak", "volume", False),
        ("up", "thumbs-up", True),
        ("down", "thumbs-down", True),
        ("forward", "send", False),
        ("regenerate", "refresh", False),
    ]
    FEEDBACK = ("up", "down")
    action_triggered = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 0)
        lay.setSpacing(2)
        self._buttons = {}
        for key, icn, checkable in self.ACTIONS:
            b = QPushButton()
            b.setObjectName("msgAction")
            b.setIcon(iconlib.icon(icn))
            b.setIconSize(QSize(17, 17))
            b.setFixedSize(30, 30)
            b.setCheckable(checkable)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._on_click(k))
            if checkable:
                b.toggled.connect(lambda checked, bb=b, ic=icn:
                    bb.setIcon(iconlib.tinted_icon(ic, "#007AFF") if checked
                               else iconlib.icon(ic)))
            self._buttons[key] = b
            lay.addWidget(b)

    def _on_click(self, key):
        if key in self.FEEDBACK:
            self._toggle_feedback(key)
        self.action_triggered.emit(key)

    def _toggle_feedback(self, key):
        # 注意: clicked 触发时按钮已完成 toggle, 这里基于 toggle 后的状态处理
        other = "down" if key == "up" else "up"
        b, ob = self._buttons[key], self._buttons[other]
        if b.isChecked():
            ob.setChecked(False)  # 选中一个则取消另一个

    def reset_feedback(self):
        for k in self.FEEDBACK:
            self._buttons[k].setChecked(False)

    def feedback_state(self):
        if self._buttons["up"].isChecked():
            return "up"
        if self._buttons["down"].isChecked():
            return "down"
        return None
