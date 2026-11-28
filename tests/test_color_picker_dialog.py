# -*- coding: utf-8 -*-
"""取色器数据层与弹窗测试。"""
import pytest
from PySide6.QtWidgets import QWidget

from kivo.core import paths, color_store
from kivo.core.config import ConfigManager
from kivo.ui.dialogs.color_picker_dialog import ColorPickerDialog


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


@pytest.fixture
def config():
    return ConfigManager()


@pytest.fixture
def parent(qapp):
    return QWidget()


def test_hex_to_rgb():
    assert color_store.hex_to_rgb("#3478F6") == (52, 120, 246)
    assert color_store.hex_to_rgb("#abc") == (170, 187, 204)
    assert color_store.hex_to_rgb("xyz") is None


def test_rgb_to_hsl():
    h, s, l = color_store.rgb_to_hsl(52, 120, 246)
    assert 0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100


def test_color_formats():
    fmts = color_store.color_formats("#3478F6")
    assert fmts["hex"] == "#3478F6"
    assert fmts["rgb"].startswith("rgb(")
    assert fmts["hsl"].startswith("hsl(")
    assert color_store.color_formats("xyzzzz") is None


def test_parse_history():
    import json
    raw = json.dumps(["#3478F6", "#FF0000"])
    hist = color_store.parse_history(raw)
    assert hist == ["#3478F6", "#FF0000"]


def test_parse_bad():
    assert color_store.parse_history("not json") == []


def test_add_to_history():
    hist = color_store.add_to_history([], "#3478F6")
    assert hist[0] == "#3478F6"
    # 重复置顶
    hist = color_store.add_to_history(hist + ["#000000"], "#3478F6")
    assert hist[0] == "#3478F6"
    assert len(hist) == 2


def test_dialog_empty(qapp, parent, config):
    d = ColorPickerDialog(parent, config)
    d.show()
    qapp.processEvents()
    assert d.history == []


def test_dialog_add_picked(qapp, parent, config):
    d = ColorPickerDialog(parent, config)
    d.add_picked("#3478F6")
    qapp.processEvents()
    assert d.history[0] == "#3478F6"
    # 已持久化
    assert config.get("Config", "ColorHistory")


def test_dialog_detail(qapp, parent, config):
    d = ColorPickerDialog(parent, config)
    d.add_picked("#3478F6")
    d._show_detail("#3478F6")
    qapp.processEvents()
    # 详情区有内容
    assert d.detail_lay.count() == 1


def test_pick_screen_callback(qapp, parent, config):
    called = []
    d = ColorPickerDialog(parent, config,
                          pick_screen_callback=lambda: called.append(1))
    d._pick_screen()
    assert called == [1]
