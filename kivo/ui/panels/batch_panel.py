# -*- coding: utf-8 -*-
"""图片批量处理面板: 文件列表 + 处理选项 + 后台处理 + 进度。"""
from __future__ import annotations

import os

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QListWidget, QRadioButton, QButtonGroup, QFileDialog,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton
from ..dialogs.base import show_toast
from ...core.batch_store import BatchStore, validate_options
from ...core.i18n import tr


class _Worker(QObject):
    progress = Signal(int, int)
    finished = Signal(int, list)

    def __init__(self, store, files, opts, out_dir):
        super().__init__()
        self.store = store
        self.files = files
        self.opts = opts
        self.out_dir = out_dir

    def run(self):
        ok, errors = self.store.run_all(
            self.files, self.opts, self.out_dir,
            lambda i, t: self.progress.emit(i, t))
        self.finished.emit(ok, errors)


class BatchPanel(QWidget):
    def __init__(self, theme: Theme, store: BatchStore | None = None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = store or BatchStore()
        self.files = []
        self._thread = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(10)

        title = QLabel(tr("batch.title"))
        title.setObjectName("hero")
        outer.addWidget(title)

        # 文件列表
        list_card = QFrame()
        list_card.setObjectName("card")
        add_shadow(list_card, blur=14, alpha=20)
        ll = QVBoxLayout(list_card)
        ll.setContentsMargins(12, 10, 12, 10)
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(120)
        ll.addWidget(self.file_list)
        fb = QHBoxLayout()
        add = SecondaryButton(tr("batch.add_images"), icon_name="plus")
        add.clicked.connect(self._add_files)
        remove = SecondaryButton(tr("batch.remove_sel"), icon_name="trash")
        remove.clicked.connect(self._remove_sel)
        fb.addWidget(add); fb.addWidget(remove); fb.addStretch()
        ll.addLayout(fb)
        outer.addWidget(list_card)

        # 选项
        opt_card = QFrame()
        opt_card.setObjectName("card")
        add_shadow(opt_card, blur=14, alpha=20)
        ol = QVBoxLayout(opt_card)
        ol.setContentsMargins(14, 12, 14, 12)
        ol.setSpacing(8)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel(tr("batch.percent")))
        self.percent = QLineEdit("100"); self.percent.setFixedWidth(70)
        r1.addWidget(self.percent)
        r1.addWidget(QLabel(tr("batch.max_side")))
        self.max_side = QLineEdit("0"); self.max_side.setFixedWidth(70)
        r1.addWidget(self.max_side)
        r1.addStretch()
        ol.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel(tr("batch.output_fmt")))
        self.fmt_group = QButtonGroup(self)
        for txt, val in ((tr("batch.keep_fmt"), ""), ("JPG", "jpg"),
                         ("PNG", "png"), ("WEBP", "webp")):
            rb = QRadioButton(txt)
            rb.setProperty("fmt", val)
            if val == "":
                rb.setChecked(True)
            self.fmt_group.addButton(rb)
            r2.addWidget(rb)
        r2.addStretch()
        ol.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel(tr("batch.quality")))
        self.quality = QLineEdit("88"); self.quality.setFixedWidth(70)
        r3.addWidget(self.quality)
        r3.addStretch()
        ol.addLayout(r3)

        r4 = QHBoxLayout()
        r4.addWidget(QLabel(tr("batch.watermark")))
        self.watermark = QLineEdit(); self.watermark.setFixedWidth(220)
        r4.addWidget(self.watermark)
        r4.addStretch()
        ol.addLayout(r4)
        outer.addWidget(opt_card)

        # 输出目录 + 运行
        r5 = QHBoxLayout()
        r5.addWidget(QLabel(tr("batch.out_folder")))
        self.out_dir = QLineEdit(); self.out_dir.setMinimumWidth(260)
        r5.addWidget(self.out_dir, 1)
        pick = SecondaryButton(tr("batch.choose"), icon_name="folder-open")
        pick.clicked.connect(self._pick_dir)
        r5.addWidget(pick)
        outer.addLayout(r5)

        self.progress_lab = QLabel("")
        self.progress_lab.setObjectName("mutedLabel")
        outer.addWidget(self.progress_lab)

        run = PrimaryButton(tr("batch.start"), icon_name="zap")
        run.clicked.connect(self._run)
        outer.addWidget(run)
        outer.addStretch()

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("batch.choose_images"), "",
            "图片 (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff)")
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_list.addItem(os.path.basename(p))

    def _remove_sel(self):
        for item in self.file_list.selectedItems():
            idx = self.file_list.row(item)
            self.file_list.takeItem(idx)
            del self.files[idx]

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr("batch.choose_out"))
        if d:
            self.out_dir.setText(d)

    def _run(self):
        if self._thread is not None:
            return
        if not self.files:
            show_toast(self, tr("batch.need_images"))
            return
        try:
            percent = int(self.percent.text())
            max_side = int(self.max_side.text())
            quality = int(self.quality.text())
        except ValueError:
            show_toast(self, tr("batch.bad_params"))
            return
        if not validate_options(percent, max_side, quality):
            show_toast(self, tr("batch.bad_params"))
            return

        out_dir = self.out_dir.text().strip()
        if not out_dir:
            out_dir = os.path.join(os.path.dirname(self.files[0]) or ".", "kivo_batch")
            self.out_dir.setText(out_dir)

        rb = self.fmt_group.checkedButton()
        opts = {"percent": percent, "max_side": max_side, "quality": quality,
                "format": rb.property("fmt"),
                "watermark": self.watermark.text().strip()}

        self._thread = QThread(self)
        self._worker = _Worker(self.store, list(self.files), opts, out_dir)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_progress(self, i, total):
        self.progress_lab.setText(tr("batch.processing", i=i, total=total))

    def _on_finished(self, ok, errors):
        msg = tr("batch.done", ok=ok)
        if errors:
            msg += tr("batch.failed_count", n=len(errors))
        self.progress_lab.setText(msg)
        show_toast(self, msg)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
