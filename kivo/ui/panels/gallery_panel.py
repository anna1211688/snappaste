# -*- coding: utf-8 -*-
"""截图历史画廊面板: 网格缩略图、钉图/删除、空状态。

缩略图在后台线程用 QImage 加载与缩放 (QImage 可在非主线程使用), 完成后经
信号回主线程填充, 并按路径缓存, 避免大量图片同步加载卡顿。
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout, QApplication,
)

from ..theme import Theme
from ..components import DangerButton, EmptyState
from ...core import gallery_store
from ...core.i18n import tr

THUMB_W, THUMB_H = 160, 110
COLUMNS = 4


class _ThumbWorker(QObject):
    """后台加载器: 经队列信号在工作线程读取并缩放图片。"""

    loaded = Signal(str, QImage)
    _request = Signal(str, int, int)

    def __init__(self):
        super().__init__()
        # 同对象内信号在 moveToThread 后变为跨线程队列连接
        self._request.connect(self._load)

    def submit(self, path: str, width: int, height: int):
        self._request.emit(path, width, height)

    def _load(self, path: str, width: int, height: int):
        img = QImage(path)
        if not img.isNull():
            img = img.scaled(width, height,
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.loaded.emit(path, img)


class ThumbnailLoader(QObject):
    """管理后台线程与缩略图缓存, 重复请求直接命中。"""

    ready = Signal(str, QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache: dict[str, QImage] = {}
        # 线程不挂 Qt parent: 避免加载器随面板被销毁时强删仍在运行的线程
        self._thread = QThread()
        self._worker = _ThumbWorker()
        self._worker.moveToThread(self._thread)
        self._worker.loaded.connect(self._on_loaded)
        self._thread.start()

    def request(self, path: str, width: int, height: int):
        cached = self._cache.get(path)
        if cached is not None:
            self.ready.emit(path, cached)
            return
        self._worker.submit(path, width, height)

    def _on_loaded(self, path: str, img: QImage):
        self._cache[path] = img
        self.ready.emit(path, img)

    def shutdown(self):
        thread = getattr(self, "_thread", None)
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait()

    def __del__(self):
        # 面板被回收（含测试结束）时确保后台线程已退出, 防止运行中线程被销毁
        self.shutdown()


class GalleryPanel(QWidget):
    def __init__(self, theme: Theme, shots_dir, pin_callback=None,
                 screenshot_callback=None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.shots_dir = shots_dir
        self.pin_callback = pin_callback
        self.screenshot_callback = screenshot_callback
        self._thumb_labels: dict[str, QLabel] = {}

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

        self.loader = ThumbnailLoader(self)
        self.loader.ready.connect(self._on_thumb)
        # 应用退出时确保后台线程被正确回收
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.loader.shutdown)

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
        self._thumb_labels.clear()

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
        # 异步加载: 先占位, 后台完成后再填充
        self._thumb_labels[path] = img
        self.loader.request(path, THUMB_W, THUMB_H)
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

    def _on_thumb(self, path: str, img: QImage):
        label = self._thumb_labels.get(path)
        if label is not None:
            label.setPixmap(QPixmap.fromImage(img))

    def _pin(self, name):
        if self.pin_callback:
            self.pin_callback(name)

    def _delete_one(self, name):
        gallery_store.delete_file(self.shots_dir, name)
        self.refresh()

    def _delete_all(self):
        gallery_store.delete_all(self.shots_dir)
        self.refresh()
