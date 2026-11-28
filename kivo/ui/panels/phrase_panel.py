# -*- coding: utf-8 -*-
"""常用语面板: 列表+编辑区、新增/保存/删除/排序、复制与直接粘贴。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout,
    QHBoxLayout, QTextEdit,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, SectionHeader, MutedLabel,
)


class PhrasePanel(QWidget):
    def __init__(self, theme: Theme, phrase_store):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = phrase_store

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel("常用语")
        title.setObjectName("hero")
        root.addWidget(title)
        root.addWidget(self._main_card(), 1)

    def _main_card(self):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=22, alpha=28)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.listw = QListWidget()
        self.listw.setObjectName("recordList")
        self.listw.currentRowChanged.connect(self._on_select)
        self.listw.itemActivated.connect(lambda _it: self.paste_selected())
        lay.addWidget(self.listw, 1)

        self.empty = self._empty_widget()
        lay.addWidget(self.empty)

        hint = MutedLabel("选中一条，内容会填进编辑区；改完点「保存修改」。双击列表可直接粘贴。")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.editor = QTextEdit()
        self.editor.setObjectName("phraseEditor")
        self.editor.setFixedHeight(96)
        lay.addWidget(self.editor)

        lay.addLayout(self._button_row())
        self.refresh()
        return card

    def _empty_widget(self):
        box = QWidget()
        v = QVBoxLayout(box)
        v.setAlignment(Qt.AlignCenter)
        icon = QLabel("💬")
        icon.setAlignment(Qt.AlignCenter)
        t1 = QLabel("还没有常用语")
        t1.setAlignment(Qt.AlignCenter)
        t1.setObjectName("blockHead")
        t2 = MutedLabel("把常回的话存成一条，之后双击就能直接粘贴")
        t2.setAlignment(Qt.AlignCenter)
        v.addWidget(icon)
        v.addWidget(t1)
        v.addWidget(t2)
        return box

    def refresh(self):
        self.listw.clear()
        for i, p in enumerate(self.store.phrases):
            body = p["text"].strip()
            first = body.splitlines()[0] if body else ""
            suffix = " …" if len(body) > len(first) or len(first) > 58 else ""
            self.listw.addItem(QListWidgetItem(f"{i + 1}. {first[:58]}{suffix}"))
        has = bool(self.store.phrases)
        self.listw.setVisible(has)
        self.empty.setVisible(not has)

    def _on_select(self, row):
        if 0 <= row < len(self.store.phrases):
            self.editor.setPlainText(self.store.phrases[row]["text"])

    def _button_row(self):
        row = QHBoxLayout()
        paste = PrimaryButton("粘贴选中")
        paste.clicked.connect(self.paste_selected)
        copy = SecondaryButton("复制选中")
        copy.clicked.connect(self.copy_selected)
        add = SecondaryButton("新增")
        add.clicked.connect(self.add)
        from_clip = SecondaryButton("从剪贴板添加")
        from_clip.clicked.connect(self.add_from_clipboard)
        save = SecondaryButton("保存修改")
        save.clicked.connect(self.save_edit)
        delete = SecondaryButton("删除")
        delete.clicked.connect(self.delete)
        up = SecondaryButton("上移")
        up.clicked.connect(lambda: self.move(-1))
        down = SecondaryButton("下移")
        down.clicked.connect(lambda: self.move(1))
        for b in (paste, copy, add, from_clip, save, delete, up, down):
            row.addWidget(b)
        return row

    # ---------- 动作 ----------
    def add(self):
        if self.store.add(self.editor.toPlainText()):
            self.store.save()
            self.editor.clear()
            self.refresh()

    def add_from_clipboard(self):
        from PySide6.QtWidgets import QApplication
        if self.store.add(QApplication.clipboard().text()):
            self.store.save()
            self.refresh()

    def save_edit(self):
        row = self.listw.currentRow()
        if self.store.update(row, self.editor.toPlainText()):
            self.store.save()
            self.refresh()

    def delete(self):
        row = self.listw.currentRow()
        if self.store.delete(row) is not None:
            self.store.save()
            self.editor.clear()
            self.refresh()

    def move(self, d):
        row = self.listw.currentRow()
        j = self.store.move(row, d)
        if j is not None:
            self.store.save()
            self.refresh()
            self.listw.setCurrentRow(j)

    def copy_selected(self):
        row = self.listw.currentRow()
        if 0 <= row < len(self.store.phrases):
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.store.phrases[row]["text"])

    def paste_selected(self):
        # 窗口隐藏/键盘模拟属于 Windows 系统层；这里先把内容放入剪贴板保证链路可用
        self.copy_selected()
