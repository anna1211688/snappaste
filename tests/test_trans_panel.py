# -*- coding: utf-8 -*-
"""翻译中心面板测试。"""
import time

import pytest

from kivo.ui.theme import Theme
from kivo.ui.panels.trans_panel import TranslatePanel


class FakeConfig:
    def __init__(self):
        self.sets = []

    def set(self, section, key, value):
        self.sets.append((key, value))


class FakeClient:
    def __init__(self):
        self.config = FakeConfig()
        self.raise_exc = None

    def translate_to(self, text, target, source=None):
        if self.raise_exc:
            raise self.raise_exc
        if not text:
            return ""
        return "译文:" + text


class FakeAI:
    pass


@pytest.fixture
def tp(qapp):
    p = TranslatePanel(Theme(False), FakeClient(), FakeAI())
    p.show()
    qapp.processEvents()
    return p


def _pump(qapp, panel, timeout=3.0):
    end = time.time() + timeout
    while panel.busy and time.time() < end:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


def test_initial(tp):
    assert tp._source_edit.toPlainText() == ""
    assert tp._target_edit.toPlainText() == ""


def test_translate_direct(tp, qapp):
    tp._source_edit.setPlainText("Hello")
    tp.translate_now()
    _pump(qapp, tp)
    assert tp._target_edit.toPlainText() == "译文:Hello"


def test_empty_source_clears(tp, qapp):
    tp._target_edit.setPlainText("旧译文")
    tp._source_edit.setPlainText("")
    tp.translate_now()
    qapp.processEvents()
    assert tp._target_edit.toPlainText() == ""


def test_translate_failure(tp, qapp):
    tp.client.raise_exc = RuntimeError("网络错误")
    tp._source_edit.setPlainText("Hi")
    tp.translate_now()
    _pump(qapp, tp)
    assert "翻译失败" in tp._target_edit.toPlainText()


def test_clear(tp, qapp):
    tp._source_edit.setPlainText("abc")
    tp._clear()
    qapp.processEvents()
    assert tp._source_edit.toPlainText() == ""
    assert tp._target_edit.toPlainText() == ""


def test_copy_target(tp):
    tp._target_edit.setPlainText("结果")
    tp._copy_target()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "结果"


def test_switch_persists(tp):
    tp.ai_switch.findChild(type(tp.ai_switch))  # noop
    sw = tp.mini_switch
    from kivo.ui.components import Switch
    s = sw.findChild(Switch)
    s.setChecked(False)
    assert ("MiniTrans", "0") in tp.client.config.sets


def test_swap_languages(tp):
    # 源设为 English, 目标中文
    tp.source_lang.setCurrentIndex(tp.source_lang.findData("en"))
    tp.target_lang.setCurrentIndex(tp.target_lang.findData("zh-CN"))
    tp._target_edit.setPlainText("你好")
    tp._swap_languages()
    assert tp._source_edit.toPlainText() == "你好"
    assert tp.source_lang.currentData() == "zh-CN"
