# -*- coding: utf-8 -*-
"""热键设置弹窗测试。"""
import pytest
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget, QPushButton

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.ui.theme import Theme
from kivo.ui.dialogs.hotkey_dialog import HotkeyDialog, HotkeyEdit


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


@pytest.fixture
def parent(qapp):
    w = QWidget()
    w.show()
    qapp.processEvents()
    return w


@pytest.fixture
def dlg(qapp, parent):
    d = HotkeyDialog(parent, Theme(False), ConfigManager())
    d.show()
    qapp.processEvents()
    return d


def _key(key, mods=Qt.NoModifier, text=""):
    return QKeyEvent(QEvent.KeyPress, key, mods, text)


def test_editor_count(dlg):
    assert len(dlg.editors) == 27


def test_capture_letter_with_mods():
    e = HotkeyEdit("无")
    e.start_capture()
    assert e.text() == "请按键…"
    e.keyPressEvent(_key(Qt.Key_V, Qt.ControlModifier | Qt.AltModifier, "v"))
    assert e.text() == "ctrl+alt+v"


def test_capture_function_key():
    e = HotkeyEdit("无")
    e.start_capture()
    e.keyPressEvent(_key(Qt.Key_F6, Qt.NoModifier))
    assert e.text() == "f6"


def test_capture_escape_restores():
    e = HotkeyEdit("F2")
    e.start_capture()
    e.keyPressEvent(_key(Qt.Key_Escape))
    assert e.text() == "F2"
    assert e._capturing is False


def test_capture_ignores_bare_modifier():
    e = HotkeyEdit("无")
    e.start_capture()
    e.keyPressEvent(_key(Qt.Key_Control))
    assert e.text() == "请按键…"
    assert e._capturing is True


def test_restore_defaults(dlg):
    dlg._restore_defaults()
    assert dlg.editors[("Config", "ShowHotKey")].text() == "F2"
    assert dlg.editors[("Snip", "SnipKey")].text() == "F1"


def test_apply_saves(dlg, qapp):
    called = []
    dlg.on_applied = lambda: called.append(1)
    dlg.editors[("Config", "ShowHotKey")].setText("ctrl+q")
    dlg._apply()
    qapp.processEvents()
    assert dlg.config.get("Config", "ShowHotKey") == "CTRL+Q"
    assert called == [1]


def test_apply_conflict_requires_confirm(dlg, qapp):
    dlg.editors[("Config", "ShowHotKey")].setText("f1")
    dlg.editors[("Snip", "SnipKey")].setText("f1")
    dlg._apply()  # 第一次：进入确认，不保存
    assert dlg._confirming is True
    assert dlg.apply_btn.text() == "确认冲突，后设生效"
    # 确认阶段尚未把冲突解决结果写入（ShowHotKey 仍为内置默认 F2，而非 f1）
    assert dlg.config.get("Config", "ShowHotKey") == "F2"
    dlg._apply()  # 第二次：真正保存
    qapp.processEvents()
    assert dlg.config.get("Snip", "SnipKey") == "F1"
    # 先设的 ShowHotKey 被清空
    assert dlg.config.get("Config", "ShowHotKey") == "无"


def test_clear_button_sets_none(dlg):
    edit = dlg.editors[("Config", "ShowHotKey")]
    edit.setText("ctrl+q")
    clr = [b for b in dlg.findChildren(QPushButton) if b.text() == "清除"]
    assert clr
    # 第一个清除按钮对应第一行
    clr[0].click()
    assert list(dlg.editors.values())[0].text() == "无"
