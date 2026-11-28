# -*- coding: utf-8 -*-
"""剪贴板面板: 记录列表、搜索、锁定/去重/删除、多次复制与顺序粘贴、粘贴选项。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QVBoxLayout, QHBoxLayout, QComboBox,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, DangerButton, SectionHeader, EmptyState,
)
from ...core.i18n import tr
from ..icons import icon


class ClipPanel(QWidget):
    def __init__(self, theme: Theme, clip_store):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = clip_store
        self._visible = []  # 过滤后可见的 records 索引

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel(tr("clip.title"))
        title.setObjectName("hero")
        head.addWidget(title)
        head.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("clip.search_ph"))
        self.search.setFixedWidth(220)
        self.search.textChanged.connect(self.refresh)
        head.addWidget(self.search)
        root.addLayout(head)

        root.addWidget(self._records_card(), 1)
        root.addLayout(self._action_row())
        root.addWidget(self._options_card())

        self.refresh()

    # ---------- 记录卡 ----------
    def _records_card(self):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=22, alpha=28)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        lock = SecondaryButton(tr("clip.lock"), icon_name="lock")
        lock.clicked.connect(self.toggle_lock)
        dedupe = SecondaryButton(tr("clip.dedupe"), icon_name="filter")
        dedupe.clicked.connect(self.dedupe)
        del_sel = DangerButton(tr("clip.del_sel"), icon_name="trash")
        del_sel.clicked.connect(self.delete_selected)
        del_all = DangerButton(tr("clip.del_all"), icon_name="trash")
        del_all.clicked.connect(self.delete_all)
        for b in (lock, dedupe):
            top.addWidget(b)
        top.addStretch()
        top.addWidget(del_sel)
        top.addWidget(del_all)
        lay.addLayout(top)

        self.listw = QListWidget()
        self.listw.setObjectName("recordList")
        self.listw.setSelectionMode(QListWidget.SingleSelection)
        lay.addWidget(self.listw)

        self.empty = EmptyState(
            "copy", tr("clip.empty_title"), tr("clip.empty_sub"))
        lay.addWidget(self.empty)
        return card

    def refresh(self):
        q = self.search.text().strip().lower()
        self.listw.clear()
        self._visible = []
        for i, r in enumerate(self.store.records):
            if q and q not in r["text"].lower():
                continue
            self._visible.append(i)
            item = QListWidgetItem(f"{len(self._visible)}.  {r['text']}")
            if r["locked"]:
                item.setForeground(Qt.gray)
                item.setIcon(icon("lock"))
            self.listw.addItem(item)
        has = self.listw.count() > 0
        self.listw.setVisible(has)
        self.empty.setVisible(not has)

    def selected_record_idx(self):
        row = self.listw.currentRow()
        if row < 0 or row >= len(self._visible):
            return -1
        return self._visible[row]

    # ---------- 顶部操作 ----------
    def toggle_lock(self):
        i = self.selected_record_idx()
        if i >= 0:
            self.store.toggle_lock(i)
            self.store.save()
            self.refresh()

    def dedupe(self):
        self.store.dedupe()
        self.store.save()
        self.refresh()

    def delete_selected(self):
        i = self.selected_record_idx()
        if i >= 0:
            self.store.delete(i)
            self.store.save()
            self.refresh()

    def delete_all(self):
        self.store.delete_all()
        self.store.save()
        self.refresh()

    # ---------- 主操作行 ----------
    def _action_row(self):
        row = QHBoxLayout()
        multi = PrimaryButton(tr("clip.multi"), icon_name="copy")
        multi.clicked.connect(self.multi_copy)
        paste_one = SecondaryButton(tr("clip.paste_next"), icon_name="chevron-right")
        paste_one.clicked.connect(self.paste_next)
        paste_all = SecondaryButton(tr("clip.paste_all"), icon_name="check")
        paste_all.clicked.connect(self.paste_all)
        row.addWidget(multi)
        row.addWidget(paste_one)
        row.addWidget(paste_all)
        row.addStretch()
        return row

    def multi_copy(self):
        from PySide6.QtWidgets import QApplication
        text = QApplication.clipboard().text()
        if text:
            self.store.add(text)
            self.store.save()
            self.refresh()

    def paste_next(self):
        if self.store.paste_index >= len(self.store.records):
            return
        r = self.store.records[self.store.paste_index]
        self._set_clipboard(r["text"])
        self.store.paste_index += 1

    def paste_all(self):
        sep = self._separator_text()
        text = sep.join(r["text"] for r in self.store.records)
        self._set_clipboard(text)
        self.store.paste_index = len(self.store.records)

    def _set_clipboard(self, text):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    # ---------- 粘贴选项 ----------
    def _options_card(self):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        lay.addWidget(SectionHeader(tr("clip.options")))

        row = QHBoxLayout()
        row.addWidget(QLabel(tr("clip.separator")))
        self.sep_combo = QComboBox()
        self.sep_combo.addItem(tr("clip.sep_enter"), "enter")
        self.sep_combo.addItem("TAB", "tab")
        self.sep_combo.addItem(tr("clip.sep_none"), "none")
        row.addWidget(self.sep_combo)
        row.addSpacing(16)
        row.addWidget(QLabel(tr("clip.interval")))
        self.interval = QLineEdit("0")
        self.interval.setFixedWidth(80)
        row.addWidget(self.interval)
        row.addStretch()
        lay.addLayout(row)
        return card

    def _separator_text(self):
        v = self.sep_combo.currentData()
        return {"enter": "\n", "tab": "\t", "none": ""}.get(v, "\n")
