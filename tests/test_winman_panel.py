# -*- coding: utf-8 -*-
"""窗口管理模块与面板测试（Linux 下验证降级，Windows 方法用 mock 验证）。"""
from kivo.core.winman import WindowManager, IS_WINDOWS
from kivo.ui.theme import Theme
from kivo.ui.panels.winman_panel import WinmanPanel


def test_platform_flag():
    # 当前测试环境为 Linux
    assert IS_WINDOWS is False


def test_unsupported_returns_none():
    wm = WindowManager()
    assert wm.supported is False
    assert wm.foreground_hwnd() is None
    assert wm.target_hwnd(False) is None


def test_panel_buttons_disabled(qapp):
    p = WinmanPanel(Theme(False), WindowManager())
    p.show()
    qapp.processEvents()
    from PySide6.QtWidgets import QPushButton
    for b in p.findChildren(QPushButton):
        assert not b.isEnabled()


def test_act_no_target(qapp):
    p = WinmanPanel(Theme(False), WindowManager())
    p.show()
    # 无目标时不应抛错（内部 toast）
    p._act(lambda h: None)
    qapp.processEvents()


class _FakeWM:
    def __init__(self):
        self.calls = []
        self.supported = True
        self.last_foreign = 12345

    def foreground_hwnd(self):
        return 999

    def target_hwnd(self, foreground_is_self):
        return self.last_foreign

    def toggle_topmost(self, h):
        self.calls.append(("top", h))


def test_act_with_mock_target(qapp):
    p = WinmanPanel(Theme(False), _FakeWM())
    p.show()
    p._act(lambda h: p.wm.toggle_topmost(h))
    qapp.processEvents()
    assert p.wm.calls == [("top", 12345)]
