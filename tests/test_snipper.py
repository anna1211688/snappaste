# -*- coding: utf-8 -*-
"""截图覆盖层测试。"""
import pytest
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtTest import QTest

from kivo.ui.theme import Theme
from kivo.platform.snipper import SnipperOverlay


@pytest.fixture
def overlay(qapp):
    picked, cancelled = [], []
    ov = SnipperOverlay(Theme(False),
                        on_pick=lambda r: picked.append(r),
                        on_cancel=lambda: cancelled.append(1))
    ov.setGeometry(QRect(0, 0, 800, 600))
    ov.show()
    qapp.processEvents()
    return ov, picked, cancelled


def _drag(ov, p1, p2):
    QTest.mousePress(ov, Qt.LeftButton, pos=p1)
    QTest.mouseMove(ov, pos=p2)
    QTest.mouseRelease(ov, Qt.LeftButton, pos=p2)


def test_drag_produces_selection(overlay, qapp):
    ov, picked, _ = overlay
    _drag(ov, QPoint(100, 100), QPoint(300, 250))
    qapp.processEvents()
    assert len(picked) == 1
    assert picked[0] == (100, 100, 300, 250)


def test_reverse_drag_normalized(overlay, qapp):
    ov, picked, _ = overlay
    _drag(ov, QPoint(300, 250), QPoint(100, 100))
    qapp.processEvents()
    assert picked[0] == (100, 100, 300, 250)


def test_tiny_selection_ignored(overlay, qapp):
    ov, picked, _ = overlay
    _drag(ov, QPoint(100, 100), QPoint(101, 101))
    qapp.processEvents()
    assert picked == []


def test_escape_cancels(overlay, qapp):
    ov, _picked, cancelled = overlay
    QTest.keyClick(ov, Qt.Key_Escape)
    qapp.processEvents()
    assert cancelled == [1]


def test_paint_does_not_raise(overlay, qapp):
    ov, _p, _c = overlay
    QTest.mousePress(ov, Qt.LeftButton, pos=QPoint(50, 50))
    QTest.mouseMove(ov, pos=QPoint(200, 150))
    qapp.processEvents()
    pix = ov.grab()  # 触发 paintEvent
    assert not pix.isNull()


def test_release_without_press_noop(overlay, qapp):
    ov, picked, _ = overlay
    QTest.mouseRelease(ov, Qt.LeftButton, pos=QPoint(300, 300))
    qapp.processEvents()
    assert picked == []
