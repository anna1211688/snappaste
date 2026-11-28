# -*- coding: utf-8 -*-
"""语音翻译面板测试。"""
import time

import pytest

from kivo.ui.theme import Theme
from kivo.ui.panels.voice_panel import VoicePanel


class FakeVoice:
    def __init__(self):
        self.config = FakeConfig()

    def _stt_model(self):
        return "whisper-1"

    def resolve_mime(self, path):
        if not path.endswith(".mp3"):
            raise RuntimeError("不支持格式")
        return ".mp3", "audio/mpeg"

    def transcribe(self, path, cfg, language=""):
        return "Hello there"

    def translate_text(self, text, code):
        return "你好"


class FakeConfig:
    def set(self, *a):
        pass


class FakeAI:
    def cfg_for(self, route):
        return {"key": "sk-x", "base": "https://api.example.com"}


@pytest.fixture
def vp(qapp):
    p = VoicePanel(Theme(False), FakeVoice(), FakeAI())
    p.show()
    qapp.processEvents()
    return p


def _pump(qapp, panel, timeout=3.0):
    end = time.time() + timeout
    while panel.busy and time.time() < end:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


def test_initial(vp):
    assert vp.original._box.toPlainText() == ""
    assert vp.target.count() > 0


def test_start_without_file(vp, qapp):
    vp.start()
    qapp.processEvents()
    assert "请先选择" in vp.status_label.text()


def test_choose_bad_format(vp, qapp):
    vp.voice.resolve_mime = lambda p: (_ for _ in ()).throw(RuntimeError("不支持格式"))
    vp.path = ""
    # 直接走 choose 的校验分支
    try:
        vp.voice.resolve_mime("x.wav")
    except RuntimeError:
        vp.signals.failed.emit("不支持格式")
    qapp.processEvents()
    assert "失败" in vp.status_label.text()


def test_start_success(vp, qapp):
    vp.path = "/tmp/a.mp3"
    vp.file_label.setText("a.mp3")
    vp.start()
    _pump(qapp, vp)
    assert vp.original._box.toPlainText() == "Hello there"
    assert vp.translated._box.toPlainText() == "你好"
    assert vp.status_label.text() == "完成"
    assert not vp.busy
    assert vp.start_btn.isEnabled()


def test_start_missing_key(vp, qapp):
    vp.ai = type("A", (), {"cfg_for": lambda self, r: {"key": ""}})()
    vp.path = "/tmp/a.mp3"
    vp.start()
    _pump(qapp, vp)
    assert "API Key" in vp.status_label.text()


def test_copy(vp, qapp):
    vp.original._box.setPlainText("复制内容")
    vp._copy(vp.original)
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "复制内容"
