# -*- coding: utf-8 -*-
"""Spotlight 式快捷面板: 搜索框 + 结果列表，键盘导航，选中即粘贴。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QVBoxLayout, QListWidget, QListWidgetItem,
)

from ..theme import Theme, add_shadow
from ..components import SearchInput
from ...core import quick_store


class QuickPanel(QDialog):
    def __init__(self, theme: Theme, records, phrases,
                 pick_callback=None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.records = records
        self.phrases = phrases
        self.pick_callback = pick_callback
        self._results = []

        self.setObjectName("quickRoot")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(580, 380)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        self.card = QFrame()
        self.card.setObjectName("quickCard")
        add_shadow(self.card, blur=30, dy=12, alpha=60)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        self.entry = SearchInput("搜索剪贴板、常用语，或直接算算术…")
        self.entry.textChanged.connect(self.refresh)
        self.entry.returnPressed.connect(self.pick)
        cl.addWidget(self.entry)

        self.list = QListWidget()
        self.list.setObjectName("quickList")
        self.list.itemActivated.connect(lambda _it: self.pick())
        cl.addWidget(self.list)
        outer.addWidget(self.card)

        self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self.entry.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close(); return
        if event.key() in (Qt.Key_Down, Qt.Key_Up):
            row = self.list.currentRow()
            count = self.list.count()
            if count:
                if event.key() == Qt.Key_Down:
                    self.list.setCurrentRow(min(count - 1, row + 1))
                else:
                    self.list.setCurrentRow(max(0, row - 1))
            return
        super().keyPressEvent(event)

    def refresh(self):
        self._results = quick_store.collect(
            self.entry.text(), self.records, self.phrases)
        self.list.clear()
        for label, _value in self._results:
            self.list.addItem(QListWidgetItem(label))
        if self.list.count():
            self.list.setCurrentRow(0)

    def pick(self):
        if not self._results:
            return
        row = self.list.currentRow()
        if row < 0:
            row = 0
        value = self._results[row][1]
        self.close()
        if self.pick_callback:
            self.pick_callback(value)
