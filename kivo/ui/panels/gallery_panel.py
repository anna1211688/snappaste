# -*- coding: utf-8 -*-
"""截图历史画廊面板: 网格缩略图、钉图/删除、空状态。"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout,
)

from ..theme import Theme
from ..components import DangerButton, EmptyState
from ...core import gallery_store
from ...core.i18n import tr

THUMB_W, THUMB_H = 160, 110
COLUMNS = 4


class GalleryPanel(QWidget):
    def __init__(self, theme: Theme, shots_dir, pin_callback=None,
                 screenshot_callback=None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.shots_dir = shots_dir
        self.pin_callback = pin_callback
        self.screenshot_callback = screenshot_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel(tr("gallery.title"))
        title.setObjectName("hero")
        head.addWidget(title)
        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        head.addWidget(self.count_label)
        head.addStretch()
        del_all = DangerButton(tr("gallery.del_all"), icon_name="trash")
        del_all.clicked.connect(self._delete_all)
        head.addWidget(del_all)
        outer.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("scrollArea")
        self.container = QWidget()
        self.container.setObjectName("scrollBody")
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setSpacing(12)
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll)

        self.refresh()

    def refresh(self):
        self._clear_grid()
        all_files = gallery_store.list_files(self.shots_dir)
        files = all_files[:gallery_store.GALLERY_MAX]
        if len(all_files) > gallery_store.GALLERY_MAX:
            self.count_label.setText(tr("gallery.count_more",
                                       total=len(all_files),
                                       limit=gallery_store.GALLERY_MAX))
        else:
            self.count_label.setText(tr("gallery.count", n=len(all_files)))

        if not files:
            self._build_empty()
            return
        for i, name in enumerate(files):
            self.grid.addWidget(self._make_cell(name), i // COLUMNS, i % COLUMNS)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _build_empty(self):
        box = EmptyState(
            "browser", tr("gallery.empty_title"), tr("gallery.empty_sub"),
            action_text=tr("gallery.shot") if self.screenshot_callback else "",
            on_action=self.screenshot_callback)
        self.grid.addWidget(box, 0, 0, 1, COLUMNS)

    def _make_cell(self, name):
        cell = QFrame()
        cell.setObjectName("galCell")
        lay = QVBoxLayout(cell)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        img = QLabel()
        img.setFixedSize(THUMB_W, THUMB_H)
        img.setAlignment(Qt.AlignCenter)
        img.setObjectName("thumb")
        path = os.path.join(self.shots_dir, name)
        pm = QPixmap(path)
        if not pm.isNull():
            img.setPixmap(pm.scaled(THUMB_W, THUMB_H,
                                    Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lay.addWidget(img)

        lab = QLabel(gallery_store.cell_label(name))
        lab.setObjectName("galName")
        lab.setAlignment(Qt.AlignCenter)
        lay.addWidget(lab)

        btn_row = QHBoxLayout()
        pin_btn = QPushButton(tr("gallery.pin"))
        pin_btn.setObjectName("miniBtn")
        pin_btn.clicked.connect(lambda: self._pin(name))
        del_btn = QPushButton(tr("gallery.delete"))
        del_btn.setObjectName("miniBtn")
        del_btn.clicked.connect(lambda: self._delete_one(name))
        btn_row.addWidget(pin_btn); btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)
        return cell

    def _pin(self, name):
        if self.pin_callback:
            self.pin_callback(name)

    def _delete_one(self, name):
        gallery_store.delete_file(self.shots_dir, name)
        self.refresh()

    def _delete_all(self):
        gallery_store.delete_all(self.shots_dir)
        self.refresh()
