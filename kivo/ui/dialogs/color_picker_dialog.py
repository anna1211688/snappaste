# -*- coding: utf-8 -*-
"""取色器弹窗: 历史色板、颜色详情与复制，屏幕取色回调注入。"""
from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QPushButton, QLabel, QGridLayout, QFrame, QVBoxLayout, QHBoxLayout,
)

from .base import Dialog
from ..components import PrimaryButton, SecondaryButton
from ...core import color_store


class ColorPickerDialog(Dialog):
    def __init__(self, parent, config, pick_screen_callback=None):
        super().__init__(parent, "取色器", width=460)
        self.config = config
        self.pick_screen_callback = pick_screen_callback

        pick = PrimaryButton("屏幕取色")
        pick.clicked.connect(self._pick_screen)
        self.body.addWidget(pick)

        self.grid_host = QFrame()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(6)
        self.body.addWidget(self.grid_host)

        self.detail = QFrame()
        self.detail_lay = QVBoxLayout(self.detail)
        self.body.addWidget(self.detail)

        self.history = color_store.parse_history(
            config.get("Config", "ColorHistory", fallback=""))
        self._render_grid()

    def _pick_screen(self):
        if self.pick_screen_callback:
            self.pick_screen_callback()

    def _render_grid(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()
        if not self.history:
            empty = QLabel("还没有历史颜色，点「屏幕取色」开始")
            empty.setObjectName("muted")
            self.grid.addWidget(empty, 0, 0)
            return
        for i, hexv in enumerate(self.history):
            sw = QPushButton()
            sw.setFixedSize(40, 32)
            sw.setObjectName("colorSwatch")
            sw.setStyleSheet(f"background:{hexv};border-radius:4px;")
            sw.clicked.connect(lambda checked, h=hexv: self._show_detail(h))
            self.grid.addWidget(sw, i // 8, i % 8)

    def _show_detail(self, hexv):
        fmts = color_store.color_formats(hexv)
        while self.detail_lay.count():
            it = self.detail_lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()
        if not fmts:
            return
        row = QHBoxLayout()
        block = QLabel()
        block.setFixedSize(44, 44)
        block.setStyleSheet(f"background:{hexv};border-radius:6px;")
        row.addWidget(block)
        col = QVBoxLayout()
        for key in ("hex", "rgb", "hsl"):
            r = QHBoxLayout()
            lab = QLabel(fmts[key])
            cp = SecondaryButton("复制")
            cp.clicked.connect(lambda checked, v=fmts[key]: self._copy(v))
            r.addWidget(lab); r.addWidget(cp); r.addStretch()
            col.addLayout(r)
        row.addLayout(col)
        self.detail_lay.addLayout(row)

    def _copy(self, value):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(value)

    def add_picked(self, hexv):
        self.history = color_store.add_to_history(self.history, hexv)
        self.config.set("Config", "ColorHistory", json.dumps(self.history))
        self.config.save()
        self._render_grid()
