# -*- coding: utf-8 -*-
"""AI 长期记忆管理弹窗。"""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QLineEdit

from .base import Dialog
from ..components import PrimaryButton, SecondaryButton, DangerButton
from ...core import memory_store
from ...core.i18n import tr


class AiMemoryDialog(Dialog):
    def __init__(self, parent, memory_path):
        super().__init__(parent, tr("mem.title"), width=520)
        self.path = memory_path
        self.items = memory_store.load_memory(memory_path)
        self._confirming_clear = False

        h = self._muted(tr("mem.hint"))
        self.body.addWidget(h)

        self.list = QListWidget()
        self.list.setObjectName("promptList")
        self.body.addWidget(self.list)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText(tr("mem.ph"))
        self.entry.returnPressed.connect(self._add)
        self.body.addWidget(self.entry)

        add_b = PrimaryButton(tr("common.add"), icon_name="plus")
        add_b.clicked.connect(self._add)
        del_b = SecondaryButton(tr("mem.delete_sel"), icon_name="trash")
        del_b.clicked.connect(self._delete)
        self.clear_b = DangerButton(tr("mem.clear_all"), icon_name="trash")
        self.clear_b.clicked.connect(self._clear)
        self.add_button(self.clear_b); self.add_button(del_b); self.add_button(add_b)

        self._refresh()

    def _muted(self, text):
        from PySide6.QtWidgets import QLabel
        lab = QLabel(text)
        lab.setWordWrap(True)
        lab.setObjectName("muted")
        return lab

    def _refresh(self):
        self.list.clear()
        for m in self.items:
            self.list.addItem(QListWidgetItem(m["text"]))
        if self.list.count():
            self.list.setCurrentRow(0)

    def _add(self):
        if memory_store.add_memory(self.items, self.entry.text()):
            memory_store.save_memory(self.path, self.items)
            self.entry.clear()
            self._refresh()

    def _delete(self):
        if memory_store.delete_memory(self.items, self.list.currentRow()):
            memory_store.save_memory(self.path, self.items)
            self._refresh()

    def _clear(self):
        # 二次确认：第一次进入确认态，3 秒内再点才执行
        if not self._confirming_clear:
            self._confirming_clear = True
            self.clear_b.setText(tr("mem.confirm"))
            QTimer.singleShot(3000, self._reset_confirm)
            return
        memory_store.clear_memory(self.items)
        memory_store.save_memory(self.path, self.items)
        self._reset_confirm()
        self._refresh()

    def _reset_confirm(self):
        self._confirming_clear = False
        self.clear_b.setText(tr("mem.clear_all"))
