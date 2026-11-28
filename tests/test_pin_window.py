# -*- coding: utf-8 -*-
"""贴图窗口测试。"""
import pytest
from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtGui import QPixmap, QColor, QKeyEvent
from PySide6.QtTest import QTest

from kivo.ui.theme import Theme
from kivo.platform.pin_window import PinWindow, MIN_SCALE, MAX_SCALE


def _pixmap(w=120, h=80):
    pm = QPixmap(w, h)
    pm.fill(QColor("#3478F6"))
    return pm


@pytest.fixture
def pin(qapp):
    closed = []
    w = PinWindow(Theme(False), _pixmap(), on_close=lambda s: closed.append(s))
    w.show()
    qapp.processEvents()
    return w, closed


def test_initial_shows_pixmap(pin):
    w, _ = pin
    assert not w.image_label.pixmap().isNull()
    assert w._scale == 1.0


def test_scale_zoom_in(pin):
    w, _ = pin
    w.scale_at(1.1)
    assert w._scale == pytest.approx(1.1)


def test_scale_clamps(pin):
    w, _ = pin
    w.scale_at(100)
    assert w._scale == MAX_SCALE
    w.scale_at(0.001)
    assert w._scale == MIN_SCALE


def test_rotate_changes_size(pin):
    w, _ = pin
    orig = (w._orig.width(), w._orig.height())
    w.rotate()
    assert (w._orig.width(), w._orig.height()) == (orig[1], orig[0])


def test_copy_to_clipboard(pin, qapp):
    w, _ = pin
    w.copy_to_clipboard()
    assert not qapp.clipboard().pixmap().isNull()


def test_double_click_closes(pin, qapp):
    w, closed = pin
    QTest.mouseDClick(w, Qt.LeftButton, pos=QPoint(10, 10))
    qapp.processEvents()
    assert closed == [w]
    assert not w.isVisible()


def test_escape_closes(pin, qapp):
    w, closed = pin
    w.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
    assert closed == [w]


def test_set_opacity(pin):
    w, _ = pin
    w.set_opacity(0.5)
    assert w.windowOpacity() == pytest.approx(0.5, abs=0.02)


def test_drag_moves_window(pin, qapp):
    w, _ = pin
    before = w.pos()
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(5, 5))
    QTest.mouseMove(w, pos=QPoint(40, 40))
    qapp.processEvents()
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(40, 40))
    # 拖动后窗口位置发生变化（全局坐标偏移）
    assert w.pos() != before
    assert w._drag_pos is None
