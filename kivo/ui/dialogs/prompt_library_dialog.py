# -*- coding: utf-8 -*-
"""角色 / 提示词库弹窗。"""
from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QLineEdit, QTextEdit

from .base import Dialog
from ..components import PrimaryButton, SecondaryButton, DangerButton
from ...core import prompt_store
from ...core.i18n import tr


class PromptEditDialog(Dialog):
    """新增提示词的二级弹窗。"""

    def __init__(self, parent):
        super().__init__(parent, tr("plib.new_prompt"), width=420)
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText(tr("common.title"))
        self.body.addWidget(self.title_in)
        self.prompt_in = QTextEdit()
        self.prompt_in.setPlaceholderText(tr("plib.prompt_ph"))
        self.prompt_in.setFixedHeight(180)
        self.body.addWidget(self.prompt_in)

        save = PrimaryButton(tr("common.save"), icon_name="save")
        save.clicked.connect(self.accept)
        self.add_button(save, accept=False)

    def values(self):
        return self.title_in.text().strip(), self.prompt_in.toPlainText().strip()


class PromptLibraryDialog(Dialog):
    def __init__(self, parent, prompts_path, apply_callback=None,
                 clear_callback=None):
        super().__init__(parent, tr("plib.library_title"), width=520)
        self.path = prompts_path
        self.apply_callback = apply_callback
        self.clear_callback = clear_callback
        self.items = prompt_store.load_library(prompts_path)

        self.list = QListWidget()
        self.list.setObjectName("promptList")
        self.body.addWidget(self.list)
        self._refresh()

        apply_b = PrimaryButton(tr("plib.apply_role"), icon_name="check")
        apply_b.clicked.connect(self._apply)
        add_b = SecondaryButton(tr("common.new"), icon_name="plus")
        add_b.clicked.connect(self._add)
        del_b = DangerButton(tr("plib.delete_sel"), icon_name="trash")
        del_b.clicked.connect(self._delete)
        clear_b = SecondaryButton(tr("plib.clear_role"), icon_name="trash")
        clear_b.clicked.connect(self._clear)
        self.add_button(clear_b); self.add_button(del_b)
        self.add_button(add_b); self.add_button(apply_b)

    def _refresh(self):
        self.list.clear()
        for it in self.items:
            self.list.addItem(QListWidgetItem(
                prompt_store.role_title_label(it["title"])))
        if self.list.count():
            self.list.setCurrentRow(0)

    def _add(self):
        dlg = PromptEditDialog(self)
        if dlg.exec() and dlg.values()[0] and dlg.values()[1]:
            title, prompt = dlg.values()
            if prompt_store.add_item(self.items, title, prompt):
                prompt_store.save_library(self.path, self.items)
                self._refresh()

    def _delete(self):
        row = self.list.currentRow()
        if prompt_store.delete_item(self.items, row):
            prompt_store.save_library(self.path, self.items)
            self._refresh()

    def _apply(self):
        row = self.list.currentRow()
        if row < 0:
            return
        chosen = dict(self.items[row])
        if self.apply_callback:
            self.apply_callback(chosen)
        self.accept()

    def _clear(self):
        if self.clear_callback:
            self.clear_callback()
        self.accept()
