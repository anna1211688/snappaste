# -*- coding: utf-8 -*-
"""迷你翻译窗测试。"""
import time

from kivo.ui.theme import Theme
from kivo.ui.panels.mini_trans_panel import MiniTranslateWindow


class FakeConfig:
    def get(self, section, key, fallback=None):
        return fallback

    def set(self, section, key, value):
        pass

    def save(self):
        pass


class FakeClient:
    def __init__(self):
        self.config = FakeConfig()

    def translate_to(self, text, target, source=None):
        return "译:" + text if text else ""


class FakeAI:
    def __init__(self, ready=False, reply=None):
        self._ready = ready
        self._reply = reply

    def ready(self, route=None):
        return self._ready

    def chat_messages(self, messages, **kw):
        if self._reply is None:
            raise RuntimeError("x")
        return self._reply


def _pump(qapp, win, timeout=3.0):
    end = time.time() + timeout
    while win.busy and time.time() < end:
        qapp.processEvents(); time.sleep(0.01)
    qapp.processEvents()


def _win(qapp, ai=None):
    w = MiniTranslateWindow(Theme(False), FakeClient(), ai or FakeAI())
    w.show(); qapp.processEvents()
    return w


def test_render(qapp):
    w = _win(qapp)
    assert w.target.count() > 5


def test_translate_online(qapp):
    w = _win(qapp)
    w.source_edit.setPlainText("Hello")
    w.translate_now()
    _pump(qapp, w)
    assert w.target_edit.toPlainText() == "译:Hello"


def test_ai_first(qapp):
    w = _win(qapp, FakeAI(ready=True, reply="AI结果"))
    w.source_edit.setPlainText("Hi")
    w.translate_now()
    _pump(qapp, w)
    assert w.target_edit.toPlainText() == "AI结果"


def test_clear(qapp):
    w = _win(qapp)
    w.source_edit.setPlainText("abc")
    w._clear()
    assert w.source_edit.toPlainText() == ""
    assert w.target_edit.toPlainText() == ""


def test_copy_one(qapp):
    w = _win(qapp)
    w.target_edit.setPlainText("结果")
    w._copy_one()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "结果"


def test_copy_both(qapp):
    w = _win(qapp)
    w.source_edit.setPlainText("原文")
    w.target_edit.setPlainText("译文")
    w._copy_both()
    from PySide6.QtWidgets import QApplication
    clip = QApplication.clipboard().text()
    assert "原文" in clip and "译文" in clip


def test_hide_on_close(qapp):
    w = _win(qapp)
    assert w.isVisible()
    w.hide()
    assert not w.isVisible()


def test_show_with(qapp):
    w = _win(qapp)
    w.hide()
    w.show_with("预填")
    qapp.processEvents()
    assert w.isVisible()
    assert w.source_edit.toPlainText() == "预填"
