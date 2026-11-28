# -*- coding: utf-8 -*-
"""标注数据层测试。"""
from PIL import Image

from kivo.core import annotation as A


def base_img(w=120, h=90):
    return Image.new("RGB", (w, h), "white")


def test_clamp_width():
    assert A.clamp_width(50) == A.WIDTH_MAX
    assert A.clamp_width(0) == A.WIDTH_MIN
    assert A.clamp_width("x") == A.DEFAULT_WIDTH
    assert A.clamp_width(4) == 4


def test_norm_box_reversed():
    assert A.norm_box((10, 20, 5, 8)) == (5, 8, 10, 20)


def test_make_shape_op():
    op = A.make_shape_op("rect", (1, 2, 3, 4), "#FF0000", 3)
    assert op["type"] == "rect" and op["box"] == (1, 2, 3, 4)
    assert A.make_shape_op("bad", (1, 2, 3, 4), "#000", 2) is None


def test_make_pen_op():
    assert A.make_pen_op([(0, 0)], "#000", 2) is None
    op = A.make_pen_op([(0, 0), (1, 1), (2, 2)], "#000", 2)
    assert op["points"] == [(0, 0), (1, 1), (2, 2)]


def test_make_text_op():
    assert A.make_text_op((0, 0), "", "#000", 2) is None
    op = A.make_text_op((5, 5), "hi", "#000", 2)
    assert op["text"] == "hi"


def test_make_seq_op():
    op = A.make_seq_op((10, 10), 3, "#FF0000", 2)
    assert op["n"] == 3


def test_fx_region():
    img = base_img(60, 60)
    assert A.fx_region(img, "mosaic").size == (60, 60)
    assert A.fx_region(img, "blur").size == (60, 60)


def test_render_all_tool_types():
    stack = A.OpStack()
    stack.add(A.make_shape_op("rect", (5, 5, 40, 40), "#FF0000", 3))
    stack.add(A.make_shape_op("ellipse", (5, 5, 40, 40), "#00B050", 2))
    stack.add(A.make_shape_op("line", (5, 5, 40, 40), "#000000", 2))
    stack.add(A.make_shape_op("arrow", (5, 5, 40, 40), "#0070FF", 2))
    stack.add(A.make_shape_op("mosaic", (10, 10, 60, 60), "#000", 2))
    stack.add(A.make_shape_op("blur", (10, 10, 60, 60), "#000", 2))
    stack.add(A.make_pen_op([(0, 0), (20, 20), (40, 10)], "#000", 2))
    stack.add(A.make_text_op((10, 10), "标注", "#000", 2))
    stack.add(A.make_seq_op((50, 50), 1, "#FF0000", 2))
    out = A.render_ops(base_img(), stack.ops)
    assert out.size == (120, 90)
    # 原图不被修改
    assert base_img().getpixel((0, 0)) == (255, 255, 255)


def test_op_stack_undo_redo():
    s = A.OpStack()
    assert s.undo() is False
    s.add(A.make_shape_op("rect", (1, 1, 4, 4), "#000", 2))
    s.add(A.make_shape_op("line", (1, 1, 4, 4), "#000", 2))
    assert len(s.ops) == 2
    assert s.undo() is True and len(s.ops) == 1
    assert s.redo() is True and len(s.ops) == 2
    # 新操作清空重做栈
    s.add(A.make_shape_op("rect", (1, 1, 5, 5), "#000", 2))
    assert s.redo() is False


def test_op_stack_clear_and_seq():
    s = A.OpStack()
    s.add(A.make_seq_op((0, 0), 1, "#000", 2))
    s.add(A.make_seq_op((0, 0), 2, "#000", 2))
    assert s.next_seq_number() == 3
    s.clear()
    assert s.ops == [] and s.undone == []
    assert s.next_seq_number() == 1


def test_add_none_ignored():
    s = A.OpStack()
    assert s.add(None) is False
