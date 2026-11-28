# -*- coding: utf-8 -*-
"""语音翻译面板: 选择音频 → 后台转写并翻译 → 原文/译文双结果卡。"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QComboBox, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTextEdit, QFileDialog,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, SecondaryButton, SectionHeader, MutedLabel
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

        title = QLabel("语音翻译")
        title.setObjectName("hero")
        sub = MutedLabel("选择聊天软件导出的语音消息，自动转写成文字再翻译成目标语言。")
        root.addWidget(title)
        root.addWidget(sub)

        root.addWidget(self._file_card())
        self.original = self._result_block("原文（转写）")
        self.translated = self._result_block("译文")
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
        pick = SecondaryButton("选择音频文件")
        pick.clicked.connect(self.choose)
        self.file_label = QLabel("未选择文件")
        self.file_label.setObjectName("mutedLabel")
        r1.addWidget(pick)
        r1.addWidget(self.file_label, 1)
        lay.addLayout(r1)

        fmt = MutedLabel("支持 OGG/Opus、M4A/AAC、MP3、WAV、WEBM、FLAC、AAC 等，单个不超过 25 MB。")
        fmt.setWordWrap(True)
        lay.addWidget(fmt)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("目标语言"))
        self.target = QComboBox()
        for name, _code in TRANS_TARGETS:
            self.target.addItem(name)
        r2.addWidget(self.target)
        r2.addSpacing(12)
        r2.addWidget(QLabel("转写模型"))
        self.model = QLineEdit(voice_stt_model(self.voice))
        self.model.setFixedWidth(180)
        r2.addWidget(self.model)
        r2.addSpacing(12)
        r2.addWidget(QLabel("源语言(可选)"))
        self.language = QLineEdit()
        self.language.setFixedWidth(90)
        r2.addWidget(self.language)
        r2.addStretch()
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.start_btn = PrimaryButton("开始转写翻译")
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
        copy = SecondaryButton("复制")
        copy.clicked.connect(lambda: self._copy(card))
        top.addWidget(head)
        top.addStretch()
        top.addWidget(copy)
        lay.addLayout(top)

        box = QTextEdit()
        box.setObjectName("resultBox")
        box.setReadOnly(True)
        box.setPlaceholderText("结果将显示在这里")
        lay.addWidget(box)
        card._box = box
        return card

    def _copy(self, card):
        text = card._box.toPlainText()
        if text:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.signals.status.emit("已复制")

    # ---------- 交互 ----------
    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择音频文件")
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
            self.signals.failed.emit("请先选择一个音频文件。")
            return
        self.busy = True
        self.start_btn.setEnabled(False)
        self.status_label.setText("正在上传并转写语音…")
        code = TRANS_TARGETS[self.target.currentIndex()][1]
        language = self.language.text().strip()[:10]
        self.voice.config.set("AI", "VoiceModel", self.model.text().strip())
        signals = self.signals

        def work():
            try:
                cfg = self.ai.cfg_for("voice")
                if not cfg.get("key"):
                    raise RuntimeError("还没填 AI 接口的 API Key：到「设置 → AI 模型中心」选服务、填 key。")
                original = self.voice.transcribe(self.path, cfg, language=language)
                signals.status.emit("正在翻译…")
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
        self.status_label.setText("完成")

    def _on_failed(self, msg):
        self.busy = False
        self.start_btn.setEnabled(True)
        self.status_label.setText("失败：" + msg)


def voice_stt_model(voice_client):
    try:
        return voice_client._stt_model()
    except Exception:
        return "whisper-1"
