# -*- coding: utf-8 -*-
"""屏幕标尺测试。"""
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent

from kivo.ui.dialogs.ruler_window import RulerWindow, MIN_LEN, MAX_LEN


def _win(qapp):
    w = RulerWindow()
    w.show()
    qapp.processEvents()
    return w


def test_initial_horizontal(qapp):
    w = _win(qapp)
    assert not w.vertical
    assert w.width() == 600 and w.height() == 34


def test_toggle_orientation(qapp):
    w = _win(qapp)
    w._toggle_orientation()
    assert w.vertical
    assert w.width() == 34 and w.height() == 600


def test_length_clamp(qapp):
    w = _win(qapp)
    w._set_length(MAX_LEN + 500)
    assert w.length == MAX_LEN
    w._set_length(MIN_LEN - 500)
    assert w.length == MIN_LEN


def test_length_step(qapp):
    w = _win(qapp)
    w._set_length(600)
    assert w.length == 600
    w._set_length(650)
    assert w.length == 650


def test_keyboard_escape(qapp):
    w = _win(qapp)
    ev = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    w.keyPressEvent(ev)
    qapp.processEvents()
    assert not w.isVisible()


def test_keyboard_resize(qapp):
    w = _win(qapp)
    w._set_length(600)
    w.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Plus, Qt.NoModifier))
    assert w.length == 650
    w.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Minus, Qt.NoModifier))
    assert w.length == 600


def test_render_grab(qapp):
    w = _win(qapp)
    pm = w.grab()
    assert not pm.isNull()


def test_vertical_render(qapp):
    w = _win(qapp)
    w._toggle_orientation()
    pm = w.grab()
    assert not pm.isNull()
