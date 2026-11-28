# -*- coding: utf-8 -*-
"""迷你翻译窗: 置顶常驻、可拖动、圆角，原文/译文双框，AI 优先，防抖翻译。"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QComboBox, QTextEdit,
    QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton
from ..icons import icon
from ...core.voice import TRANS_TARGETS


class _Signals(QObject):
    result = Signal(str)
    failed = Signal(str)


class MiniTranslateWindow(QDialog):
    def __init__(self, theme: Theme, translate_client, ai_client, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.client = translate_client
        self.ai = ai_client
        self.busy = False
        self._drag_pos = None

        self.setObjectName("miniRoot")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(400)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        self.card = QFrame()
        self.card.setObjectName("miniCard")
        add_shadow(self.card, blur=28, dy=10, alpha=55)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(0, 0, 0, 12)
        cl.setSpacing(8)

        cl.addWidget(self._title_bar())
        cl.addLayout(self._control())
        cl.addWidget(self._edits())
        cl.addLayout(self._buttons())
        outer.addWidget(self.card)

        self.signals = _Signals()
        self.signals.result.connect(self._on_result)
        self.signals.failed.connect(self._on_failed)

        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(450)
        self.debounce.timeout.connect(self.translate_now)
        self.source_edit.textChanged.connect(self.debounce.start)

    def _title_bar(self):
        bar = QFrame()
        bar.setObjectName("miniTitleBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 8, 10, 8)
        title = QLabel("迷你翻译")
        title.setObjectName("miniTitle")
        lay.addWidget(title)
        lay.addStretch()
        close = QLabel()
        close.setObjectName("miniClose")
        close.setCursor(Qt.PointingHandCursor)
        close.setPixmap(icon("close").pixmap(14, 14))
        close.mousePressEvent = lambda _e: self.hide()
        lay.addWidget(close)
        # 拖动支持
        bar.mousePressEvent = self._begin_drag
        bar.mouseMoveEvent = self._do_drag
        return bar

    def _begin_drag(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _do_drag(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _control(self):
        row = QHBoxLayout()
        row.setContentsMargins(12, 0, 12, 0)
        row.addWidget(QLabel("目标语言"))
        self.target = QComboBox()
        for name, code in TRANS_TARGETS:
            self.target.addItem(name, code)
        self.target.currentIndexChanged.connect(self.translate_now)
        row.addWidget(self.target)
        self.status = QLabel("")
        self.status.setObjectName("miniStatus")
        row.addWidget(self.status)
        row.addStretch()
        return row

    def _edits(self):
        wrap = QFrame()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)
        self.source_edit = QTextEdit()
        self.source_edit.setObjectName("miniEdit")
        self.source_edit.setFixedHeight(90)
        self.target_edit = QTextEdit()
        self.target_edit.setObjectName("miniEdit")
        self.target_edit.setReadOnly(True)
        self.target_edit.setFixedHeight(90)
        lay.addWidget(self.source_edit)
        lay.addWidget(self.target_edit)
        return wrap

    def _buttons(self):
        row = QHBoxLayout()
        row.setContentsMargins(12, 0, 12, 0)
        clear = SecondaryButton("清空", icon_name="trash")
        clear.clicked.connect(self._clear)
        row.addWidget(clear)
        row.addStretch()
        both = SecondaryButton("复制双语", icon_name="copy")
        both.clicked.connect(self._copy_both)
        one = PrimaryButton("复制译文", icon_name="copy")
        one.clicked.connect(self._copy_one)
        row.addWidget(both); row.addWidget(one)
        return row

    def show_with(self, text=None):
        self.show()
        self.raise_(); self.activateWindow()
        if text:
            self.source_edit.setPlainText(text)

    def translate_now(self):
        text = self.source_edit.toPlainText().strip()
        if not text:
            self.target_edit.clear(); self.status.setText(""); return
        if self.busy:
            return
        self.busy = True
        self.status.setText("翻译中…")
        target = self.target.currentData()
        use_ai = (self.client.config.get("Translate", "TTUseAI", fallback="1") or "1") != "0"
        signals = self.signals

        def work():
            try:
                r = None
                if use_ai and self.ai.ready("text"):
                    r = self._ai_translate(text, target)
                if not r:
                    r = self.client.translate_to(text, target)
                if r:
                    signals.result.emit(r)
                else:
                    signals.failed.emit("没拿到译文")
            except Exception as e:
                signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True, name="kivo-mini").start()

    def _ai_translate(self, text, target):
        tgt_name = self.target.currentText()
        prompt = (f"把下面这段文字翻译成{tgt_name}，只输出译文，"
                  "不要加任何解释、引号或原文：\n" + text)
        try:
            r = self.ai.chat_messages(
                [{"role": "user", "content": prompt}],
                route="text", timeout=15, max_tokens=1024)
            return r if r and r.strip() else None
        except Exception:
            return None

    def _on_result(self, text):
        self.busy = False
        self.target_edit.setPlainText(text)
        self.status.setText("")

    def _on_failed(self, msg):
        self.busy = False
        self.status.setText("翻译失败")

    def _clear(self):
        self.source_edit.clear(); self.target_edit.clear(); self.status.setText("")

    def _copy_one(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.target_edit.toPlainText())
        self.status.setText("译文已复制")

    def _copy_both(self):
        from PySide6.QtWidgets import QApplication
        m = self.source_edit.toPlainText() + "\n" + self.target_edit.toPlainText()
        QApplication.clipboard().setText(m)
        self.status.setText("双语已复制")
