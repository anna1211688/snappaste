# -*- coding: utf-8 -*-
"""复制即译结果卡: 光标旁无边框置顶小窗，AI 优先翻译，20 秒自动关闭。"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton
from ..icons import icon

AUTO_CLOSE_MS = 20_000


class _Signals(QObject):
    result = Signal(str)
    failed = Signal(str)


class CopyTransCard(QDialog):
    def __init__(self, theme: Theme, translator, target="", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.translator = translator  # callable(text) -> str | None
        self.target = target
        self._gen = 0
        self._orig = ""

        self.setObjectName("ctRoot")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(340)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self.card = QFrame()
        self.card.setObjectName("ctCard")
        add_shadow(self.card, blur=26, dy=8, alpha=50)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(0, 0, 0, 12)
        cl.setSpacing(6)

        cl.addWidget(self._title_bar())
        self.orig_label = QLabel()
        self.orig_label.setObjectName("ctOrig")
        self.orig_label.setWordWrap(True)
        cl.addWidget(self.orig_label)
        self.tran_label = QLabel("翻译中…")
        self.tran_label.setObjectName("ctTrans")
        self.tran_label.setWordWrap(True)
        cl.addWidget(self.tran_label)
        cl.addLayout(self._buttons())
        outer.addWidget(self.card)

        self.signals = _Signals()
        self.signals.result.connect(self._fill)
        self.signals.failed.connect(self._on_fail)

        self.auto_close = QTimer(self)
        self.auto_close.setSingleShot(True)
        self.auto_close.setInterval(AUTO_CLOSE_MS)
        self.auto_close.timeout.connect(self.close_card)

    def _title_bar(self):
        bar = QFrame()
        bar.setObjectName("ctTitleBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 10, 10, 6)
        title = QLabel("复制即译")
        title.setObjectName("ctTitle")
        lay.addWidget(title)
        lay.addStretch()
        close = QLabel()
        close.setObjectName("ctClose")
        close.setCursor(Qt.PointingHandCursor)
        close.setPixmap(icon("close").pixmap(14, 14))
        close.mousePressEvent = lambda _e: self.close_card()
        lay.addWidget(close)
        return bar

    def _buttons(self):
        row = QHBoxLayout()
        row.setContentsMargins(14, 4, 14, 0)
        row.addStretch()
        both = SecondaryButton("复制双语", icon_name="copy")
        both.clicked.connect(self._copy_both)
        one = PrimaryButton("复制译文", icon_name="copy")
        one.clicked.connect(self._copy_one)
        row.addWidget(both); row.addWidget(one)
        return row

    def show_at(self, orig, x, y):
        self._orig = orig
        self._gen += 1
        gen = self._gen
        self.orig_label.setText(orig)
        self.tran_label.setText("翻译中…")
        self.tran_label.setObjectName("ctTrans")
        self._restyle(self.tran_label)
        self.show()
        self.raise_(); self.activateWindow()
        self._place(x, y)
        self.auto_close.start()
        translator = self.translator
        signals = self.signals

        def work():
            try:
                r = translator(orig)
                if gen != self._gen:
                    return
                if r:
                    signals.result.emit(r)
                else:
                    signals.failed.emit("翻译失败：检查网络后重试")
            except Exception as e:
                if gen == self._gen:
                    signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True, name="kivo-copytrans").start()

    def _place(self, x, y):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        w, h = self.width(), self.height()
        nx = max(screen.left() + 4, min(x + 12, screen.right() - w - 4))
        ny = max(screen.top() + 4, min(y + 16, screen.bottom() - h - 4))
        self.move(nx, ny)

    def _fill(self, text):
        self.tran_label.setText(text)

    def _on_fail(self, msg):
        self.tran_label.setText(msg)
        self.tran_label.setObjectName("ctFail")
        self._restyle(self.tran_label)

    def _copy_one(self):
        QApplication.clipboard().setText(self.tran_label.text())

    def _copy_both(self):
        m = self._orig + "\n" + self.tran_label.text()
        QApplication.clipboard().setText(m)

    def close_card(self):
        self.auto_close.stop()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_card()
        else:
            super().keyPressEvent(event)

    @staticmethod
    def _restyle(w):
        w.style().unpolish(w); w.style().polish(w)
