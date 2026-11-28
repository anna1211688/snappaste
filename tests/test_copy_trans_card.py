# -*- coding: utf-8 -*-
"""复制即译结果卡测试。"""
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from kivo.ui.theme import Theme
from kivo.ui.dialogs.copy_trans_card import CopyTransCard


def _wait(qapp, cond, tries=200):
    for _ in range(tries):
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.01)
    qapp.processEvents()
    return cond()


def _make(qapp, translator):
    card = CopyTransCard(Theme(False), translator, target="英语")
    card.show()
    qapp.processEvents()
    return card


def test_initial_state(qapp):
    card = _make(qapp, lambda t: "x")
    assert card.tran_label.text() == "翻译中…"
    assert card.isVisible()


def test_show_at_fills_result(qapp):
    card = _make(qapp, lambda t: "你好世界")
    card.show_at("Hello world", 100, 100)
    assert _wait(qapp, lambda: card.tran_label.text() == "你好世界")
    assert card.orig_label.text() == "Hello world"


def test_show_at_failure(qapp):
    def fail(t):
        raise RuntimeError("boom")
    card = _make(qapp, fail)
    card.show_at("Hi", 10, 10)
    assert _wait(qapp, lambda: card.tran_label.objectName() == "ctFail")
    assert "boom" in card.tran_label.text()


def test_none_result_is_failure(qapp):
    card = _make(qapp, lambda t: None)
    card.show_at("Hi", 10, 10)
    assert _wait(qapp, lambda: card.tran_label.objectName() == "ctFail")


def test_copy_one(qapp):
    card = _make(qapp, lambda t: "译文")
    card.show_at("src", 10, 10)
    _wait(qapp, lambda: card.tran_label.text() == "译文")
    card._copy_one()
    assert QApplication.clipboard().text() == "译文"


def test_copy_both(qapp):
    card = _make(qapp, lambda t: "译文")
    card.show_at("原文", 10, 10)
    _wait(qapp, lambda: card.tran_label.text() == "译文")
    card._copy_both()
    assert QApplication.clipboard().text() == "原文\n译文"


def test_place_clamps_to_screen(qapp):
    card = _make(qapp, lambda t: "x")
    screen = QApplication.primaryScreen().availableGeometry()
    card.show_at("很长的内容", screen.right() - 5, screen.bottom() - 5)
    qapp.processEvents()
    assert card.frameGeometry().right() <= screen.right()
    assert card.frameGeometry().bottom() <= screen.bottom()


def test_generation_guard_stale_result(qapp):
    def slow(t):
        time.sleep(0.08)
        return "旧译文"
    card = _make(qapp, slow)
    card.show_at("第一次", 10, 10)
    time.sleep(0.02)
    # 第二次以新内容启动，旧线程回来时 gen 已过期
    card.translator = lambda t: "新译文"
    card.show_at("第二次", 10, 10)
    assert _wait(qapp, lambda: card.tran_label.text() == "新译文")
    assert card.orig_label.text() == "第二次"


def test_escape_closes(qapp):
    card = _make(qapp, lambda t: "x")
    from PySide6.QtGui import QKeyEvent
    ev = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    card.keyPressEvent(ev)
    assert not card.isVisible()


def test_close_stops_timer(qapp):
    card = _make(qapp, lambda t: "x")
    card.show_at("s", 10, 10)
    card.close_card()
    assert not card.auto_close.isActive()
    assert not card.isVisible()
