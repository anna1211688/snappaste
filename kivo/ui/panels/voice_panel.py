# -*- coding: utf-8 -*-
"""语音翻译面板: 选择音频 → 后台转写并翻译 → 原文/译文双结果卡。"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QComboBox, QLineEdit, QVBoxLayout,
    QHBoxLayout, QTextEdit, QFileDialog,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton, MutedLabel
from ...core.i18n import tr
from ...core.voice import TRANS_TARGETS


class _Signals(QObject):
    status = Signal(str)
    done = Signal(str, str)
    failed = Signal(str)


class VoicePanel(QWidget):
    def __init__(self, theme: Theme, voice_client, ai_client):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.voice = voice_client
        self.ai = ai_client
        self.path = ""
        self.busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        title = QLabel(tr("voice.title"))
        title.setObjectName("hero")
        sub = MutedLabel(tr("voice.sub"))
        root.addWidget(title)
        root.addWidget(sub)

        root.addWidget(self._file_card())
        self.original = self._result_block(tr("voice.original"))
        self.translated = self._result_block(tr("voice.translated"))
        root.addWidget(self.original, 1)
        root.addWidget(self.translated, 1)

        self.signals = _Signals()
        self.signals.status.connect(self.status_label.setText)
        self.signals.done.connect(self._on_done)
        self.signals.failed.connect(self._on_failed)

    def _file_card(self):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=22, alpha=28)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        r1 = QHBoxLayout()
        pick = SecondaryButton(tr("voice.pick"), icon_name="folder-open")
        pick.clicked.connect(self.choose)
        self.file_label = QLabel(tr("voice.no_file"))
        self.file_label.setObjectName("mutedLabel")
        r1.addWidget(pick)
        r1.addWidget(self.file_label, 1)
        lay.addLayout(r1)

        fmt = MutedLabel(tr("voice.fmt"))
        fmt.setWordWrap(True)
        lay.addWidget(fmt)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel(tr("voice.target")))
        self.target = QComboBox()
        for name, _code in TRANS_TARGETS:
            self.target.addItem(name)
        r2.addWidget(self.target)
        r2.addSpacing(12)
        r2.addWidget(QLabel(tr("voice.model")))
        self.model = QLineEdit(voice_stt_model(self.voice))
        self.model.setFixedWidth(180)
        r2.addWidget(self.model)
        r2.addSpacing(12)
        r2.addWidget(QLabel(tr("voice.source")))
        self.language = QLineEdit()
        self.language.setFixedWidth(90)
        r2.addWidget(self.language)
        r2.addStretch()
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.start_btn = PrimaryButton(tr("voice.start"), icon_name="voice")
        self.start_btn.clicked.connect(self.start)
        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedLabel")
        r3.addWidget(self.start_btn)
        r3.addWidget(self.status_label, 1)
        lay.addLayout(r3)
        return card

    def _result_block(self, title):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=18, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        head = QLabel(title)
        head.setObjectName("blockHead")
        copy = SecondaryButton(tr("common.copy"), icon_name="copy")
        copy.clicked.connect(lambda: self._copy(card))
        top.addWidget(head)
        top.addStretch()
        top.addWidget(copy)
        lay.addLayout(top)

        box = QTextEdit()
        box.setObjectName("resultBox")
        box.setReadOnly(True)
        box.setPlaceholderText(tr("voice.result_ph"))
        lay.addWidget(box)
        card._box = box
        return card

    def _copy(self, card):
        text = card._box.toPlainText()
        if text:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.signals.status.emit(tr("voice.copied"))

    # ---------- 交互 ----------
    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("voice.pick"))
        if not path:
            return
        try:
            self.voice.resolve_mime(path)
        except RuntimeError as e:
            self.signals.failed.emit(str(e))
            return
        self.path = path
        import os
        self.file_label.setText(os.path.basename(path))

    def start(self):
        if self.busy:
            return
        if not self.path:
            self.signals.failed.emit(tr("voice.no_file_err"))
            return
        self.busy = True
        self.start_btn.setEnabled(False)
        self.status_label.setText(tr("voice.uploading"))
        code = TRANS_TARGETS[self.target.currentIndex()][1]
        language = self.language.text().strip()[:10]
        self.voice.config.set("AI", "VoiceModel", self.model.text().strip())
        signals = self.signals

        def work():
            try:
                cfg = self.ai.cfg_for("voice")
                if not cfg.get("key"):
                    raise RuntimeError(tr("voice.no_key"))
                original = self.voice.transcribe(self.path, cfg, language=language)
                signals.status.emit(tr("voice.translating"))
                translated = self.voice.translate_text(original, code)
                signals.done.emit(original, translated)
            except Exception as e:
                signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True, name="kivo-voice").start()

    def _on_done(self, original, translated):
        self.busy = False
        self.start_btn.setEnabled(True)
        self.original._box.setPlainText(original)
        self.translated._box.setPlainText(translated)
        self.status_label.setText(tr("voice.done"))

    def _on_failed(self, msg):
        self.busy = False
        self.start_btn.setEnabled(True)
        self.status_label.setText(tr("voice.failed") + msg)


def voice_stt_model(voice_client):
    try:
        return voice_client._stt_model()
    except Exception:
        return "whisper-1"
