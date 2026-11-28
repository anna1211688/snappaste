# -*- coding: utf-8 -*-
"""热键设置弹窗: 27 个动作的录入/清除/恢复预设，冲突二次确认后保存。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QLineEdit, QLabel, QPushButton, QScrollArea, QWidget,
    QGridLayout,
)

from ..theme import Theme
from ..components import PrimaryButton, SecondaryButton, MutedLabel
from .base import Dialog, show_toast
from ...core import hotkey_store as hs
from ...core.i18n import tr

_SPECIAL_KEYS = {
    Qt.Key_Space: "space", Qt.Key_Return: "enter", Qt.Key_Enter: "enter",
    Qt.Key_Tab: "tab", Qt.Key_Backspace: "backspace", Qt.Key_Delete: "delete",
    Qt.Key_Home: "home", Qt.Key_End: "end",
    Qt.Key_Left: "left", Qt.Key_Right: "right", Qt.Key_Up: "up", Qt.Key_Down: "down",
    Qt.Key_Insert: "insert", Qt.Key_PageUp: "pageup", Qt.Key_PageDown: "pagedown",
}


class HotkeyEdit(QLineEdit):
    """支持按键捕获的输入框。"""

    def __init__(self, initial):
        super().__init__(initial)
        self._capturing = False
        self._old = initial

    def start_capture(self):
        self._capturing = True
        self._old = self.text()
        self.setText(tr("hkdlg.press"))
        self.setFocus()

    def keyPressEvent(self, e):
        if not self._capturing:
            super().keyPressEvent(e)
            return
        key = e.key()
        if key == Qt.Key_Escape:
            self._capturing = False
            self.setText(self._old)
            return
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        mods = []
        m = e.modifiers()
        if m & Qt.ControlModifier:
            mods.append("ctrl")
        if m & Qt.AltModifier:
            mods.append("alt")
        if m & Qt.ShiftModifier:
            mods.append("shift")
        if m & Qt.MetaModifier:
            mods.append("win")
        name = self._key_name(key)
        if not name:
            return
        self._capturing = False
        self.setText("+".join(mods + [name]))

    @staticmethod
    def _key_name(key):
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        if Qt.Key_F1 <= key <= Qt.Key_F35:
            return f"f{key - Qt.Key_F1 + 1}"
        return _SPECIAL_KEYS.get(key)


class HotkeyDialog(Dialog):
    def __init__(self, parent, theme: Theme, config, on_applied=None):
        super().__init__(parent, tr("hkdlg.title"), width=520)
        self.theme = theme
        self.config = config
        self.on_applied = on_applied
        self.editors = {}
        self._confirming = False

        hint = MutedLabel(tr("hkdlg.hint"))
        hint.setWordWrap(True)
        self.body.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(380)
        host = QWidget()
        host.setObjectName("transparentPane")
        grid = QGridLayout(host)
        grid.setContentsMargins(2, 2, 6, 2)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        for row, (section, key, label_key) in enumerate(hs.HOTKEY_ACTIONS):
            grid.addWidget(QLabel(tr(label_key)), row, 0)
            cur = hs.current_value(self.config, section, key)
            edit = HotkeyEdit(tr("hk.none") if cur == hs.NONE else cur)
            edit.setFixedWidth(150)
            self.editors[(section, key)] = edit
            grid.addWidget(edit, row, 1)
            rec = QPushButton(tr("hkdlg.capture"))
            rec.clicked.connect(edit.start_capture)
            grid.addWidget(rec, row, 2)
            clr = QPushButton(tr("hkdlg.clear"))
            clr.clicked.connect(
                lambda _f=False, e=edit: e.setText(tr("hk.none")))
            grid.addWidget(clr, row, 3)
        scroll.setWidget(host)
        self.body.addWidget(scroll)

        restore = SecondaryButton(tr("hkdlg.restore"), icon_name="refresh")
        restore.clicked.connect(self._restore_defaults)
        self.add_button(restore)

        self.apply_btn = PrimaryButton(tr("common.apply"), icon_name="check")
        self.apply_btn.clicked.connect(self._apply)
        self.add_button(self.apply_btn)

    def _current_mapping(self):
        return {ak: e.text() for ak, e in self.editors.items()}

    def _restore_defaults(self):
        for ak, val in hs.default_mapping().items():
            self.editors[ak].setText(
                tr("hk.none") if val == hs.NONE else val)
        show_toast(self, tr("hkdlg.restored"))

    def _apply(self):
        mapping = self._current_mapping()
        normalized = [(ak, hs.normalize_hotkey(v)) for ak, v in mapping.items()]
        conflicts = hs.find_conflicts(normalized)
        if conflicts and not self._confirming:
            self._confirming = True
            self.apply_btn.setText(tr("hkdlg.confirm_conflict"))
            show_toast(self, tr("hkdlg.dup"))
            QTimer.singleShot(3000, self._reset_confirm)
            return
        self._reset_confirm()
        hs.apply_mapping(self.config, mapping)
        self.config.save()
        if self.on_applied:
            self.on_applied()
        show_toast(self, tr("hkdlg.saved"))
        self.accept()

    def _reset_confirm(self):
        self._confirming = False
        self.apply_btn.setText(tr("common.apply"))
