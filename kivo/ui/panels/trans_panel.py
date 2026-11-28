# -*- coding: utf-8 -*-
"""翻译中心面板: 双栏原文/译文、语言切换、AI/迷你/复制开关、防抖自动翻译。"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QTextEdit,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, Switch,
)
from ...core.i18n import tr
from ...core.voice import TRANS_TARGETS


class _Signals(QObject):
    result = Signal(str)
    failed = Signal(str)


class TranslatePanel(QWidget):
    def __init__(self, theme: Theme, translate_client, ai_client):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.client = translate_client
        self.ai = ai_client
        self.busy = False
        self._swapping = False
        self._switches = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(tr("trans.title"))
        title.setObjectName("hero")
        root.addWidget(title)

        root.addLayout(self._control_row())
        root.addWidget(self._columns(), 1)
        root.addLayout(self._button_row())

        self.signals = _Signals()
        self.signals.result.connect(self._on_result)
        self.signals.failed.connect(self._on_failed)

        # 停笔 350ms 防抖
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(350)
        self.debounce.timeout.connect(self.translate_now)
        self._source_edit.textChanged.connect(lambda: self.debounce.start())

    # ---------- 控制行 ----------
    def _control_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("trans.source")))
        self.source_lang = QComboBox()
        self.source_lang.addItem(tr("trans.auto"), None)
        for name, code in TRANS_TARGETS:
            self.source_lang.addItem(name, code)
        self.source_lang.currentIndexChanged.connect(self.translate_now)
        row.addWidget(self.source_lang)

        swap = QLabel("⇄")
        swap.setObjectName("swapIcon")
        swap.setCursor(Qt.PointingHandCursor)
        swap.mousePressEvent = lambda _e: self._swap_languages()
        row.addWidget(swap)

        row.addWidget(QLabel(tr("trans.target")))
        self.target_lang = QComboBox()
        for name, code in TRANS_TARGETS:
            self.target_lang.addItem(name, code)
        self.target_lang.setCurrentIndex(0)
        self.target_lang.currentIndexChanged.connect(self.translate_now)
        row.addWidget(self.target_lang)

        row.addSpacing(16)
        self.ai_switch = self._labelled_switch(tr("trans.use_ai"), "TTUseAI", True)
        self.mini_switch = self._labelled_switch(tr("trans.use_mini"), "MiniTrans", True)
        self.copy_switch = self._labelled_switch(tr("trans.use_copy"), "CopyTrans", True)
        row.addWidget(self.ai_switch)
        row.addWidget(self.mini_switch)
        row.addWidget(self.copy_switch)
        row.addStretch()
        return row

    def _labelled_switch(self, label, cfg_key, default):
        holder = QWidget()
        h = QHBoxLayout(holder)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        sw = Switch(default)
        sw._on_color = self.theme.tokens["accent"]
        sw.toggled.connect(lambda on, k=cfg_key: self._save_switch(k, on))
        self._switches[cfg_key] = sw
        lab = QLabel(label)
        h.addWidget(sw)
        h.addWidget(lab)
        return holder

    def _save_switch(self, key, on):
        self.client.config.set("Translate", key, "1" if on else "0")
        self.client.config.save()

    # ---------- 双栏 ----------
    def _columns(self):
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self.source_box = self._edit_card(tr("trans.source_text"), readonly=False)
        self.target_box = self._edit_card(tr("trans.target_text"), readonly=True)
        h.addWidget(self.source_box, 1)
        h.addWidget(self.target_box, 1)
        return wrap

    def _edit_card(self, title, readonly):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=20, alpha=24)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        head = QLabel(title)
        head.setObjectName("blockHead")
        lay.addWidget(head)
        box = QTextEdit()
        box.setObjectName("transBox")
        box.setReadOnly(readonly)
        lay.addWidget(box)
        if readonly:
            self._target_edit = box
        else:
            self._source_edit = box
        return card

    # ---------- 按钮行 ----------
    def _button_row(self):
        row = QHBoxLayout()
        paste = SecondaryButton(tr("trans.paste"), icon_name="copy")
        paste.clicked.connect(self._paste)
        clear = SecondaryButton(tr("common.clear"), icon_name="trash")
        clear.clicked.connect(self._clear)
        copy_both = SecondaryButton(tr("trans.copy_both"), icon_name="copy")
        copy_both.clicked.connect(self._copy_both)
        copy_t = PrimaryButton(tr("trans.copy_target"), icon_name="copy")
        copy_t.clicked.connect(self._copy_target)
        row.addWidget(paste)
        row.addWidget(clear)
        row.addStretch()
        row.addWidget(copy_both)
        row.addWidget(copy_t)
        return row

    # ---------- 动作 ----------
    def _paste(self):
        from PySide6.QtWidgets import QApplication
        self._source_edit.setPlainText(QApplication.clipboard().text())

    def _clear(self):
        self._source_edit.clear()
        self._target_edit.clear()

    def _copy_target(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._target_edit.toPlainText())

    def _copy_both(self):
        from PySide6.QtWidgets import QApplication
        both = self._source_edit.toPlainText() + "\n" + self._target_edit.toPlainText()
        QApplication.clipboard().setText(both)

    def _swap_languages(self):
        src_code = self.source_lang.currentData()
        if src_code is None:
            return
        tgt_code = self.target_lang.currentData()
        src_text = self._source_edit.toPlainText()
        tgt_text = self._target_edit.toPlainText()

        self._swapping = True
        idx = self.source_lang.findData(tgt_code)
        if idx >= 0:
            self.source_lang.setCurrentIndex(idx)
        idx = self.target_lang.findData(src_code)
        if idx >= 0:
            self.target_lang.setCurrentIndex(idx)
        self._swapping = False

        # 译文变原文，原文变译文
        self._source_edit.setPlainText(tgt_text)
        self._target_edit.setPlainText(src_text)

    # ---------- 翻译 ----------
    def translate_now(self):
        if self._swapping:
            return
        text = self._source_edit.toPlainText().strip()
        if not text:
            self._target_edit.clear()
            return
        if self.busy:
            return
        self.busy = True
        target = self.target_lang.currentData()
        source = self.source_lang.currentData()
        signals = self.signals

        use_ai = self._switches["TTUseAI"].isChecked()

        def work():
            try:
                r = None
                # 勾了 AI 且配了 key：先 AI（懂上下文），失败/空再回退在线通道
                if use_ai and self.ai.ready("text"):
                    r = self._ai_translate(text, target, source)
                if not r:
                    r = self.client.translate_to(text, target, source)
                if r:
                    signals.result.emit(r)
                else:
                    signals.failed.emit(tr("trans.no_result"))
            except Exception as e:
                signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True, name="kivo-trans").start()

    def _ai_translate(self, text, target, source):
        tgt_name = self.target_lang.currentText()
        src_hint = ""
        if source:
            src_hint = f"原文是{self.source_lang.currentText()}，"
        prompt = (f"{src_hint}把下面这段文字翻译成{tgt_name}，"
                  "只输出译文，不要加任何解释、引号或原文：\n" + text)
        try:
            r = self.ai.chat_messages(
                [{"role": "user", "content": prompt}],
                route="text", timeout=15, max_tokens=1024)
            return r if r and r.strip() else None
        except Exception:
            return None

    def _on_result(self, text):
        self.busy = False
        self._target_edit.setPlainText(text)

    def _on_failed(self, msg):
        self.busy = False
        self._target_edit.setPlainText(tr("trans.failed") + " " + msg)
