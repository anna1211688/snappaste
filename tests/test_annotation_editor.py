# -*- coding: utf-8 -*-
"""标注编辑器窗口测试。"""
from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from kivo.ui.theme import Theme
from kivo.ui.dialogs.annotation_editor import (
    AnnotationEditor, TOOL_LABELS,
)


def _editor(callbacks=None, size=(200, 160)):
    img = Image.new("RGB", size, "white")
    return AnnotationEditor(img, Theme(False), callbacks=callbacks)


def test_construct(qapp):
    ed = _editor()
    assert len(ed.tool_group.buttons()) == len(TOOL_LABELS)
    assert len(ed.color_group.buttons()) == 6
    assert ed.canvas.pixmap() is not None
    assert ed.current_tool == "rect"


def test_drag_adds_rect(qapp):
    ed = _editor()
    c = ed.canvas
    QTest.mousePress(c, Qt.LeftButton, pos=QPoint(20, 20))
    QTest.mouseMove(c, QPoint(80, 60))
    QTest.mouseRelease(c, Qt.LeftButton, pos=QPoint(80, 60))
    assert len(ed.stack.ops) == 1
    assert ed.stack.ops[0]["type"] == "rect"
    assert ed.stack.ops[0]["box"] == (20, 20, 80, 60)


def test_switch_tool_pen(qapp):
    ed = _editor()
    ed._set_tool("pen")
    assert ed.current_tool == "pen"
    c = ed.canvas
    QTest.mousePress(c, Qt.LeftButton, pos=QPoint(10, 10))
    QTest.mouseMove(c, QPoint(30, 40))
    QTest.mouseMove(c, QPoint(50, 50))
    QTest.mouseRelease(c, Qt.LeftButton, pos=QPoint(50, 50))
    assert ed.stack.ops[0]["type"] == "pen"
    assert len(ed.stack.ops[0]["points"]) >= 2


def test_seq_tool_immediate(qapp):
    ed = _editor()
    ed._set_tool("seq")
    QTest.mousePress(ed.canvas, Qt.LeftButton, pos=QPoint(40, 40))
    QTest.mouseRelease(ed.canvas, Qt.LeftButton, pos=QPoint(40, 40))
    assert ed.stack.ops[0]["type"] == "seq"
    assert ed.stack.ops[0]["n"] == 1


def test_undo_redo(qapp):
    ed = _editor()
    c = ed.canvas
    QTest.mousePress(c, Qt.LeftButton, pos=QPoint(10, 10))
    QTest.mouseRelease(c, Qt.LeftButton, pos=QPoint(50, 50))
    assert len(ed.stack.ops) == 1
    ed._undo()
    assert len(ed.stack.ops) == 0
    ed._redo()
    assert len(ed.stack.ops) == 1


def test_clear(qapp):
    ed = _editor()
    c = ed.canvas
    QTest.mousePress(c, Qt.LeftButton, pos=QPoint(10, 10))
    QTest.mouseRelease(c, Qt.LeftButton, pos=QPoint(50, 50))
    ed._clear()
    assert ed.stack.ops == []


def test_switch_color(qapp):
    ed = _editor()
    ed._set_color("#0070FF")
    assert ed.current_color == "#0070FF"


def test_result_image(qapp):
    ed = _editor()
    out = ed.result_image()
    assert out.size == (200, 160)


def test_finish_pin_callback(qapp):
    received = []
    ed = _editor(callbacks={"pin": lambda im: received.append(im)})
    ed._finish("pin")
    assert len(received) == 1
    assert received[0].size == (200, 160)


def test_discard_callback(qapp):
    discarded = []
    ed = _editor(callbacks={"discard": lambda: discarded.append(True)})
    ed._discard()
    assert discarded == [True]


def test_ocr_callback(qapp):
    got = []
    ed = _editor(callbacks={"ocr": lambda im: got.append(im)})
    ed._invoke("ocr")
    assert len(got) == 1


def test_large_image_scaled(qapp):
    ed = _editor(size=(2000, 1400))
    assert ed.scale < 1.0
    assert ed.canvas.width() <= 1500
