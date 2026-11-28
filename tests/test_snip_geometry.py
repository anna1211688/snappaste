# -*- coding: utf-8 -*-
"""截图几何纯逻辑测试。"""
from kivo.platform.snip_geometry import (
    normalize_rect, clamp_rect, rect_size, valid_selection, pick_window,
    MIN_SELECT,
)


def test_normalize_forward():
    assert normalize_rect(10, 20, 100, 200) == (10, 20, 100, 200)


def test_normalize_reverse_drag():
    # 从右下往左上拖
    assert normalize_rect(100, 200, 10, 20) == (10, 20, 100, 200)


def test_normalize_mixed_axes():
    assert normalize_rect(100, 20, 10, 200) == (10, 20, 100, 200)


def test_clamp_within_bounds():
    assert clamp_rect((10, 10, 50, 50), 100, 100) == (10, 10, 50, 50)


def test_clamp_out_of_bounds():
    assert clamp_rect((-20, -10, 150, 120), 100, 80) == (0, 0, 100, 80)


def test_rect_size():
    assert rect_size((0, 0, 100, 40)) == (100, 40)


def test_valid_selection_ok():
    assert valid_selection((0, 0, 50, 50)) is True


def test_invalid_too_small():
    assert valid_selection((0, 0, MIN_SELECT - 1, 50)) is False
    assert valid_selection((0, 0, 0, 0)) is False


def test_pick_window_single():
    rects = [(0, 0, 500, 500)]
    assert pick_window(100, 100, rects) == (0, 0, 500, 500)


def test_pick_window_smallest():
    rects = [(0, 0, 500, 500), (50, 50, 200, 200)]
    assert pick_window(100, 100, rects) == (50, 50, 200, 200)


def test_pick_window_none():
    rects = [(0, 0, 100, 100)]
    assert pick_window(200, 200, rects) is None


def test_pick_window_ignores_degenerate():
    rects = [(0, 0, 0, 0)]
    assert pick_window(0, 0, rects) is None
