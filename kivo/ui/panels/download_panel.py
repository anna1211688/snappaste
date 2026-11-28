# -*- coding: utf-8 -*-
"""无水印下载面板: 链接输入、目录、后台下载、进度条与下载记录。"""
from __future__ import annotations

import os

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, Switch, MutedLabel,
)
from ...core.download_store import DownloadStore, clean_url, default_dir
from ...core.i18n import tr


class _Worker(QObject):
    progress = Signal(float)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, store, url, download, outdir, use_cookies):
        super().__init__()
        self.store = store
        self.url = url
        self.download = download
        self.outdir = outdir
        self.use_cookies = use_cookies

    def _hook(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            got = d.get("downloaded_bytes") or 0
            if total:
                self.progress.emit(got * 100.0 / total)

    def run(self):
        try:
            info = self.store.run(self.url, self.download, self.outdir,
                                  self.use_cookies, self._hook)
            self.finished.emit(info or {})
        except Exception as e:  # 边界兜底：失败经信号回主线程提示
            self.failed.emit(str(e).replace("ERROR: ", "")[:300])


class DownloadPanel(QWidget):
    def __init__(self, theme: Theme, store: DownloadStore):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = store
        self._thread = None
        self._worker = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        title = QLabel(tr("dl.title"))
        title.setObjectName("hero")
        outer.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=18, alpha=24)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        lay.addWidget(MutedLabel(tr("dl.support")))

        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(tr("dl.url_ph"))
        url_row.addWidget(self.url_edit, 1)
        paste = SecondaryButton(tr("dl.paste"), icon_name="link")
        paste.clicked.connect(self._paste)
        url_row.addWidget(paste)
        lay.addLayout(url_row)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel(tr("dl.save_to")))
        self.dir_edit = QLineEdit(default_dir(self.store.config))
        dir_row.addWidget(self.dir_edit, 1)
        pick = SecondaryButton(tr("dl.pick_folder"), icon_name="folder-open")
        pick.clicked.connect(self._pick_dir)
        dir_row.addWidget(pick)
        lay.addLayout(dir_row)

        self.cookie_switch = Switch()
        self.cookie_switch._on_color = theme.tokens["accent"]
        lay.addLayout(self._switch_row(self.cookie_switch, tr("dl.cookie")))

        self.ask_switch = Switch(
            (self.store.config.get("Config", "DownloadAsk", fallback="1") or "1") != "0")
        self.ask_switch._on_color = theme.tokens["accent"]
        self.ask_switch.toggled.connect(self._save_ask)
        lay.addLayout(self._switch_row(self.ask_switch, tr("dl.ask")))

        btn_row = QHBoxLayout()
        parse_btn = SecondaryButton(tr("dl.parse"), icon_name="search")
        parse_btn.clicked.connect(lambda: self._start(False))
        self.dl_btn = PrimaryButton(tr("dl.start"), icon_name="download")
        self.dl_btn.clicked.connect(lambda: self._start(True))
        open_btn = SecondaryButton(tr("dl.open_folder"), icon_name="folder-open")
        open_btn.clicked.connect(self._open_dir)
        btn_row.addWidget(parse_btn)
        btn_row.addWidget(self.dl_btn)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        lay.addWidget(self.bar)

        self.status = MutedLabel(tr("dl.initial"))
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            (tr("dl.col_title"), tr("dl.col_site"), tr("dl.col_file")))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setFixedHeight(170)
        lay.addWidget(self.table)

        lay.addWidget(MutedLabel(tr("dl.copyright")))
        outer.addWidget(card)
        outer.addStretch()

    def _switch_row(self, sw, text):
        row = QHBoxLayout()
        row.addWidget(sw)
        lab = QLabel(text)
        lab.setObjectName("mutedLabel")
        row.addWidget(lab)
        row.addStretch()
        return row

    def _paste(self):
        from PySide6.QtWidgets import QApplication
        t = QApplication.clipboard().text().strip()
        if t:
            self.url_edit.setText(t)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr("dl.pick_location"), self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)
            self.store.config.set("Config", "DownloadDir", d)

    def _save_ask(self, on):
        self.store.config.set("Config", "DownloadAsk", "1" if on else "0")

    def _open_dir(self):
        d = self.dir_edit.text() or default_dir(self.store.config)
        os.makedirs(d, exist_ok=True)
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def _set_busy(self, busy):
        self.dl_btn.setEnabled(not busy)

    def _start(self, download):
        if self._thread is not None:
            return
        url = clean_url(self.url_edit.text())
        if not url.startswith("http"):
            self.status.setText(tr("dl.need_url"))
            return
        self.url_edit.setText(url)
        outdir = self.dir_edit.text() or default_dir(self.store.config)
        if download and self.ask_switch.isChecked():
            picked = QFileDialog.getExistingDirectory(self, tr("dl.pick_location"), outdir)
            if picked:
                outdir = picked

        self._set_busy(True)
        self.bar.setValue(0)
        self.status.setText(tr("dl.downloading"))

        self._thread = QThread()
        self._worker = _Worker(self.store, url, download, outdir,
                               self.cookie_switch.isChecked())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def _on_progress(self, pct):
        self.bar.setValue(int(pct))
        self.status.setText(tr("dl.download_pct", pct=round(pct)))

    def _on_finished(self, info):
        title = info.get("title") or tr("dl.untitled")
        site = info.get("extractor_key") or info.get("extractor") or ""
        fname = os.path.basename(info.get("filename") or info.get("_filename") or "")
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(title))
        self.table.setItem(0, 1, QTableWidgetItem(site))
        self.table.setItem(0, 2, QTableWidgetItem(fname))
        self.bar.setValue(100)
        self.status.setText(tr("dl.saved") + title[:50])
        self._cleanup()

    def _on_failed(self, msg):
        hint = self.store.friendly_error(msg)
        self.status.setText(tr("dl.failed") + f"{msg} {hint}")
        self._cleanup()

    def _cleanup(self):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
        self._set_busy(False)
