# -*- coding: utf-8 -*-
"""番茄钟状态机与面板测试。"""
from kivo.core.pomo_store import PomoStore, format_seconds, next_mode
from kivo.ui.theme import Theme
from kivo.ui.panels.pomo_panel import PomoPanel


def test_format():
    assert format_seconds(1507) == "25:07"
    assert format_seconds(-5) == "00:00"


def test_next_mode():
    assert next_mode("focus") == "break"
    assert next_mode("break") == "focus"


def test_countdown():
    s = PomoStore(1, 1)  # 专注 1 分钟
    s.toggle()
    assert s.running
    s.tick()
    assert s.remain == 59


def test_auto_advance():
    s = PomoStore(1, 1)
    s.remain = 1
    s.running = True
    advanced = s.tick()
    assert advanced
    assert s.mode == "break"
    assert s.remain == 60


def test_tick_when_idle():
    s = PomoStore()
    assert s.tick() is False


def test_reset():
    s = PomoStore(25, 5)
    s.toggle()
    s.tick()
    s.reset()
    assert not s.running
    assert s.remain == 25 * 60


def test_advance_callback():
    s = PomoStore()
    fired = []
    s.on_advance = lambda mode: fired.append(mode)
    s.advance()
    assert fired == ["break"]


def test_apply_settings():
    s = PomoStore()
    assert s.apply_settings(30, 10)
    assert s.focus_min == 30
    assert not s.apply_settings(999, 10)
    assert not s.apply_settings(25, 0)


def test_panel_render(qapp):
    p = PomoPanel(Theme(False))
    p.show()
    qapp.processEvents()
    assert p.time_lab.text() == "25:00"
    assert p.main_btn.text() == "开始"


def test_panel_toggle(qapp):
    p = PomoPanel(Theme(False))
    p.show()
    p._toggle()
    assert p.timer.isActive()
    assert p.main_btn.text() == "暂停"
    p._toggle()
    assert not p.timer.isActive()
