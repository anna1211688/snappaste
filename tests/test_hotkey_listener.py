# -*- coding: utf-8 -*-
"""全局热键监听器测试。"""
import pytest

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.platform.hotkey_listener import HotkeyListener, _default_add, _default_remove


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


def test_default_backend_stub_on_linux():
    h = _default_add("f2", lambda: None)
    assert h == ("stub", "f2")
    _default_remove(h)  # 不报错


def test_bindings_uses_action_map():
    cfg = ConfigManager()
    called = []
    action_map = {("Config", "ShowHotKey"): lambda: called.append(1)}
    lis = HotkeyListener(cfg, action_map)
    b = lis.bindings()
    assert ("f2", action_map[("Config", "ShowHotKey")]) in b


def test_bindings_skips_missing_callback():
    cfg = ConfigManager()  # ShowHotKey=F2 但 action_map 为空
    lis = HotkeyListener(cfg, {})
    assert lis.bindings() == []


def test_start_registers_handles():
    cfg = ConfigManager()
    action_map = {("Config", "ShowHotKey"): lambda: None}
    added, removed = [], []
    lis = HotkeyListener(cfg, action_map,
                         add=lambda hk, cb: added.append(hk) or hk,
                         remove=lambda h: removed.append(h))
    lis.start()
    assert lis.active_count == 1
    assert added == ["f2"]


def test_stop_removes_all():
    cfg = ConfigManager()
    action_map = {("Config", "ShowHotKey"): lambda: None}
    removed = []
    lis = HotkeyListener(cfg, action_map,
                         add=lambda hk, cb: hk,
                         remove=lambda h: removed.append(h))
    lis.start()
    lis.stop()
    assert removed == ["f2"]
    assert lis.active_count == 0


def test_start_clears_previous():
    cfg = ConfigManager()
    action_map = {("Config", "ShowHotKey"): lambda: None}
    n = [0]
    def add(hk, cb):
        n[0] += 1; return f"h{n[0]}"
    removed = []
    lis = HotkeyListener(cfg, action_map, add=add,
                         remove=lambda h: removed.append(h))
    lis.start(); lis.start()
    # 第二次 start 先清掉第一次的句柄
    assert removed == ["h1"]
    assert lis.active_count == 1


def test_binder_exception_skipped():
    cfg = ConfigManager()
    action_map = {("Config", "ShowHotKey"): lambda: None}
    def boom(hk, cb):
        raise RuntimeError("x")
    lis = HotkeyListener(cfg, action_map, add=boom, remove=lambda h: None)
    lis.start()
    assert lis.active_count == 0


def test_none_handle_not_stored():
    cfg = ConfigManager()
    action_map = {("Config", "ShowHotKey"): lambda: None}
    lis = HotkeyListener(cfg, action_map,
                         add=lambda hk, cb: None, remove=lambda h: None)
    lis.start()
    assert lis.active_count == 0
