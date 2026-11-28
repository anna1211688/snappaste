# -*- coding: utf-8 -*-
"""AppRuntime 接线与动作测试: 注入平台假对象, 不依赖真实 Windows 能力。"""
import pytest

from kivo.core import paths
from kivo.app_context import Services
from kivo.ui.app_runtime import AppRuntime
from kivo.ui.theme import Theme
from kivo.ui.main_window import MainWindow


class _FakeGuard:
    def acquire(self):
        return True


class _FakeHotkeys:
    def __init__(self):
        self.active_count = 0
        self.started = False

    def start(self):
        self.started = True
        self.active_count = 1

    def stop(self):
        self.started = False
        self.active_count = 0


class _FakeTray:
    def __init__(self, *a, **k):
        self.stopped = False

    def start(self):
        return True

    def stop(self):
        self.stopped = True


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    for name in ("CONFIG_PATH", "RECORDS_PATH", "PHRASES_PATH", "AI_CHATS_PATH",
                 "PROJECTS_PATH", "CALC_HISTORY_PATH", "CRASH_LOG_PATH"):
        monkeypatch.setattr(paths, name, str(tmp_path / f"{name}.dat"))


@pytest.fixture
def rt(qapp):
    services = Services()
    # ClipStore 在导入时绑定路径常量, 路径 monkeypatch 不影响它, 显式清空隔离
    services.clip_store.records = []
    services.clip_store.paste_index = 0
    win = MainWindow(Theme(False), services.make_main_services(Theme(False)))
    r = AppRuntime(services, win, instance_guard=_FakeGuard(),
                   hotkey_listener=_FakeHotkeys(),
                   tray_factory=lambda *a, **k: _FakeTray())
    return r, services, win


def test_action_map_covers_all_hotkeys(rt):
    r, services, win = rt
    expected = {(s, k) for s, k, _i in __import__(
        "kivo.core.hotkey_store", fromlist=["HOTKEY_ACTIONS"]).HOTKEY_ACTIONS}
    assert set(r.action_map) == expected


def test_edit_actions_send_combos(rt, monkeypatch):
    r, services, win = rt
    calls = []
    monkeypatch.setattr("kivo.platform.input_sim.foreground_is_self", lambda: False)
    monkeypatch.setattr(
        "kivo.platform.input_sim.send_combo",
        lambda vk: calls.append(vk) or True)
    r.act_select_all(); r.act_cut(); r.act_copy(); r.act_paste()
    assert calls == [0x41, 0x58, 0x43, 0x56]


def test_edit_skipped_when_foreground_self(rt, monkeypatch):
    r, services, win = rt
    calls = []
    monkeypatch.setattr("kivo.platform.input_sim.foreground_is_self", lambda: True)
    monkeypatch.setattr(
        "kivo.platform.input_sim.send_combo",
        lambda vk: calls.append(vk) or True)
    r.act_copy()
    assert calls == []


def test_multi_apply_splits_lines(rt):
    r, services, win = rt
    r._multi_apply("a\nb\nc")
    texts = [x["text"] for x in services.clip_store.records]
    assert texts == ["a", "b", "c"]


def test_paste_next_apply_consumes(rt):
    r, services, win = rt
    store = services.clip_store
    store.add("x"); store.add("y")
    store.paste_index = 0
    r._paste_next_apply(0, True)
    assert [x["text"] for x in store.records] == ["y"]


def test_paste_next_apply_failed_keeps_record(rt):
    r, services, win = rt
    store = services.clip_store
    store.add("x")
    r._paste_next_apply(0, False)
    assert len(store.records) == 1
    assert store.paste_index == 0


def test_close_hides_to_tray(rt, qapp):
    r, services, win = rt
    r.start()
    from PySide6.QtGui import QCloseEvent
    ev = QCloseEvent()
    win.closeEvent(ev)
    assert not ev.isAccepted()
    assert not win.isVisible()
    r.stop()


def test_toggle_hotkeys(rt):
    r, services, win = rt
    assert r.hotkeys.active_count == 0
    r.toggle_hotkeys()
    assert r.hotkeys.active_count == 1
    r.toggle_hotkeys()
    assert r.hotkeys.active_count == 0


def test_select_ai_shows_and_switches(rt):
    r, services, win = rt
    win.hide()
    r.select_ai()
    assert win.isVisible()
    assert win._current == "ai"


def test_snip_delayed_uses_config_seconds(rt, monkeypatch):
    r, services, win = rt
    fired = []
    monkeypatch.setattr(r, "snip_region", lambda: fired.append(1))
    services.config.set("Snip", "DelaySeconds", "0")
    r.snip_delayed()
    assert r._delay_pending is True
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()
    assert fired == [1]
    assert r._delay_pending is False


def test_toggle_clickthrough(rt):
    r, services, win = rt
    from kivo.platform.pin_window import PinWindow
    from PySide6.QtGui import QPixmap
    p1 = PinWindow(win.theme, QPixmap(40, 40))
    p2 = PinWindow(win.theme, QPixmap(40, 40))
    r._pins = [p1, p2]
    r.toggle_clickthrough()
    assert p1.click_through and p2.click_through
    r.toggle_clickthrough()
    assert not p1.click_through and not p2.click_through


def test_restore_pin_reopens_closed(rt):
    r, services, win = rt
    from kivo.platform.pin_window import PinWindow
    from PySide6.QtGui import QPixmap
    pin = PinWindow(win.theme, QPixmap(40, 40))
    pin.on_close = lambda p: r._closed_pins.append(p)
    r._pins = [pin]
    pin.close_pin()
    assert r._closed_pins == [pin]
    r.restore_pin()
    assert r._closed_pins == []
    assert pin.isVisible()


def test_copy_trans_disabled_returns(rt):
    r, services, win = rt
    services.config.set("Translate", "CopyTrans", "0")
    r.copy_trans()  # 开关关闭时直接返回, 不弹卡
